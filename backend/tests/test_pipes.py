"""Testes dos pipes de coleta (`coletar`) com `httpx.MockTransport` — sem
rede real. Payloads baseados nos exemplos sanitizados de
`docs/modulos/esaj-apis.md`."""

import httpx
import pytest

from app.services.pipes import pipe_audiencias, pipe_intimacoes, pipe_processos


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://esaj.tjsp.jus.br")


class TestPipeIntimacoes:
    @pytest.mark.asyncio
    async def test_coleta_e_valida_itens_do_payload(self):
        payload = [
            {
                "id": "cdProcesso=1A0000XXXX0000,nuSeqIntimacao=10,oab=123456SP",
                "titulo": "Mero expediente",
                "descricao": "Texto da intimação...",
                "cdProcesso": "1A0000XXXX0000",
                "instancia": "PG",
                "dataMovimentacao": "2026-06-30T11:14:06",
                "ciencia": False,
            }
        ]

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/tarefas-adv/api/intimacoes"
            return httpx.Response(200, json=payload)

        async with _client(handler) as client:
            resultado = await pipe_intimacoes.coletar(client)

        assert len(resultado) == 1
        assert resultado[0].cd_processo == "1A0000XXXX0000"
        assert resultado[0].ciencia is False

    @pytest.mark.asyncio
    async def test_item_sem_cd_processo_e_omitido_sem_logar_oab(self, caplog):
        payload = [
            {
                "id": "cdProcesso=1A0000XXXX0000,nuSeqIntimacao=10,oab=123456SP",
                "cdProcesso": "1A0000XXXX0000",
            },
            {
                "id": "cdProcesso=1B0000YYYY0000,nuSeqIntimacao=11,oab=999999SP",
                "titulo": "sem cdProcesso",
            },
        ]

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=payload)

        with caplog.at_level("INFO"):
            async with _client(handler) as client:
                resultado = await pipe_intimacoes.coletar(client)

        assert len(resultado) == 1
        assert resultado[0].cd_processo == "1A0000XXXX0000"
        texto = caplog.text
        assert "123456SP" not in texto
        assert "999999SP" not in texto
        assert "pipe=intimacoes" in texto


class TestPipeAudiencias:
    @pytest.mark.asyncio
    async def test_coleta_e_valida_itens_do_payload(self):
        payload = [
            {
                "dataMovimentacao": "2026-05-25T17:30:29",
                "dataAudiencia": "2026-07-21T16:00:00",
                "situacao": "Pendente",
                "titulo": "Instrução, Debates e Julgamento",
                "local": "Sala de Audiências",
                "cdProcesso": "1A0000XXXX0000",
            }
        ]

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/tarefas-adv/api/audiencias"
            return httpx.Response(200, json=payload)

        async with _client(handler) as client:
            resultado = await pipe_audiencias.coletar(client)

        assert len(resultado) == 1
        assert resultado[0].titulo == "Instrução, Debates e Julgamento"
        assert resultado[0].local == "Sala de Audiências"


class TestPipeProcessos:
    @pytest.mark.asyncio
    async def test_lista_vazia_de_cds_nao_faz_requisicao(self):
        chamadas = []

        def handler(request: httpx.Request) -> httpx.Response:
            chamadas.append(request)
            return httpx.Response(200, json=[])

        async with _client(handler) as client:
            resultado = await pipe_processos.coletar(client, [])

        assert resultado == []
        assert chamadas == []

    @pytest.mark.asyncio
    async def test_codigo_pedido_que_nao_volta_e_apenas_omitido(self):
        payload = [{"cdProcesso": "AAA", "nuProcesso": "00000000000000000000"}]

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=payload)

        async with _client(handler) as client:
            resultado = await pipe_processos.coletar(client, ["AAA", "BBB"])

        assert len(resultado) == 1
        assert resultado[0].cd_processo == "AAA"

    @pytest.mark.asyncio
    async def test_lista_grande_e_dividida_em_lotes(self):
        cds_processo = [f"CD{i}" for i in range(120)]
        lotes_recebidos: list[list[str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            cds_do_lote = request.url.params.get_list("cdsProcesso")
            lotes_recebidos.append(cds_do_lote)
            return httpx.Response(200, json=[{"cdProcesso": cd} for cd in cds_do_lote])

        async with _client(handler) as client:
            resultado = await pipe_processos.coletar(client, cds_processo)

        assert len(lotes_recebidos) == 3
        assert all(len(lote) <= pipe_processos.CDS_PROCESSO_CHUNK_SIZE for lote in lotes_recebidos)
        assert len(resultado) == 120
