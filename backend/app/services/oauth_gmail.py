"""OAuth2 com a Gmail API — geração da URL de consentimento e troca de código
por tokens de acesso/refresh.

Implementado com `httpx` puro (sem `google-auth-oauthlib`): o Authorization
Code flow do Google é só duas chamadas REST documentadas, e evitar o SDK
mantém a mesma abordagem "httpx direto" já usada no restante do projeto para
integrações externas.

Escopo mínimo: `gmail.readonly` (somente leitura) — usado só para localizar,
na Etapa 6, o e-mail de verificação enviado pelo e-SAJ. Nenhuma chamada de
escrita, envio ou exclusão é feita com este token.
"""

from urllib.parse import urlencode

import httpx

from app.core.config import get_settings
from app.services.oauth_common import OAUTH_HTTP_TIMEOUT_SECONDS, OAuthTokenExchangeError

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


def build_authorize_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_oauth_redirect_uri,
        "response_type": "code",
        "scope": SCOPE,
        # access_type=offline + prompt=consent: sem isso o Google só devolve
        # refresh_token na primeira autorização de todas — reconexões depois
        # de revogar o acesso ficariam sem refresh_token nenhum.
        "access_type": "offline",
        "prompt": "consent",
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
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
        )

    if response.status_code != httpx.codes.OK:
        raise OAuthTokenExchangeError(f"Gmail token endpoint retornou {response.status_code}")

    return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Troca um `refresh_token` por um novo `access_token`.

    O Google normalmente não devolve um novo `refresh_token` nesta chamada —
    quem chamar deve preservar o `refresh_token` original se a resposta não
    trouxer um novo.
    """
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
        raise OAuthTokenExchangeError(f"Gmail refresh endpoint retornou {response.status_code}")

    return response.json()
