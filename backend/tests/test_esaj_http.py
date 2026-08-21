"""Testes de app.services.esaj_http.buscar_json — sem rede real, via
`httpx.MockTransport`."""

import httpx
import pytest

from app.services.esaj_http import (
    EsajPortalIndisponivelError,
    EsajRateLimitError,
    EsajSessaoInvalidaError,
    buscar_json,
    validar_itens,
)


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://esaj.tjsp.jus.br")


class TestBuscarJson:
    @pytest.mark.asyncio
    async def test_resposta_json_200_e_devolvida_como_lista(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[{"id": "1"}, {"id": "2"}])

        async with _client(handler) as client:
            resultado = await buscar_json(client, "/tarefas-adv/api/intimacoes", referer="ref")

        assert resultado == [{"id": "1"}, {"id": "2"}]

    @pytest.mark.asyncio
    async def test_html_de_login_levanta_sessao_invalida(self):
        html_login = (
            "<!doctype html><html><body>"
            "<form id='usernameForm'></form><form id='passwordForm'></form>"
            "</body></html>"
        )

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, headers={"content-type": "text/html"}, text=html_login)

        async with _client(handler) as client:
            with pytest.raises(EsajSessaoInvalidaError):
                await buscar_json(client, "/tarefas-adv/api/intimacoes", referer="ref")

    @pytest.mark.asyncio
    async def test_redirect_final_para_sajcas_levanta_sessao_invalida(self):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/tarefas-adv/api/intimacoes":
                return httpx.Response(
                    302, headers={"location": "https://esaj.tjsp.jus.br/sajcas/login"}
                )
            return httpx.Response(200, headers={"content-type": "text/html"}, text="<!doctype html>login sajcas")

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://esaj.tjsp.jus.br",
            follow_redirects=True,
        ) as client:
            with pytest.raises(EsajSessaoInvalidaError):
                await buscar_json(client, "/tarefas-adv/api/intimacoes", referer="ref")

    @pytest.mark.asyncio
    async def test_status_429_levanta_rate_limit_e_nao_portal_indisponivel(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, text="rate limited")

        async with _client(handler) as client:
            with pytest.raises(EsajRateLimitError):
                await buscar_json(client, "/tarefas-adv/api/intimacoes", referer="ref")

    @pytest.mark.asyncio
    async def test_status_diferente_de_200_levanta_portal_indisponivel(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="erro interno")

        async with _client(handler) as client:
            with pytest.raises(EsajPortalIndisponivelError):
                await buscar_json(client, "/tarefas-adv/api/intimacoes", referer="ref")

    @pytest.mark.asyncio
    async def test_payload_que_nao_e_lista_levanta_portal_indisponivel(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"não": "é uma lista"})

        async with _client(handler) as client:
            with pytest.raises(EsajPortalIndisponivelError):
                await buscar_json(client, "/tarefas-adv/api/intimacoes", referer="ref")

    @pytest.mark.asyncio
    async def test_timeout_levanta_portal_indisponivel(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("timeout simulado")

        async with _client(handler) as client:
            with pytest.raises(EsajPortalIndisponivelError):
                await buscar_json(client, "/tarefas-adv/api/intimacoes", referer="ref")


class TestValidarItens:
    def test_omite_item_invalido_sem_logar_payload(self, caplog):
        from app.schemas.esaj_raw import IntimacaoRaw

        payload = [
            {"id": "cdProcesso=AAA,oab=123456SP", "cdProcesso": "AAA"},
            {"id": "cdProcesso=BBB,oab=999999SP"},
        ]

        with caplog.at_level("INFO"):
            resultado = validar_itens(IntimacaoRaw, payload, contexto="intimacoes")

        assert len(resultado) == 1
        assert resultado[0].cd_processo == "AAA"
        texto = caplog.text
        assert "123456SP" not in texto
        assert "999999SP" not in texto
        assert "cdProcesso=BBB" not in texto
        assert "pipe=intimacoes" in texto
        assert "campos=" in texto
