"""OAuth2 do Google Drive (ADR-022).

Mesmo OAuth client do Gmail, mas outro consentimento, outro redirect URI e
outro escopo: `drive.file`. A plataforma só enxerga o que ela criou e o que a
pessoa escolheu no seletor do Google. O token do e-mail não é reutilizado.

httpx puro, no mesmo estilo de `oauth_gmail.py`.
"""

from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings
from app.services.oauth_common import OAUTH_HTTP_TIMEOUT_SECONDS, OAuthTokenExchangeError

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
SCOPE = "https://www.googleapis.com/auth/drive.file"

# Nome do "provider" dentro do `state` assinado. Um state do Gmail não vale aqui.
STATE_PROVIDER = "google_drive"


def configurado() -> bool:
    settings = get_settings()
    return bool(settings.google_client_id and settings.google_client_secret)


def picker_configurado() -> bool:
    settings = get_settings()
    return bool(settings.google_picker_api_key and settings.google_project_number)


def build_authorize_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_drive_oauth_redirect_uri,
        "response_type": "code",
        "scope": SCOPE,
        # Sem offline + consent o Google não devolve refresh_token ao reconectar.
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def escopo_concedido(tokens: dict) -> bool:
    """O consentimento granular deixa a pessoa desmarcar o acesso ao Drive."""
    concedidos = str(tokens.get("scope") or "").split()
    return SCOPE in concedidos


async def exchange_code(code: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=OAUTH_HTTP_TIMEOUT_SECONDS) as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_drive_oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
    if response.status_code != httpx.codes.OK:
        raise OAuthTokenExchangeError(f"Drive token endpoint retornou {response.status_code}")
    return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=OAUTH_HTTP_TIMEOUT_SECONDS) as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "refresh_token": refresh_token,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "grant_type": "refresh_token",
            },
        )
    if response.status_code != httpx.codes.OK:
        raise OAuthTokenExchangeError(f"Drive refresh endpoint retornou {response.status_code}")
    return response.json()


async def revoke_token(token: str) -> bool:
    """Revoga no Google. Falha de rede não impede a pessoa de desconectar aqui."""
    try:
        async with httpx.AsyncClient(timeout=OAUTH_HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(
                REVOKE_URL,
                data={"token": token},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except httpx.HTTPError:
        return False
    return response.status_code == httpx.codes.OK


def montar_payload(tokens: dict, anterior: dict | None = None) -> dict:
    """Só o necessário para usar e renovar o token. Sem `id_token` e afins."""
    anterior = anterior or {}
    expires_in = tokens.get("expires_in")
    expires_at = None
    if isinstance(expires_in, (int, float)):
        expires_at = (datetime.now(UTC) + timedelta(seconds=int(expires_in))).isoformat()
    return {
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token") or anterior.get("refresh_token"),
        "expires_at": expires_at,
        "scope": tokens.get("scope") or anterior.get("scope") or SCOPE,
    }
