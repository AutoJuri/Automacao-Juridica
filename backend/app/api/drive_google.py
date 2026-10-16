"""Conexão da pessoa com o Google Drive (ADR-022).

Mesmo desenho do e-mail OAuth: `authorize` devolve a URL (o frontend navega
até ela) e `callback` é uma rota pública que chega como navegação pura do
browser, então o `state` assinado diz de quem é o `code`. Falha no callback
nunca expõe o motivo na URL.
"""

import logging

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.rate_limit import (
    LIMITE_DRIVE_PICKER_TOKEN,
    LIMITE_OAUTH_AUTHORIZE,
    LIMITE_OAUTH_CALLBACK,
    limiter,
)
from app.core.security import (
    TokenInvalidoError,
    create_oauth_state_token,
    decode_oauth_state_token,
)
from app.schemas.credentials import AuthorizeUrlSchema
from app.schemas.drive import DriveStatusSchema, PickerTokenSchema
from app.services import drive_arquivos as servico
from app.services import oauth_google_drive
from app.services.drive_google import DriveDesconectadoError
from app.services.oauth_common import OAuthTokenExchangeError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/drive/google", tags=["drive"])

ROTA_DRIVE = "/drive"


def _redirect(resultado: str) -> RedirectResponse:
    return RedirectResponse(f"{get_settings().frontend_url}{ROTA_DRIVE}?google={resultado}")


@router.get("/status", response_model=DriveStatusSchema)
async def status_conexao(current_user: CurrentUser, db: DbSession) -> DriveStatusSchema:
    return await servico.status_conexao(db, current_user.id)


@router.get("/authorize", response_model=AuthorizeUrlSchema)
@limiter.limit(LIMITE_OAUTH_AUTHORIZE)
async def autorizar(request: Request, current_user: CurrentUser) -> AuthorizeUrlSchema:
    if not oauth_google_drive.configurado():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conexão com o Google Drive ainda não configurada no servidor",
        )
    state = create_oauth_state_token(current_user.id, oauth_google_drive.STATE_PROVIDER)
    return AuthorizeUrlSchema(authorize_url=oauth_google_drive.build_authorize_url(state))


@router.get("/callback", include_in_schema=False)
@limiter.limit(LIMITE_OAUTH_CALLBACK)
async def callback(request: Request, db: DbSession) -> RedirectResponse:
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not code or not state:
        return _redirect("erro")

    try:
        user_id, provider = decode_oauth_state_token(state)
    except TokenInvalidoError:
        logger.warning("State do OAuth do Drive inválido ou expirado")
        return _redirect("erro")
    if provider != oauth_google_drive.STATE_PROVIDER:
        logger.warning("State do OAuth do Drive gerado para outro fluxo")
        return _redirect("erro")

    try:
        tokens = await oauth_google_drive.exchange_code(code)
    except OAuthTokenExchangeError:
        logger.warning("Falha ao trocar o code do Drive para user_id=%s", user_id)
        return _redirect("erro")

    if not oauth_google_drive.escopo_concedido(tokens):
        logger.warning("Drive conectado sem o escopo drive.file para user_id=%s", user_id)
        return _redirect("escopo")

    try:
        await servico.salvar_conexao(db, user_id, tokens)
    except DriveDesconectadoError:
        logger.warning("Google não devolveu refresh_token do Drive para user_id=%s", user_id)
        return _redirect("erro")

    logger.info("Google Drive conectado para user_id=%s", user_id)
    return _redirect("conectado")


@router.delete("", response_model=DriveStatusSchema)
async def desconectar(current_user: CurrentUser, db: DbSession) -> DriveStatusSchema:
    resultado = await servico.desconectar(db, current_user.id)
    logger.info("Google Drive desconectado para user_id=%s", current_user.id)
    return resultado


@router.post("/picker-token", response_model=PickerTokenSchema)
@limiter.limit(LIMITE_DRIVE_PICKER_TOKEN)
async def token_do_picker(
    request: Request, response: Response, current_user: CurrentUser, db: DbSession
) -> PickerTokenSchema:
    """Token de acesso curto (`drive.file`) só para abrir o seletor do Google.

    Exceção documentada na ADR-022: o seletor roda no navegador. O refresh
    token continua só no backend.
    """
    settings = get_settings()
    if not oauth_google_drive.picker_configurado():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="O seletor do Google Drive ainda não está configurado no servidor",
        )
    token, expira_em = await servico.token_do_picker(db, current_user.id)
    response.headers["Cache-Control"] = "no-store"
    return PickerTokenSchema(
        access_token=token,
        expires_in=expira_em,
        api_key=settings.google_picker_api_key,
        app_id=settings.google_project_number,
    )
