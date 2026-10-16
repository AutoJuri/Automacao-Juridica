"""Testes de app.services.datajud.consultar_processo — sem rede real, via
`httpx.MockTransport`."""

from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
import pytest

from app.schemas.datajud_raw import DatajudProcessoRaw
from app.services import datajud
from app.services.consulta_publica import montar_consulta_publica
from app.services.datajud import ExibicaoDatajud

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


def _hit_minimo() -> dict:
    return {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "numeroProcesso": "10023456720258260100",
                        "classe": {"nome": "Procedimento Comum Cível"},
                        "orgaoJulgador": {"nome": "1ª Vara Cível"},
                        "grau": "G1",
                    }
                }
            ]
        }
    }


class TestConsultarExibicao:
    @pytest.mark.asyncio
    async def test_encontrado_devolve_a_ficha(self, monkeypatch):
        _com_chave(monkeypatch)

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=_hit_minimo())

        async with _client(handler) as client:
            resultado = await datajud.consultar_exibicao(client, NUMERO_CNJ_TJSP)

        assert resultado.situacao == "encontrado"
        assert resultado.tribunal == "tjsp"
        assert resultado.processo is not None
        assert resultado.processo.classe is not None
        assert resultado.processo.classe.nome == "Procedimento Comum Cível"

    @pytest.mark.asyncio
    async def test_sem_hit_e_ausente_e_erro_e_indisponivel(self, monkeypatch):
        _com_chave(monkeypatch)

        def sem_hit(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"hits": {"hits": []}})

        async with _client(sem_hit) as client:
            ausente = await datajud.consultar_exibicao(client, NUMERO_CNJ_TJSP)
        assert ausente.situacao == "ausente"
        assert ausente.processo is None

        def erro(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="fora")

        async with _client(erro) as client:
            indisponivel = await datajud.consultar_exibicao(client, NUMERO_CNJ_TJSP)
        assert indisponivel.situacao == "indisponivel"

    @pytest.mark.asyncio
    async def test_numero_invalido_e_tribunal_fora_do_mapa(self, monkeypatch):
        _com_chave(monkeypatch)

        async with _client(lambda request: httpx.Response(200, json={})) as client:
            invalido = await datajud.consultar_exibicao(client, "não é cnj")
            eleitoral = await datajud.consultar_exibicao(client, "1002345-67.2025.6.26.0100")

        assert invalido.situacao == "numero_invalido"
        assert eleitoral.situacao == "tribunal_nao_suportado"


class TestFichaPublica:
    def test_ajuizamento_compacto_nao_vira_timestamp(self):
        processo = DatajudProcessoRaw.model_validate(
            {
                "dataAjuizamento": "20250827120723",
                "dataHoraUltimaAtualizacao": "2026-04-15T09:36:48.609000Z",
                "nivelSigilo": "0",
                "formato": {"nome": "Eletrônico"},
                "sistema": {"nome": "SAJ"},
                "orgaoJulgador": {"nome": "05 CIVEL DE BAURU"},
                "movimentos": [
                    {
                        "nome": "Distribuição",
                        "dataHora": "2025-08-27T12:17:56.000Z",
                        "orgaoJulgador": {"nome": "05 CIVEL DE BAURU"},
                        "complementosTabelados": [
                            {"nome": "sorteio", "descricao": "tipo_de_distribuicao_redistribuicao"}
                        ],
                    }
                ],
            }
        )
        assert processo.data_ajuizamento == datetime(2025, 8, 27, 12, 7, 23, tzinfo=UTC)
        ficha = montar_consulta_publica(
            "1020590-88.2025.8.26.0071",
            ExibicaoDatajud("encontrado", "tjsp", processo),
        )
        assert ficha.formato == "Eletrônico"
        assert ficha.sistema == "SAJ"
        assert ficha.sigilo == "Público"
        assert ficha.atualizado_em is not None
        assert len(ficha.movimentos) == 1
        assert ficha.movimentos[0].complementos == ["sorteio"]
        assert ficha.movimentos[0].orgao_julgador == "05 CIVEL DE BAURU"
        assert ficha.movimentos_total == 1

    def test_corta_movimentos_depois_de_cem(self):
        processo = DatajudProcessoRaw.model_validate(
            {
                "movimentos": [
                    {"nome": f"Andamento {indice}", "dataHora": f"2025-01-{(indice % 28) + 1:02d}T12:00:00.000Z"}
                    for indice in range(130)
                ]
            }
        )
        ficha = montar_consulta_publica(
            "1020590-88.2025.8.26.0071",
            ExibicaoDatajud("encontrado", "tjsp", processo),
        )
        assert ficha.movimentos_total == 130
        assert len(ficha.movimentos) == 100
