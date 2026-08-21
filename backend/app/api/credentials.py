"""Rotas de credenciais do e-SAJ e conexão OAuth2 de e-mail.

Contrato com o frontend: CPF/senha nunca voltam na resposta — só a versão
mascarada do CPF (`cpf_mascarado`) e um booleano de status. O mesmo vale para
o token OAuth2 do e-mail: o frontend só sabe se está `email_conectado`.
"""

import json
import logging
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.cpf import mask_cpf
from app.core.rate_limit import LIMITE_CREDENCIAL_ESAJ, LIMITE_OAUTH_AUTHORIZE, limiter
from app.core.security import (
    TokenInvalidoError,
    create_oauth_state_token,
    decode_oauth_state_token,
    encrypt_secret,
)
from app.models.tribunal import (
    SESSION_STATUS_ATIVO,
    SESSION_STATUS_EMAIL_DESCONECTADO,
    SESSION_STATUS_REAUTH_PENDENTE,
    TRIBUNAL_ESAJ_TJSP,
    TribunalCredential,
    TribunalSession,
)
from app.schemas.credentials import (
    AuthorizeUrlSchema,
    CredentialStatusSchema,
    EsajCredentialCreateSchema,
)
from app.services import oauth_gmail, oauth_outlook
from app.services.credential_validation import validar_credencial_esaj
from app.services.oauth_common import OAuthTokenExchangeError

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/credentials", tags=["credentials"])

# Rota do frontend que exibe o resultado da conexão de e-mail.
ROTA_CONFIGURACOES = "/configuracoes"

EmailProvider = Literal["gmail", "outlook"]
_PROVIDER_SERVICES = {"gmail": oauth_gmail, "outlook": oauth_outlook}
_PROVIDER_CONFIGURADO = {
    "gmail": lambda: bool(settings.google_client_id and settings.google_client_secret),
    "outlook": lambda: bool(settings.microsoft_client_id and settings.microsoft_client_secret),
}


def _status_schema(
    credencial: TribunalCredential | None, sessao: TribunalSession | None = None
) -> CredentialStatusSchema:
    if credencial is None:
        return CredentialStatusSchema(cadastrado=False)

    return CredentialStatusSchema(
        cadastrado=True,
        tribunal=credencial.tribunal,
        cpf_mascarado=credencial.cpf_mascarado,
        email_provider=credencial.email_provider,
        email_conectado=credencial.email_oauth_token_encrypted is not None,
        last_validated_at=credencial.last_validated_at,
        is_active=credencial.is_active,
        session_status=sessao.status if sessao is not None else None,
        sessao_expirada=sessao.cookie_expirado() if sessao is not None else False,
    )


async def _buscar_credencial_esaj(db: DbSession, user_id: UUID) -> TribunalCredential | None:
    return await db.scalar(
        select(TribunalCredential).where(
            TribunalCredential.user_id == user_id,
            TribunalCredential.tribunal == TRIBUNAL_ESAJ_TJSP,
        )
    )


async def _buscar_sessao_esaj(db: DbSession, user_id: UUID) -> TribunalSession | None:
    return await db.scalar(
        select(TribunalSession).where(
            TribunalSession.user_id == user_id,
            TribunalSession.tribunal == TRIBUNAL_ESAJ_TJSP,
        )
    )


async def _upsert_sessao_status(db: DbSession, user_id: UUID, status_sessao: str) -> TribunalSession:
    """Garante uma linha de sessão com o status visível logo na resposta HTTP
    (antes da BackgroundTask avançar) — evita o frontend ficar sem polling
    porque a resposta ainda traz o status antigo.
    """
    sessao = await _buscar_sessao_esaj(db, user_id)
    if sessao is None:
        sessao = TribunalSession(
            user_id=user_id,
            tribunal=TRIBUNAL_ESAJ_TJSP,
            cookie_encrypted=None,
            status=status_sessao,
        )
        db.add(sessao)
    else:
        sessao.status = status_sessao
        if status_sessao != SESSION_STATUS_ATIVO:
            sessao.anular_cookie()
    await db.commit()
    await db.refresh(sessao)
    return sessao


async def _apagar_sessao_esaj(db: DbSession, user_id: UUID) -> None:
    sessao = await _buscar_sessao_esaj(db, user_id)
    if sessao is not None:
        await db.delete(sessao)


@router.get("/status", response_model=CredentialStatusSchema)
async def status_credenciais(current_user: CurrentUser, db: DbSession) -> CredentialStatusSchema:
    credencial = await _buscar_credencial_esaj(db, current_user.id)
    sessao = await _buscar_sessao_esaj(db, current_user.id) if credencial else None
    return _status_schema(credencial, sessao)


@router.post("/esaj", response_model=CredentialStatusSchema)
@limiter.limit(LIMITE_CREDENCIAL_ESAJ)
async def salvar_credencial_esaj(
    request: Request,
    dados: EsajCredentialCreateSchema,
    current_user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> CredentialStatusSchema:
    """Cria ou substitui a credencial do e-SAJ do usuário autenticado.

    CPF e senha só existem descriptografados durante esta função — nunca são
    logados, nunca voltam na resposta. `cpf_mascarado` é calculado uma vez
    aqui e persistido em texto puro (ADR-005), evitando decriptar de novo só
    para exibir no frontend.

    A validação real da credencial no e-SAJ roda depois, em background
    (ADR-008) — esta resposta não espera pelo resultado do login.
    """
    credencial = await _buscar_credencial_esaj(db, current_user.id)
    cpf_mascarado = mask_cpf(dados.cpf)
    cpf_encrypted = encrypt_secret(dados.cpf)
    senha_encrypted = encrypt_secret(dados.senha)

    if credencial is None:
        credencial = TribunalCredential(
            user_id=current_user.id,
            tribunal=TRIBUNAL_ESAJ_TJSP,
            cpf_encrypted=cpf_encrypted,
            senha_encrypted=senha_encrypted,
            cpf_mascarado=cpf_mascarado,
        )
        db.add(credencial)
    else:
        credencial.cpf_encrypted = cpf_encrypted
        credencial.senha_encrypted = senha_encrypted
        credencial.cpf_mascarado = cpf_mascarado
        credencial.is_active = True
        # CPF/senha mudaram: a última validação não vale mais para a
        # credencial nova.
        credencial.last_validated_at = None

    await db.commit()
    await db.refresh(credencial)

    # Só dispara o Playwright se o e-mail já estiver conectado — o fluxo
    # normal de onboarding cadastra CPF/senha primeiro e conecta o e-mail
    # depois. Sem e-mail, a validação real fica para o callback OAuth ou
    # para o botão "Revalidar". Em qualquer caso a sessão antiga (e o
    # cookie) não vale mais para a credencial recém-salva.
    sessao = None
    if credencial.email_provider is not None:
        sessao = await _upsert_sessao_status(db, current_user.id, SESSION_STATUS_REAUTH_PENDENTE)
        background_tasks.add_task(validar_credencial_esaj, current_user.id)
    else:
        await _apagar_sessao_esaj(db, current_user.id)
        await db.commit()

    logger.info("Credencial e-SAJ salva para user_id=%s", current_user.id)
    return _status_schema(credencial, sessao)


@router.post("/esaj/revalidar", response_model=CredentialStatusSchema)
@limiter.limit(LIMITE_CREDENCIAL_ESAJ)
async def revalidar_credencial_esaj(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> CredentialStatusSchema:
    """Dispara uma nova tentativa de login com a credencial já cadastrada —
    sem exigir reenvio de CPF/senha. Útil depois de conectar o e-mail ou
    quando o e-SAJ estava fora do ar na última tentativa.
    """
    credencial = await _buscar_credencial_esaj(db, current_user.id)
    if credencial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma credencial do e-SAJ cadastrada",
        )

    if credencial.email_provider is None:
        sessao = await _upsert_sessao_status(
            db, current_user.id, SESSION_STATUS_EMAIL_DESCONECTADO
        )
        logger.info(
            "Revalidação e-SAJ recusada sem e-mail (user_id=%s)", current_user.id
        )
        return _status_schema(credencial, sessao)

    sessao = await _upsert_sessao_status(db, current_user.id, SESSION_STATUS_REAUTH_PENDENTE)
    background_tasks.add_task(validar_credencial_esaj, current_user.id)

    logger.info("Revalidação e-SAJ disparada para user_id=%s", current_user.id)
    return _status_schema(credencial, sessao)


@router.delete("/esaj", response_model=CredentialStatusSchema)
async def remover_credencial_esaj(current_user: CurrentUser, db: DbSession) -> CredentialStatusSchema:
    credencial = await _buscar_credencial_esaj(db, current_user.id)
    if credencial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma credencial do e-SAJ cadastrada",
        )

    await _apagar_sessao_esaj(db, current_user.id)
    await db.delete(credencial)
    await db.commit()

    logger.info("Credencial e-SAJ removida para user_id=%s", current_user.id)
    return CredentialStatusSchema(cadastrado=False)


@router.delete("/email", response_model=CredentialStatusSchema)
async def desconectar_email(current_user: CurrentUser, db: DbSession) -> CredentialStatusSchema:
    credencial = await _buscar_credencial_esaj(db, current_user.id)
    if credencial is None or credencial.email_provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum e-mail conectado",
        )

    credencial.email_provider = None
    credencial.email_oauth_token_encrypted = None
    await db.commit()
    await db.refresh(credencial)

    sessao = await _upsert_sessao_status(
        db, current_user.id, SESSION_STATUS_EMAIL_DESCONECTADO
    )

    logger.info("E-mail desconectado para user_id=%s", current_user.id)
    return _status_schema(credencial, sessao)


@router.get("/email/{provider}/authorize", response_model=AuthorizeUrlSchema)
@limiter.limit(LIMITE_OAUTH_AUTHORIZE)
async def autorizar_email(
    provider: EmailProvider,
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
) -> AuthorizeUrlSchema:
    """Devolve a URL de consentimento do provedor — o frontend navega até ela.

    Não é um 302 direto: a chamada é feita via `fetch` com `Authorization:
    Bearer`, e esse header não sobreviveria a um redirect de navegação. O
    frontend recebe a URL e faz `window.location.href = authorize_url`.
    """
    credencial = await _buscar_credencial_esaj(db, current_user.id)
    if credencial is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cadastre as credenciais do e-SAJ antes de conectar o e-mail",
        )

    if not _PROVIDER_CONFIGURADO[provider]():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Conexão com {provider} ainda não configurada no servidor",
        )

    state = create_oauth_state_token(current_user.id, provider)
    authorize_url = _PROVIDER_SERVICES[provider].build_authorize_url(state)
    return AuthorizeUrlSchema(authorize_url=authorize_url)


@router.get("/email/{provider}/callback", include_in_schema=False)
async def callback_email(
    provider: EmailProvider,
    request: Request,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> RedirectResponse:
    """Recebe o redirect do provedor. Rota pública — chega como navegação
    pura do browser, nunca com header `Authorization`.

    Qualquer falha (state ausente/inválido/expirado, provider trocado,
    credencial e-SAJ removida nesse meio tempo, erro na troca do código)
    redireciona para a tela de configurações com `?email=erro`, sem nunca
    expor o motivo exato na URL.
    """
    erro_redirect = RedirectResponse(f"{settings.frontend_url}{ROTA_CONFIGURACOES}?email=erro")

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not code or not state:
        return erro_redirect

    try:
        user_id, state_provider = decode_oauth_state_token(state)
    except TokenInvalidoError:
        logger.warning("State de OAuth2 (%s) inválido ou expirado", provider)
        return erro_redirect

    if state_provider != provider:
        logger.warning("State de OAuth2 gerado para outro provider (esperado=%s)", provider)
        return erro_redirect

    credencial = await _buscar_credencial_esaj(db, user_id)
    if credencial is None:
        logger.warning("Callback OAuth2 (%s) sem credencial e-SAJ para user_id=%s", provider, user_id)
        return erro_redirect

    try:
        tokens = await _PROVIDER_SERVICES[provider].exchange_code(code)
    except OAuthTokenExchangeError:
        logger.warning("Falha ao trocar code por token (%s) para user_id=%s", provider, user_id)
        return erro_redirect

    # Só o necessário para renovar o access token depois (Etapa 6) — nunca
    # persistimos id_token nem outros campos que carreguem dados do e-mail.
    payload = json.dumps(
        {
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens.get("expires_in"),
            "token_type": tokens.get("token_type"),
        }
    )
    credencial.email_provider = provider
    credencial.email_oauth_token_encrypted = encrypt_secret(payload)
    await db.commit()

    # Com e-mail recém-conectado, dispara a validação do e-SAJ automaticamente
    # — o advogado já cadastrou CPF/senha antes e não precisa clicar em
    # "Revalidar" só por ter completado o OAuth.
    await _upsert_sessao_status(db, user_id, SESSION_STATUS_REAUTH_PENDENTE)
    background_tasks.add_task(validar_credencial_esaj, user_id)

    logger.info("E-mail %s conectado para user_id=%s", provider, user_id)
    return RedirectResponse(f"{settings.frontend_url}{ROTA_CONFIGURACOES}?email=conectado")
