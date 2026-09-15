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
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"
OAUTH_STATE_TOKEN_TYPE = "oauth_state"
OAUTH_STATE_EXPIRE_MINUTES = 10
BCRYPT_ROUNDS = 12
# Tamanho padrão do nonce do AES-GCM (96 bits) — não é segredo, só precisa
# ser único por chave, por isso pode ir concatenado no próprio blob salvo.
AES_GCM_NONCE_BYTES = 12
# bcrypt trunca silenciosamente em 72 bytes; rejeitamos antes para não aceitar
# uma senha longa cuja cauda seria ignorada na verificação.
BCRYPT_MAX_PASSWORD_BYTES = 72
# Hash bcrypt válido (12 rounds) sem usuário correspondente. Usado só para que
# o login gaste o mesmo tempo de CPU quando o e-mail não existe — sem isso,
# `user is None` pula o bcrypt e um atacante mede a diferença de tempo para
# descobrir quais e-mails estão cadastrados.
_DUMMY_PASSWORD_HASH = "$2b$12$pZPE28UKmgzyPfcEOKeMKON21R4fqXAqm3Q8CSkmUbzUuastEs7cS"


class TokenInvalidoError(Exception):
    """Access token (ou state de OAuth2) ausente, malformado, adulterado ou expirado."""


class DecriptografiaError(Exception):
    """Blob AES-GCM corrompido, adulterado ou decriptado com a chave errada.

    O `InvalidTag` da lib `cryptography` já cobre os três casos — não dá para
    diferenciar "chave errada" de "dado adulterado" sem abrir uma janela de
    oráculo, então tratamos os dois igual.
    """


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


def encrypt_secret(plaintext: str) -> bytes:
    """Criptografa CPF, senha ou token OAuth2 do e-SAJ com AES-256-GCM.

    Retorna `nonce || ciphertext_com_tag` prontos para ir numa coluna BYTEA.
    Cada chamada usa um nonce novo — nunca reaproveitar nonce com a mesma
    chave, senão o GCM perde a garantia de confidencialidade.
    """
    settings = get_settings()
    nonce = secrets.token_bytes(AES_GCM_NONCE_BYTES)
    ciphertext = AESGCM(settings.derive_aes_key()).encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ciphertext


def decrypt_secret(blob: bytes) -> str:
    """Reverte `encrypt_secret`.

    Levanta `DecriptografiaError` se o blob foi adulterado ou a chave não é a
    mesma usada para criptografar — nunca decripta "quase certo": o GCM
    verifica a tag de autenticação antes de devolver qualquer byte.
    """
    settings = get_settings()
    nonce, ciphertext = blob[:AES_GCM_NONCE_BYTES], blob[AES_GCM_NONCE_BYTES:]
    try:
        plaintext = AESGCM(settings.derive_aes_key()).decrypt(nonce, ciphertext, None)
    except InvalidTag as exc:
        raise DecriptografiaError("TagInvalida") from exc
    return plaintext.decode("utf-8")


def create_oauth_state_token(user_id: UUID, provider: str) -> str:
    """State assinado do fluxo OAuth2 (Gmail/Outlook) — sem tabela de sessão.

    O callback do provedor chega como navegação pura do browser (sem header
    Authorization), então o `state` é a única forma de recuperar com segurança
    de qual usuário e provedor é aquele `code`. `nonce` garante um valor novo
    a cada `/authorize`, e a expiração curta limita a janela de um state
    interceptado/reaproveitado.
    """
    settings = get_settings()
    agora = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": OAUTH_STATE_TOKEN_TYPE,
        "provider": provider,
        "nonce": secrets.token_urlsafe(16),
        "iat": agora,
        "exp": agora + timedelta(minutes=OAUTH_STATE_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_oauth_state_token(token: str) -> tuple[UUID, str]:
    """Decodifica o `state` e devolve `(user_id, provider)`.

    Quem chama ainda precisa comparar `provider` com o provider da URL do
    callback — o state prova quem gerou o pedido, não substitui essa checagem.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp", "type", "provider"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenInvalidoError(type(exc).__name__) from exc

    if payload.get("type") != OAUTH_STATE_TOKEN_TYPE:
        raise TokenInvalidoError("TipoDeTokenInesperado")

    try:
        user_id = UUID(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise TokenInvalidoError("SubjectInvalido") from exc

    provider = payload.get("provider")
    if not isinstance(provider, str) or not provider:
        raise TokenInvalidoError("ProviderAusente")

    return user_id, provider
