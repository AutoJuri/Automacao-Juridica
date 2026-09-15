"""OAuth2 com o Microsoft Graph — geração da URL de consentimento e troca de
código por tokens de acesso/refresh.

Implementado com `httpx` puro (sem `msal`), pelo mesmo motivo do
`oauth_gmail.py`: o Authorization Code flow da Microsoft identity platform é
duas chamadas REST documentadas, sem necessidade de SDK.

Escopo mínimo: `Mail.Read` (somente leitura) + `offline_access` (necessário
para receber `refresh_token`) — usado só para localizar, na Etapa 6, o e-mail
de verificação enviado pelo e-SAJ. Nenhuma chamada de escrita, envio ou
exclusão é feita com este token.
"""

from urllib.parse import urlencode

import httpx

from app.core.config import get_settings
from app.services.oauth_common import OAUTH_HTTP_TIMEOUT_SECONDS, OAuthTokenExchangeError

AUTHORIZE_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
SCOPE = "offline_access Mail.Read"


def build_authorize_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.microsoft_client_id,
        "redirect_uri": settings.microsoft_oauth_redirect_uri,
        "response_type": "code",
        "scope": SCOPE,
        "state": state,
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> dict:
    """Troca o `code` do redirect por `{access_token, refresh_token, ...}`."""
    settings = get_settings()
    async with httpx.AsyncClient(timeout=OAUTH_HTTP_TIMEOUT_SECONDS) as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.microsoft_client_id,
                "client_secret": settings.microsoft_client_secret,
                "redirect_uri": settings.microsoft_oauth_redirect_uri,
                "grant_type": "authorization_code",
                "scope": SCOPE,
            },
        )

    if response.status_code != httpx.codes.OK:
        raise OAuthTokenExchangeError(f"Microsoft token endpoint retornou {response.status_code}")

    return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Troca um `refresh_token` por um novo `access_token`.

    A Microsoft costuma devolver um novo `refresh_token` a cada troca — quem
    chamar deve sempre persistir o `refresh_token` retornado aqui.
    """
    settings = get_settings()
    async with httpx.AsyncClient(timeout=OAUTH_HTTP_TIMEOUT_SECONDS) as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "refresh_token": refresh_token,
                "client_id": settings.microsoft_client_id,
                "client_secret": settings.microsoft_client_secret,
                "grant_type": "refresh_token",
                "scope": SCOPE,
            },
        )

    if response.status_code != httpx.codes.OK:
        raise OAuthTokenExchangeError(f"Microsoft refresh endpoint retornou {response.status_code}")

    return response.json()
