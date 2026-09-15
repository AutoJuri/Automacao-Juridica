"""Headers HTTP de segurança aplicados a todas as respostas da API.

A SPA React já tem o seu próprio CSP via o host do frontend. Aqui o alvo é a
API: não deve ser embutida em iframe, não deve ser interpretada como outro
MIME, e em produção anuncia HSTS (o Railway termina TLS no proxy; o browser
vê HTTPS).
"""

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

HEADERS_SEGURANCA: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}

HSTS = "max-age=31536000; includeSubDomains"


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, *, hsts: bool = False) -> None:
        self.app = app
        self.hsts = hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(raw=message["headers"])
                for nome, valor in HEADERS_SEGURANCA.items():
                    headers[nome] = valor
                if self.hsts:
                    headers["Strict-Transport-Security"] = HSTS
            await send(message)

        await self.app(scope, receive, send_wrapper)
