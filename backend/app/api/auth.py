"""Rotas de autenticação da plataforma.

Contrato com o frontend: access token JWT devolvido no corpo (mantido só em
memória pelo cliente) e refresh token opaco em cookie HttpOnly, revogável no
banco.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.rate_limit import (
    LIMITE_CADASTRO,
    LIMITE_LOGIN,
    LIMITE_RECUPERAR_SENHA,
    limiter,
)
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password_or_dummy,
)
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordSchema,
    MessageSchema,
    ResetPasswordSchema,
    TokenResponseSchema,
    UserCreateSchema,
    UserLoginSchema,
    UserPublicSchema,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
# Restringe o envio do cookie às rotas que realmente precisam dele.
REFRESH_COOKIE_PATH = "/auth"
# Rota do frontend que recebe o token de redefinição.
ROTA_REDEFINIR_SENHA = "/redefinir-senha"

# Mensagem única para credenciais erradas e e-mail inexistente — não permite
# descobrir quais e-mails estão cadastrados.
_CREDENCIAIS_INVALIDAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="E-mail ou senha inválidos",
    headers={"WWW-Authenticate": "Bearer"},
)


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        # Em development o front roda em http://localhost; fora disso o
        # cookie só trafega sob HTTPS.
        secure=not settings.is_development,
        samesite="strict",
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=not settings.is_development,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
    )


async def _emitir_sessao(db: DbSession, user: User, response: Response) -> TokenResponseSchema:
    """Cria o par access token + refresh token e seta o cookie."""
    refresh_token, refresh_hash = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.jwt_refresh_token_expire_days),
        )
    )
    await db.commit()

    _set_refresh_cookie(response, refresh_token)
    return TokenResponseSchema(
        access_token=create_access_token(user.id),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserPublicSchema.model_validate(user),
    )


@router.post("/cadastro", response_model=TokenResponseSchema, status_code=status.HTTP_201_CREATED)
@limiter.limit(LIMITE_CADASTRO)
async def cadastrar(
    request: Request,
    response: Response,
    dados: UserCreateSchema,
    db: DbSession,
) -> TokenResponseSchema:
    email = dados.email.lower()
    if await db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado",
        )

    user = User(name=dados.name.strip(), email=email, password_hash=hash_password(dados.password))
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        # Corrida entre a checagem acima e o insert.
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado",
        ) from None

    return await _emitir_sessao(db, user, response)


@router.post("/login", response_model=TokenResponseSchema)
@limiter.limit(LIMITE_LOGIN)
async def login(
    request: Request,
    response: Response,
    dados: UserLoginSchema,
    db: DbSession,
) -> TokenResponseSchema:
    user = await db.scalar(select(User).where(User.email == dados.email.lower()))
    # verify_password_or_dummy sempre roda o bcrypt, mesmo sem usuário — evita
    # que o tempo de resposta denuncie quais e-mails estão cadastrados.
    if not verify_password_or_dummy(dados.password, user.password_hash if user else None):
        raise _CREDENCIAIS_INVALIDAS

    return await _emitir_sessao(db, user, response)


@router.post("/refresh", response_model=TokenResponseSchema)
async def refresh(request: Request, response: Response, db: DbSession) -> TokenResponseSchema:
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise _CREDENCIAIS_INVALIDAS

    token_hash = hash_token(token)
    agora = datetime.now(UTC)

    # UPDATE atômico: a linha só casa o WHERE (revoked_at IS NULL) uma única
    # vez. Duas chamadas concorrentes de /auth/refresh com o mesmo cookie —
    # aba duplicada, retry de rede — não conseguem mais as duas "vencer" a
    # rotação e emitir duas sessões a partir do mesmo token.
    resultado = await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > agora,
        )
        .values(revoked_at=agora)
        .returning(RefreshToken.user_id)
    )
    linha = resultado.first()

    if linha is None:
        await _revogar_tudo_se_reuso_de_refresh(db, token_hash, agora)
        raise _CREDENCIAIS_INVALIDAS

    user = await db.get(User, linha.user_id)
    if user is None:
        raise _CREDENCIAIS_INVALIDAS

    return await _emitir_sessao(db, user, response)


async def _revogar_tudo_se_reuso_de_refresh(
    db: DbSession, token_hash: str, agora: datetime
) -> None:
    """Um refresh token só deveria ser apresentado uma vez.

    Se o UPDATE atômico do refresh não achou o token com `revoked_at IS
    NULL`, mas o registro existe e já está revogado, alguém apresentou um
    token que já foi usado — sinal de cookie roubado e reaproveitado (ex.:
    vítima e atacante usando o mesmo refresh). Por precaução, derruba todas
    as sessões ativas do usuário.

    Se o registro simplesmente não existe ou só expirou sem nunca ter sido
    revogado, não há evidência de reuso — não faz nada.
    """
    registro = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if registro is None or registro.revoked_at is None:
        return

    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == registro.user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=agora)
    )
    await db.commit()


@router.post("/logout", response_model=MessageSchema)
async def logout(request: Request, response: Response, db: DbSession) -> MessageSchema:
    """Revoga o refresh token do cookie.

    Não exige access token: o cliente pode estar com o access já expirado e
    ainda assim precisa encerrar a sessão. A posse do cookie é a prova
    suficiente, e revogar um token já inválido é inócuo.
    """
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if token:
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == hash_token(token),
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        await db.commit()

    _clear_refresh_cookie(response)
    return MessageSchema(message="Sessão encerrada")


@router.get("/me", response_model=UserPublicSchema)
async def me(current_user: CurrentUser) -> UserPublicSchema:
    return UserPublicSchema.model_validate(current_user)


@router.post("/recuperar-senha", response_model=MessageSchema)
@limiter.limit(LIMITE_RECUPERAR_SENHA)
async def recuperar_senha(
    request: Request,
    dados: ForgotPasswordSchema,
    db: DbSession,
) -> MessageSchema:
    """Gera um token de redefinição.

    Ainda não há provedor de e-mail configurado: o link é escrito no log do
    servidor. Ao integrar o envio real, remover o log do link.
    """
    resposta = MessageSchema(
        message="Se o e-mail estiver cadastrado, enviaremos as instruções de redefinição."
    )

    user = await db.scalar(select(User).where(User.email == dados.email.lower()))
    if user is None:
        return resposta

    # Invalida pedidos anteriores: só o link mais recente funciona.
    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=datetime.now(UTC))
    )

    token, token_hash = generate_refresh_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC)
            + timedelta(minutes=settings.password_reset_token_expire_minutes),
        )
    )
    await db.commit()

    # O link (com o token) só vai para o log em development. Fora disso, um
    # leitor do log (agregador, suporte, vazamento) teria acesso a um token
    # de reset válido e poderia sequestrar a conta — sem provedor de e-mail,
    # não há como entregar o link de outra forma ainda (ADR-003).
    if settings.is_development:
        link = f"{settings.frontend_url}{ROTA_REDEFINIR_SENHA}?token={token}"
        logger.warning(
            "Link de redefinição de senha gerado para user_id=%s: %s",
            user.id,
            link,
        )
    else:
        logger.info("Token de redefinição de senha gerado para user_id=%s", user.id)
    return resposta


@router.post("/redefinir-senha", response_model=MessageSchema)
async def redefinir_senha(
    dados: ResetPasswordSchema,
    db: DbSession,
) -> MessageSchema:
    agora = datetime.now(UTC)

    # UPDATE atômico: evita que duas requisições concorrentes com o mesmo
    # token (retry de rede, duplo clique) consigam ambas passar pela checagem
    # de "used_at IS NULL" e gastar o mesmo token de reset duas vezes.
    resultado = await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.token_hash == hash_token(dados.token),
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > agora,
        )
        .values(used_at=agora)
        .returning(PasswordResetToken.user_id)
    )
    linha = resultado.first()
    if linha is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado",
        )

    user = await db.get(User, linha.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado",
        )

    user.password_hash = hash_password(dados.new_password)

    # Troca de senha derruba todas as sessões ativas em qualquer dispositivo.
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=agora)
    )
    await db.commit()

    return MessageSchema(message="Senha redefinida com sucesso")
