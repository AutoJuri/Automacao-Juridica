"""Hardening da Etapa 13: headers HTTP, CORS restrito e rate limit das rotas
públicas que ainda estavam sem limite (`/auth/refresh`, `/auth/redefinir-senha`).
"""

from httpx import ASGITransport, AsyncClient
import pytest

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.security_headers import HEADERS_SEGURANCA, HSTS, SecurityHeadersMiddleware
from app.main import CORS_ALLOW_HEADERS, CORS_ALLOW_METHODS, app

HEADERS_OBRIGATORIOS = {k.lower(): v for k, v in HEADERS_SEGURANCA.items()}


def _cliente_asgi() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestSecurityHeaders:
    @pytest.mark.asyncio
    async def test_health_envia_headers_de_seguranca(self):
        async with _cliente_asgi() as client:
            resposta = await client.get("/health")

        assert resposta.status_code == 200
        for nome, valor in HEADERS_OBRIGATORIOS.items():
            assert resposta.headers[nome] == valor

        if get_settings().is_development:
            assert "strict-transport-security" not in resposta.headers
        else:
            assert resposta.headers["strict-transport-security"] == HSTS

    @pytest.mark.asyncio
    async def test_hsts_quando_middleware_habilita(self):
        async def inner(scope, receive, send):
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"text/plain"]],
                }
            )
            await send({"type": "http.response.body", "body": b"ok"})

        empilhado = SecurityHeadersMiddleware(inner, hsts=True)
        async with AsyncClient(
            transport=ASGITransport(app=empilhado),
            base_url="http://test",
        ) as client:
            resposta = await client.get("/")

        assert resposta.headers["strict-transport-security"] == HSTS
        assert resposta.headers["x-frame-options"] == "DENY"


class TestDocsOpenapi:
    @pytest.mark.asyncio
    async def test_docs_so_existem_em_development(self):
        async with _cliente_asgi() as client:
            docs = await client.get("/docs")
            openapi = await client.get("/openapi.json")

        if get_settings().is_development:
            assert docs.status_code == 200
            assert openapi.status_code == 200
        else:
            assert docs.status_code == 404
            assert openapi.status_code == 404


class TestCors:
    @pytest.mark.asyncio
    async def test_preflight_aceita_metodo_e_headers_da_spa(self):
        origem = get_settings().cors_origins_list[0]
        async with _cliente_asgi() as client:
            resposta = await client.options(
                "/auth/login",
                headers={
                    "Origin": origem,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "authorization,content-type",
                },
            )

        assert resposta.status_code == 200
        assert resposta.headers["access-control-allow-origin"] == origem
        permitidos = {
            m.strip().upper()
            for m in resposta.headers["access-control-allow-methods"].split(",")
        }
        assert set(CORS_ALLOW_METHODS) <= permitidos
        assert "PUT" not in permitidos
        allow_headers = resposta.headers["access-control-allow-headers"].lower()
        for header in CORS_ALLOW_HEADERS:
            assert header.lower() in allow_headers

    @pytest.mark.asyncio
    async def test_preflight_rejeita_metodo_nao_usado(self):
        origem = get_settings().cors_origins_list[0]
        async with _cliente_asgi() as client:
            resposta = await client.options(
                "/auth/login",
                headers={
                    "Origin": origem,
                    "Access-Control-Request-Method": "PUT",
                },
            )

        assert resposta.status_code == 400
        # Starlette ainda ecoa ACAO no 400; o método pedido não entra na lista.
        permitidos = resposta.headers.get("access-control-allow-methods", "")
        assert "PUT" not in {m.strip().upper() for m in permitidos.split(",") if m.strip()}

    @pytest.mark.asyncio
    async def test_preflight_rejeita_header_arbitrario(self):
        origem = get_settings().cors_origins_list[0]
        async with _cliente_asgi() as client:
            resposta = await client.options(
                "/auth/login",
                headers={
                    "Origin": origem,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "x-custom-attack",
                },
            )

        assert resposta.status_code == 400


class TestRateLimitAuthPublico:
    @pytest.mark.asyncio
    async def test_refresh_sem_cookie_estoura_limite_por_ip(self, cliente_auth):
        client, _db = cliente_auth
        client.cookies.clear()
        limiter.reset()
        limiter.enabled = True
        try:
            respostas = [await client.post("/auth/refresh") for _ in range(21)]
        finally:
            limiter.enabled = False
            limiter.reset()

        statuses = [r.status_code for r in respostas]
        assert statuses[:20] == [401] * 20
        assert statuses[20] == 429
        corpo = respostas[20].json()
        assert corpo["detail"] == "Muitas tentativas. Tente novamente mais tarde."
        assert "hour" not in str(corpo).lower()

    @pytest.mark.asyncio
    async def test_redefinir_senha_estoura_limite_por_ip(self, cliente_auth):
        client, _db = cliente_auth
        limiter.reset()
        limiter.enabled = True
        corpo = {"token": "invalido", "new_password": "SenhaForte123!"}
        try:
            respostas = [
                await client.post("/auth/redefinir-senha", json=corpo) for _ in range(11)
            ]
        finally:
            limiter.enabled = False
            limiter.reset()

        statuses = [r.status_code for r in respostas]
        assert statuses[:10] == [400] * 10
        assert statuses[10] == 429
