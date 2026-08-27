"""Testes das funções de diff (sem banco) — app.etl.diff."""

from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from types import SimpleNamespace

from app.etl.diff import (
    aplicar_complemento_cpo,
    gerar_notificacoes,
    selecionar_novas_audiencias,
    selecionar_novas_intimacoes,
    selecionar_novas_movimentacoes,
)
from app.schemas.esaj_cpo_raw import CapaCpoRaw, CpoDetalheRaw, ParteCpoRaw
from app.models.audiencia import Audiencia
from app.models.intimacao import Intimacao
from app.models.movimentacao import Movimentacao
from app.schemas.esaj_cpo_raw import MovimentacaoRaw
from app.schemas.esaj_raw import AudienciaRaw, IntimacaoRaw

TIMEZONE_SP = ZoneInfo("America/Sao_Paulo")


def _intimacao(id_: str) -> IntimacaoRaw:
    return IntimacaoRaw.model_validate({"id": id_, "cdProcesso": "1A0"})


def _audiencia(titulo: str) -> AudienciaRaw:
    return AudienciaRaw.model_validate({"cdProcesso": "1A0", "titulo": titulo})


def _movimentacao_raw(descricao: str) -> MovimentacaoRaw:
    return MovimentacaoRaw(data="18/08/2026", titulo=descricao, descricao=descricao)


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


class TestSelecionarNovasMovimentacoes:
    def test_lista_vazia_de_existentes_mantem_todas(self):
        data = datetime(2026, 8, 18, tzinfo=TIMEZONE_SP)
        combos = [
            (_movimentacao_raw("Certidão A"), data, "hash-a"),
            (_movimentacao_raw("Certidão B"), data, "hash-b"),
        ]

        novas = selecionar_novas_movimentacoes(set(), combos)

        assert len(novas) == 2

    def test_mantem_apenas_combos_com_identidade_nova(self):
        data = datetime(2026, 8, 18, tzinfo=TIMEZONE_SP)
        combos = [
            (_movimentacao_raw("Certidão A"), data, "hash-a"),
            (_movimentacao_raw("Certidão B"), data, "hash-b"),
        ]

        novas = selecionar_novas_movimentacoes({(data, "hash-a")}, combos)

        assert len(novas) == 1
        assert novas[0][2] == "hash-b"

    def test_todas_ja_existentes_nao_sobra_nenhuma(self):
        data = datetime(2026, 8, 18, tzinfo=TIMEZONE_SP)
        combos = [(_movimentacao_raw("Certidão A"), data, "hash-a")]

        novas = selecionar_novas_movimentacoes({(data, "hash-a")}, combos)

        assert novas == []

    def test_repete_no_mesmo_lote_so_entra_uma_vez(self):
        data = datetime(2026, 8, 11, tzinfo=TIMEZONE_SP)
        combos = [
            (_movimentacao_raw("Documento Juntado"), data, "hash-doc"),
            (_movimentacao_raw("Documento Juntado"), data, "hash-doc"),
            (_movimentacao_raw("Documento Juntado"), data, "hash-doc"),
        ]

        novas = selecionar_novas_movimentacoes(set(), combos)

        assert len(novas) == 1
        assert novas[0][2] == "hash-doc"


class TestGerarNotificacoes:
    @pytest.mark.asyncio
    async def test_marca_is_new_false_depois_de_notificar(self):
        intimacao = Intimacao(titulo="Mero expediente", descricao="texto", is_new=True)
        audiencia = Audiencia(titulo="Instrução", local="Sala", is_new=True)
        movimentacao = Movimentacao(descricao="Certidão de Publicação Expedida", is_new=True)

        class _Db:
            def add(self, _obj) -> None:
                return None

        await gerar_notificacoes(_Db(), uuid4(), [intimacao], [audiencia], [movimentacao])

        assert intimacao.is_new is False
        assert audiencia.is_new is False
        assert movimentacao.is_new is False

    @pytest.mark.asyncio
    async def test_sem_movimentacoes_nao_quebra_compatibilidade(self):
        intimacao = Intimacao(titulo="Mero expediente", descricao="texto", is_new=True)

        class _Db:
            def add(self, _obj) -> None:
                return None

        await gerar_notificacoes(_Db(), uuid4(), [intimacao], [])

        assert intimacao.is_new is False


class TestAplicarComplementoCpo:
    def test_nao_apaga_juiz_nem_partes_quando_o_html_nao_traz(self):
        processo = SimpleNamespace(
            juiz="Fulano",
            foro="Foro antigo",
            partes_cpo=[{"papel": "Reqte", "nome": "Parte", "advogados": None}],
            sem_incidentes=True,
            sem_apensos=True,
        )
        detalhe = CpoDetalheRaw(
            capa=CapaCpoRaw(foro="Foro novo"),
            partes=[],
            sem_incidentes=True,
            sem_apensos=True,
        )

        aplicar_complemento_cpo(processo, detalhe)

        assert processo.foro == "Foro novo"
        assert processo.juiz == "Fulano"
        assert processo.partes_cpo[0]["papel"] == "Reqte"

    def test_preenche_partes_quando_o_parser_passa_a_achar(self):
        processo = SimpleNamespace(
            juiz=None,
            foro=None,
            partes_cpo=[],
            sem_incidentes=True,
            sem_apensos=True,
        )
        detalhe = CpoDetalheRaw(
            capa=CapaCpoRaw(foro="Foro"),
            partes=[ParteCpoRaw(papel="Reqte", nome="Parte Ativa Fake")],
            sem_incidentes=True,
            sem_apensos=True,
        )

        aplicar_complemento_cpo(processo, detalhe)

        assert processo.partes_cpo == [
            {"papel": "Reqte", "nome": "Parte Ativa Fake", "advogados": None}
        ]
        assert processo.foro == "Foro"

    def test_flag_true_nao_volta_a_false_quando_marcador_some(self):
        processo = SimpleNamespace(
            juiz=None,
            foro=None,
            partes_cpo=None,
            sem_incidentes=True,
            sem_apensos=True,
        )
        detalhe = CpoDetalheRaw(sem_incidentes=False, sem_apensos=False)

        aplicar_complemento_cpo(processo, detalhe)

        assert processo.sem_incidentes is True
        assert processo.sem_apensos is True

    def test_flag_none_aceita_false_no_primeiro_sync(self):
        processo = SimpleNamespace(
            juiz=None,
            foro=None,
            partes_cpo=None,
            sem_incidentes=None,
            sem_apensos=None,
        )
        detalhe = CpoDetalheRaw(sem_incidentes=False, sem_apensos=False)

        aplicar_complemento_cpo(processo, detalhe)

        assert processo.sem_incidentes is False
        assert processo.sem_apensos is False

    def test_flag_false_vira_true_quando_marcador_aparece(self):
        processo = SimpleNamespace(
            juiz=None,
            foro=None,
            partes_cpo=None,
            sem_incidentes=False,
            sem_apensos=False,
        )
        detalhe = CpoDetalheRaw(sem_incidentes=True, sem_apensos=True)

        aplicar_complemento_cpo(processo, detalhe)

        assert processo.sem_incidentes is True
        assert processo.sem_apensos is True

