"""Testes de app.services.datajud.consultar_processo — sem rede real, via
`httpx.MockTransport`."""

from dataclasses import dataclass

import httpx
import pytest

from app.services import datajud

NUMERO_CNJ_TJSP = "1002345-67.2025.8.26.0100"


@dataclass
class _FakeSettings:
    datajud_api_key: str = "chave-de-teste"


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _com_chave(monkeypatch, chave: str = "chave-de-teste") -> None:
    monkeypatch.setattr(datajud, "get_settings", lambda: _FakeSettings(datajud_api_key=chave))


class TestConsultarProcesso:
    @pytest.mark.asyncio
    async def test_hit_valido_e_parseado(self, monkeypatch):
        _com_chave(monkeypatch)

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api_publica_tjsp/_search"
            assert request.headers["authorization"] == "APIKey chave-de-teste"
            return httpx.Response(
                200,
                json={
                    "hits": {
                        "hits": [
                            {
                                "_source": {
                                    "numeroProcesso": "10023456720258260100",
                                    "classe": {"codigo": 1116, "nome": "Procedimento Comum Cível"},
                                    "assuntos": [{"codigo": 10570, "nome": "Rescisão contratual"}],
                                    "orgaoJulgador": {"nome": "1ª Vara Cível"},
                                    "dataAjuizamento": "2025-03-10T00:00:00.000Z",
                                    "grau": "G1",
                                    "formato": {"nome": "Eletrônico"},
                                    "movimentos": [
                                        {"codigo": 51, "nome": "Distribuído", "dataHora": "2025-03-10T09:12:00.000Z"}
                                    ],
                                }
                            }
                        ]
                    }
                },
            )

        async with _client(handler) as client:
            resultado = await datajud.consultar_processo(client, NUMERO_CNJ_TJSP)

        assert resultado is not None
        assert resultado.classe.nome == "Procedimento Comum Cível"
        assert resultado.orgao_julgador.nome == "1ª Vara Cível"
        assert resultado.grau == "G1"
        assert len(resultado.movimentos) == 1

    @pytest.mark.asyncio
    async def test_sem_hits_devolve_none(self, monkeypatch):
        _com_chave(monkeypatch)

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"hits": {"hits": []}})

        async with _client(handler) as client:
            resultado = await datajud.consultar_processo(client, NUMERO_CNJ_TJSP)

        assert resultado is None

    @pytest.mark.asyncio
    async def test_erro_http_devolve_none(self, monkeypatch):
        _com_chave(monkeypatch)

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="erro interno")

        async with _client(handler) as client:
            resultado = await datajud.consultar_processo(client, NUMERO_CNJ_TJSP)

        assert resultado is None

    @pytest.mark.asyncio
    async def test_timeout_devolve_none(self, monkeypatch):
        _com_chave(monkeypatch)

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("timeout simulado")

        async with _client(handler) as client:
            resultado = await datajud.consultar_processo(client, NUMERO_CNJ_TJSP)

        assert resultado is None

    @pytest.mark.asyncio
    async def test_json_malformado_devolve_none(self, monkeypatch):
        _com_chave(monkeypatch)

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="isso não é json")

        async with _client(handler) as client:
            resultado = await datajud.consultar_processo(client, NUMERO_CNJ_TJSP)

        assert resultado is None

    @pytest.mark.asyncio
    async def test_sem_api_key_nao_chama_rede(self, monkeypatch):
        _com_chave(monkeypatch, chave="")
        chamou = False

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal chamou
            chamou = True
            return httpx.Response(200, json={})

        async with _client(handler) as client:
            resultado = await datajud.consultar_processo(client, NUMERO_CNJ_TJSP)

        assert resultado is None
        assert chamou is False

    @pytest.mark.asyncio
    async def test_tribunal_nao_mapeado_nao_chama_rede(self, monkeypatch):
        _com_chave(monkeypatch)
        chamou = False

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal chamou
            chamou = True
            return httpx.Response(200, json={})

        async with _client(handler) as client:
            # Segmento 6 (Justiça Eleitoral) ainda não está mapeado.
            resultado = await datajud.consultar_processo(client, "1002345-67.2025.6.26.0100")

        assert resultado is None
        assert chamou is False
