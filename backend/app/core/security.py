"""Primitivas de segurança: hash de senha, JWT de acesso e refresh tokens.

Nada aqui loga senha, token bruto ou hash — apenas o tipo do erro sobe para
quem chamou.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
import jwt

from app.core.config import get_settings

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"
BCRYPT_ROUNDS = 12
# bcrypt trunca silenciosamente em 72 bytes; rejeitamos antes para não aceitar
# uma senha longa cuja cauda seria ignorada na verificação.
BCRYPT_MAX_PASSWORD_BYTES = 72
# Hash bcrypt válido (12 rounds) sem usuário correspondente. Usado só para que
# o login gaste o mesmo tempo de CPU quando o e-mail não existe — sem isso,
# `user is None` pula o bcrypt e um atacante mede a diferença de tempo para
# descobrir quais e-mails estão cadastrados.
_DUMMY_PASSWORD_HASH = "$2b$12$pZPE28UKmgzyPfcEOKeMKON21R4fqXAqm3Q8CSkmUbzUuastEs7cS"


class TokenInvalidoError(Exception):
    """Access token ausente, malformado, adulterado ou expirado."""


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(f"Senha excede {BCRYPT_MAX_PASSWORD_BYTES} bytes")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Hash malformado no banco — trata como credencial inválida, nunca
        # deixa vazar detalhe do hash na exceção.
        return False


def verify_password_or_dummy(password: str, password_hash: str | None) -> bool:
    """Verifica a senha mesmo quando não há usuário (hash `None`).

    Roda `bcrypt.checkpw` contra um hash dummy fixo nesse caso, para que o
    tempo de resposta do login não dependa de o e-mail existir ou não — o
    resultado é sempre `False` quando `password_hash` é `None`, mas só depois
    de pagar o mesmo custo de CPU que uma verificação real.
    """
    resultado = verify_password(password, password_hash or _DUMMY_PASSWORD_HASH)
    return password_hash is not None and resultado


def create_access_token(user_id: UUID, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    agora = datetime.now(UTC)
    expira_em = expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "type": ACCESS_TOKEN_TYPE,
        "iat": agora,
        "exp": agora + expira_em,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> UUID:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenInvalidoError(type(exc).__name__) from exc

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise TokenInvalidoError("TipoDeTokenInesperado")

    try:
        return UUID(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise TokenInvalidoError("SubjectInvalido") from exc


def hash_token(token: str) -> str:
    """SHA-256 hex de um token opaco.

    Refresh e reset tokens têm entropia alta o suficiente para dispensar
    bcrypt aqui, e o hash precisa ser determinístico para permitir lookup
    direto por índice único.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_refresh_token() -> tuple[str, str]:
    """Gera (token bruto para o cookie, hash para persistir no banco)."""
    token = secrets.token_urlsafe(48)
    return token, hash_token(token)
