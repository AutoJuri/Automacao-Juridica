"""Testes das funções de diff (sem banco) — app.etl.diff."""

from uuid import uuid4

import pytest

from app.etl.diff import gerar_notificacoes, selecionar_novas_audiencias, selecionar_novas_intimacoes
from app.models.audiencia import Audiencia
from app.models.intimacao import Intimacao
from app.schemas.esaj_raw import AudienciaRaw, IntimacaoRaw


def _intimacao(id_: str) -> IntimacaoRaw:
    return IntimacaoRaw.model_validate({"id": id_, "cdProcesso": "1A0"})


def _audiencia(titulo: str) -> AudienciaRaw:
    return AudienciaRaw.model_validate({"cdProcesso": "1A0", "titulo": titulo})


class TestSelecionarNovasIntimacoes:
    def test_mantem_apenas_as_que_nao_existem_ainda(self):
        brutos = [_intimacao("a"), _intimacao("b"), _intimacao("c")]

        novas = selecionar_novas_intimacoes({"a", "c"}, brutos)

        assert [raw.id for raw in novas] == ["b"]

    def test_lista_vazia_de_existentes_mantem_todas(self):
        brutos = [_intimacao("a"), _intimacao("b")]

        novas = selecionar_novas_intimacoes(set(), brutos)

        assert len(novas) == 2

    def test_todas_ja_existentes_nao_sobra_nenhuma(self):
        brutos = [_intimacao("a"), _intimacao("b")]

        novas = selecionar_novas_intimacoes({"a", "b"}, brutos)

        assert novas == []


class TestSelecionarNovasAudiencias:
    def test_mantem_apenas_combos_com_id_esaj_novo(self):
        combos = [
            (_audiencia("Instrução"), "id-1"),
            (_audiencia("Julgamento"), "id-2"),
        ]

        novas = selecionar_novas_audiencias({"id-1"}, combos)

        assert len(novas) == 1
        assert novas[0][1] == "id-2"

    def test_nao_duplica_quando_todos_os_ids_ja_existem(self):
        combos = [(_audiencia("Instrução"), "id-1")]

        novas = selecionar_novas_audiencias({"id-1"}, combos)

        assert novas == []


class TestGerarNotificacoes:
    @pytest.mark.asyncio
    async def test_marca_is_new_false_depois_de_notificar(self):
        intimacao = Intimacao(titulo="Mero expediente", descricao="texto", is_new=True)
        audiencia = Audiencia(titulo="Instrução", local="Sala", is_new=True)

        class _Db:
            def add(self, _obj) -> None:
                return None

        await gerar_notificacoes(_Db(), uuid4(), [intimacao], [audiencia])

        assert intimacao.is_new is False
        assert audiencia.is_new is False
