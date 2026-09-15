"""Testes das rotas do painel — sem banco real.

`get_db` é substituído por um dummy (evita conectar no Postgres) e as
funções de `app.services.painel` são monkeypatchadas. `get_current_user`
só é sobrescrito nos casos autenticados.
"""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.audiencia import Audiencia
from app.models.intimacao import Intimacao
from app.models.processo import Processo

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.schemas.notification import NotificationPublicSchema, NotificationsMarcadasSchema
from app.schemas.processo import (
    AudienciaPainelSchema,
    IntimacaoPainelSchema,
    IntimacaoPublicSchema,
    MovimentacaoPublicSchema,
    PartePublicSchema,
    ProcessoDetalheSchema,
    ProcessoListSchema,
    UltimaAtividadeSchema,
)
from app.services import painel as painel_service
from app.services.painel import (
    audiencia_para_painel,
    datajud_para_publico,
    intimacao_para_painel,
    intimacao_para_publico,
    montar_ultima_atividade,
    movimentacao_para_publico,
    processo_para_detalhe,
    processo_para_lista,
)

USER_ID = uuid4()
OUTRO_ID = uuid4()
PROCESSO_ID = uuid4()
NOTIF_ID = uuid4()


async def _db_dummy():
    yield SimpleNamespace()


def _user(user_id=USER_ID):
    return SimpleNamespace(id=user_id)


@pytest.fixture()
def client_factory():
    app.dependency_overrides[get_db] = _db_dummy
    yield
    app.dependency_overrides.clear()


async def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestSchemasSemIdEsaj:
    def test_intimacao_publica_nao_expoe_id_esaj(self):
        schema = IntimacaoPublicSchema(
            id=uuid4(),
            titulo="Mero expediente",
            descricao="texto",
            ciencia=False,
        )
        dumped = schema.model_dump()
        assert "id_esaj" not in dumped
        assert "oab" not in dumped

    def test_mapper_de_intimacao_ignora_id_esaj(self):
        item = SimpleNamespace(
            id=uuid4(),
            id_esaj="cdProcesso=AAA,nuSeqIntimacao=10,oab=123456SP",
            titulo="Mero expediente",
            descricao="texto",
            instancia="PG",
            data_movimentacao=None,
            ciencia=False,
        )
        publico = intimacao_para_publico(item)
        dumped = publico.model_dump()
        assert "id_esaj" not in dumped
        assert "123456SP" not in str(dumped)

    def test_mapper_painel_de_intimacao_nao_expoe_id_esaj_nem_processo_de_outro(self):
        item = SimpleNamespace(
            id=uuid4(),
            user_id=USER_ID,
            processo_id=PROCESSO_ID,
            id_esaj="cdProcesso=AAA,oab=123456SP",
            titulo="Mero expediente",
            descricao="texto",
            instancia="PG",
            data_movimentacao=None,
            ciencia=False,
        )
        outro = SimpleNamespace(
            user_id=OUTRO_ID,
            nu_processo="segredo",
            tribunal="esaj_tjsp",
            instancia="PG",
            foro="Foro",
            vara="Vara",
        )
        publico = intimacao_para_painel(item, outro)
        dumped = publico.model_dump()
        assert "id_esaj" not in dumped
        assert dumped["nu_processo"] is None
        assert "123456SP" not in str(dumped)

    def test_join_de_intimacao_e_audiencia_com_processo_exige_user_id_no_sql(self):
        on_intimacao = painel_service._on_processo_do_usuario(Intimacao.processo_id, USER_ID)
        sql_int = str(
            select(Intimacao, Processo)
            .outerjoin(Processo, on_intimacao)
            .compile(dialect=postgresql.dialect())
        )
        on_audiencia = painel_service._on_processo_do_usuario(Audiencia.processo_id, USER_ID)
        sql_aud = str(
            select(Audiencia, Processo)
            .outerjoin(Processo, on_audiencia)
            .compile(dialect=postgresql.dialect())
        )
        assert "processos.user_id" in sql_int
        assert "processos.user_id" in sql_aud

    def test_mapper_painel_de_audiencia_nao_expoe_id_esaj(self):
        publico = audiencia_para_painel(
            item_id=uuid4(),
            processo=SimpleNamespace(
                id=PROCESSO_ID,
                user_id=USER_ID,
                nu_processo="1002561-84.2026.8.26.0100",
                tribunal="esaj_tjsp",
                parte_ativa={"nome": "Acme", "representada": True},
                parte_passiva=None,
                foro="Foro",
                vara="Vara",
                juiz="Juiz",
            ),
            user_id=USER_ID,
            titulo="Instrução",
            data_audiencia=datetime(2026, 8, 25, tzinfo=UTC),
            local="Sala",
            situacao=None,
            fonte="agenda",
        )
        dumped = publico.model_dump()
        assert "id_esaj" not in dumped
        assert dumped["fonte"] == "agenda"
        assert dumped["nu_processo"] == "1002561-84.2026.8.26.0100"

    def test_detalhe_nao_carrega_id_esaj_de_audiencia(self):
        processo = SimpleNamespace(
            id=PROCESSO_ID,
            tribunal="esaj_tjsp",
            nu_processo="0000000-00.0000.0.00.0000",
            de_classe="Procedimento Comum",
            de_assunto="Assunto",
            instancia="PG",
            parte_ativa={"nome": "Parte Ativa", "representada": True},
            parte_passiva={"nome": "Parte Passiva", "representada": False},
            last_synced_at=None,
            url_cpo="https://esaj.tjsp.jus.br/cpopg/show.do",
            url_pasta=None,
        )
        audiencia = SimpleNamespace(
            id=uuid4(),
            id_esaj="cdProcesso=AAA|dataAudiencia=2026-01-01|titulo=Instrução",
            titulo="Instrução",
            data_audiencia=datetime(2026, 8, 25, 17, 0, tzinfo=UTC),
            local="Sala",
            created_at=datetime(2026, 5, 1, tzinfo=UTC),
        )
        detalhe = processo_para_detalhe(processo, [], [audiencia])
        dumped = detalhe.model_dump()
        assert "id_esaj" not in dumped
        assert "id_esaj" not in dumped["audiencias"][0]
        assert "oab" not in str(dumped).lower()

    def test_mapper_de_movimentacao_nao_expoe_campos_internos(self):
        item = SimpleNamespace(
            id=uuid4(),
            titulo="Certidão de Publicação Expedida",
            descricao="Certidão de Publicação Expedida\nRelação: 999/2026",
            data_movimentacao=datetime(2026, 8, 18, tzinfo=UTC),
            processo_id=PROCESSO_ID,
            descricao_hash="abc123",
            is_new=True,
        )
        publico = movimentacao_para_publico(item)
        dumped = publico.model_dump()
        assert "descricao_hash" not in dumped
        assert "processo_id" not in dumped
        assert "is_new" not in dumped
        assert dumped["descricao"] == "Relação: 999/2026"
        assert dumped["tem_documento"] is False
        assert dumped["url_documento"] is None

    def test_mapper_so_expoe_url_https_do_esaj(self):
        item = SimpleNamespace(
            id=uuid4(),
            titulo="Despacho",
            descricao="Despacho",
            data_movimentacao=datetime(2026, 8, 18, tzinfo=UTC),
            tem_documento=True,
            url_documento="javascript:alert(1)",
        )
        publico = movimentacao_para_publico(item)
        assert publico.tem_documento is True
        assert publico.url_documento is None

    def test_mapper_repassa_url_https_do_documento_no_esaj(self):
        url = (
            "https://esaj.tjsp.jus.br/cpopg/abrirDocumentoVinculadoMovimentacao.do"
            "?processo.codigo=ABC&cdDocumento=1"
        )
        item = SimpleNamespace(
            id=uuid4(),
            titulo="Despacho",
            descricao="Despacho",
            data_movimentacao=datetime(2026, 8, 18, tzinfo=UTC),
            tem_documento=True,
            url_documento=url,
        )
        publico = movimentacao_para_publico(item)
        assert publico.url_documento == url

    def test_mapper_nao_repete_titulo_quando_descricao_e_so_o_titulo(self):
        item = SimpleNamespace(
            id=uuid4(),
            titulo="Conclusos para Decisão",
            descricao="Conclusos para Decisão",
            data_movimentacao=datetime(2026, 8, 18, tzinfo=UTC),
        )
        assert movimentacao_para_publico(item).descricao == ""

    def test_mapper_preserva_descricao_quando_primeira_linha_nao_e_o_titulo(self):
        item = SimpleNamespace(
            id=uuid4(),
            titulo="Título",
            descricao="Outra coisa\nDetalhe",
            data_movimentacao=datetime(2026, 8, 18, tzinfo=UTC),
        )
        assert movimentacao_para_publico(item).descricao == "Outra coisa\nDetalhe"

    def test_detalhe_ordena_movimentacoes_da_mais_recente_para_a_mais_antiga(self):
        processo = SimpleNamespace(
            id=PROCESSO_ID,
            tribunal="esaj_tjsp",
            nu_processo="0000000-00.0000.0.00.0000",
            de_classe=None,
            de_assunto=None,
            instancia=None,
            parte_ativa=None,
            parte_passiva=None,
            last_synced_at=None,
            url_cpo=None,
            url_pasta=None,
        )
        antiga = SimpleNamespace(
            id=uuid4(),
            titulo="Movimentação antiga",
            descricao="texto",
            data_movimentacao=datetime(2026, 1, 1, tzinfo=UTC),
        )
        recente = SimpleNamespace(
            id=uuid4(),
            titulo="Movimentação recente",
            descricao="texto",
            data_movimentacao=datetime(2026, 8, 18, tzinfo=UTC),
        )
        detalhe = processo_para_detalhe(processo, [], [], [antiga, recente])
        assert [m.titulo for m in detalhe.movimentacoes] == ["Movimentação recente", "Movimentação antiga"]

    def test_detalhe_sem_movimentacoes_nao_quebra(self):
        processo = SimpleNamespace(
            id=PROCESSO_ID,
            tribunal="esaj_tjsp",
            nu_processo="0000000-00.0000.0.00.0000",
            de_classe=None,
            de_assunto=None,
            instancia=None,
            parte_ativa=None,
            parte_passiva=None,
            last_synced_at=None,
            url_cpo=None,
            url_pasta=None,
        )
        detalhe = processo_para_detalhe(processo, [], [])
        assert detalhe.movimentacoes == []
        assert detalhe.movimentacoes_status == "pendente"

    def test_detalhe_sem_movimentacoes_apos_sync_marca_indisponivel(self):
        processo = SimpleNamespace(
            id=PROCESSO_ID,
            tribunal="esaj_tjsp",
            nu_processo="0000000-00.0000.0.00.0000",
            de_classe=None,
            de_assunto=None,
            instancia=None,
            parte_ativa=None,
            parte_passiva=None,
            last_synced_at=None,
            url_cpo=None,
            url_pasta=None,
            movimentacoes_synced_at=datetime(2026, 8, 23, tzinfo=UTC),
        )
        detalhe = processo_para_detalhe(processo, [], [])
        assert detalhe.movimentacoes_status == "indisponivel"

    def test_detalhe_mapeia_capa_partes_e_flags_sem_html(self):
        processo = SimpleNamespace(
            id=PROCESSO_ID,
            tribunal="esaj_tjsp",
            nu_processo="0000000-00.0000.0.00.0000",
            de_classe="Procedimento Comum",
            de_assunto="Assunto JSON",
            instancia="PG",
            parte_ativa={"nome": "Polo JSON", "representada": True},
            parte_passiva=None,
            last_synced_at=None,
            url_cpo=None,
            url_pasta=None,
            movimentacoes_synced_at=datetime(2026, 8, 23, tzinfo=UTC),
            foro="Foro Central",
            vara="1ª Vara",
            juiz="Fulano de Tal",
            distribuicao="01/01/2020 às 10:00",
            controle="2020/000001",
            area="Cível",
            valor_acao="R$ 1.000,00",
            partes_cpo=[
                {"papel": "Reqte", "nome": "Autor CPO", "advogados": "Advogado"},
            ],
            sem_incidentes=True,
            sem_apensos=True,
        )
        detalhe = processo_para_detalhe(processo, [], [])
        dumped = detalhe.model_dump()
        assert dumped["juiz"] == "Fulano de Tal"
        assert dumped["foro"] == "Foro Central"
        assert dumped["de_classe"] == "Procedimento Comum"
        assert dumped["partes_cpo"] == [
            {"papel": "Reqte", "nome": "Autor CPO", "advogados": "Advogado"}
        ]
        assert dumped["sem_incidentes"] is True
        assert dumped["sem_apensos"] is True
        assert "<" not in str(dumped["partes_cpo"])

    def test_detalhe_nao_expoe_identidade_hash_de_peticao_nem_audiencia_cpo(self):
        processo = SimpleNamespace(
            id=PROCESSO_ID,
            tribunal="esaj_tjsp",
            nu_processo="0000000-00.0000.0.00.0000",
            de_classe=None,
            de_assunto=None,
            instancia=None,
            parte_ativa=None,
            parte_passiva=None,
            last_synced_at=None,
            url_cpo=None,
            url_pasta=None,
        )
        peticao = SimpleNamespace(
            id=uuid4(),
            data_peticao=datetime(2023, 10, 3, tzinfo=UTC),
            tipo="Petição Intermediária",
            protocolo="FAKE.1",
            identidade_hash="abc123",
            processo_id=PROCESSO_ID,
        )
        audiencia_cpo = SimpleNamespace(
            id=uuid4(),
            data_audiencia=datetime(2026, 8, 25, tzinfo=UTC),
            titulo="Instrução",
            situacao="Realizada",
            qt_pessoas="3",
            identidade_hash="def456",
            processo_id=PROCESSO_ID,
        )
        detalhe = processo_para_detalhe(
            processo, [], [], [], [peticao], [audiencia_cpo]
        )
        dumped = detalhe.model_dump()
        assert "identidade_hash" not in dumped["peticoes_diversas"][0]
        assert "processo_id" not in dumped["peticoes_diversas"][0]
        assert dumped["peticoes_diversas"][0]["tipo"] == "Petição Intermediária"
        assert "identidade_hash" not in dumped["audiencias_cpo"][0]
        assert dumped["audiencias_cpo"][0]["titulo"] == "Instrução"
        assert dumped["audiencias"] == []

    def test_detalhe_sem_complemento_datajud_devolve_none(self):
        processo = SimpleNamespace(
            id=PROCESSO_ID,
            tribunal="esaj_tjsp",
            nu_processo="0000000-00.0000.0.00.0000",
            de_classe=None,
            de_assunto=None,
            instancia=None,
            parte_ativa=None,
            parte_passiva=None,
            last_synced_at=None,
            url_cpo=None,
            url_pasta=None,
        )
        detalhe = processo_para_detalhe(processo, [], [])
        assert detalhe.datajud is None

    def test_detalhe_com_complemento_datajud_expoe_secao_separada(self):
        processo = SimpleNamespace(
            id=PROCESSO_ID,
            tribunal="esaj_tjsp",
            nu_processo="1002345-67.2025.8.26.0100",
            de_classe="Classe do e-SAJ",
            de_assunto=None,
            instancia=None,
            parte_ativa=None,
            parte_passiva=None,
            last_synced_at=None,
            url_cpo=None,
            url_pasta=None,
        )
        datajud = SimpleNamespace(
            classe_nome="Procedimento Comum Cível",
            assuntos=[{"codigo": 10570, "nome": "Rescisão contratual"}],
            orgao_julgador="1ª Vara Cível",
            data_ajuizamento=datetime(2025, 3, 10, tzinfo=UTC),
            grau="G1",
            formato="Eletrônico",
            movimentos=[{"codigo": 51, "nome": "Distribuído", "data_hora": None}],
            encontrado=True,
            ultima_consulta_em=datetime(2026, 9, 1, tzinfo=UTC),
        )
        detalhe = processo_para_detalhe(processo, [], [], datajud=datajud)
        dumped = detalhe.model_dump()
        # Nunca sobrescreve o que já veio do e-SAJ.
        assert dumped["de_classe"] == "Classe do e-SAJ"
        assert dumped["datajud"]["classe_nome"] == "Procedimento Comum Cível"
        assert dumped["datajud"]["orgao_julgador"] == "1ª Vara Cível"
        assert dumped["datajud"]["encontrado"] is True
        assert dumped["datajud"]["assuntos"][0]["nome"] == "Rescisão contratual"

    def test_datajud_para_publico_com_none_devolve_none(self):
        assert datajud_para_publico(None) is None

    def test_lista_nao_inclui_capa_cpo(self):
        processo = SimpleNamespace(
            id=PROCESSO_ID,
            tribunal="esaj_tjsp",
            nu_processo="0000000-00.0000.0.00.0000",
            de_classe="Procedimento Comum",
            de_assunto=None,
            instancia=None,
            parte_ativa={"nome": "Polo JSON", "representada": True},
            parte_passiva=None,
            last_synced_at=None,
            foro="Foro que não deve ir para a lista",
            juiz="Magistrado",
        )
        lista = processo_para_lista(processo, [], [])
        dumped = lista.model_dump()
        assert "foro" not in dumped
        assert "juiz" not in dumped
        assert "partes_cpo" not in dumped
        assert dumped["fixado"] is False

    def test_mapper_repassa_fixado(self):
        processo = SimpleNamespace(
            id=PROCESSO_ID,
            tribunal="esaj_tjsp",
            nu_processo="1002561-84.2026.8.26.0100",
            de_classe=None,
            de_assunto=None,
            instancia=None,
            parte_ativa=None,
            parte_passiva=None,
            last_synced_at=None,
            fixado=True,
        )
        lista = processo_para_lista(processo, [], [])
        assert lista.fixado is True

    def test_ultima_atividade_escolhe_o_evento_mais_recente(self):
        intimacao = SimpleNamespace(
            titulo="Intimação velha",
            data_movimentacao=datetime(2026, 1, 1, tzinfo=UTC),
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        audiencia = SimpleNamespace(
            titulo="Audiência nova",
            data_audiencia=datetime(2026, 8, 25, tzinfo=UTC),
            created_at=datetime(2026, 8, 1, tzinfo=UTC),
        )
        atividade = montar_ultima_atividade([intimacao], [audiencia])
        assert atividade is not None
        assert atividade.tipo == "audiencia"
        assert atividade.titulo == "Audiência nova"


class TestRotasProcessos:
    @pytest.mark.asyncio
    async def test_sem_token_retorna_401(self, client_factory):
        async with await _client() as client:
            resposta = await client.get("/processos")
        assert resposta.status_code == 401

    @pytest.mark.asyncio
    async def test_lista_so_do_usuario_autenticado(self, client_factory, monkeypatch):
        app.dependency_overrides[get_current_user] = lambda: _user()

        async def fake_listar(db, user_id, *, q=None):
            assert user_id == USER_ID
            assert q is None
            return [
                ProcessoListSchema(
                    id=PROCESSO_ID,
                    tribunal="esaj_tjsp",
                    nu_processo="1002561-84.2026.8.26.0100",
                    parte_ativa=PartePublicSchema(nome="Acme"),
                    ultima_atividade=UltimaAtividadeSchema(
                        tipo="intimacao", titulo="Mero expediente", data=datetime.now(UTC)
                    ),
                )
            ]

        monkeypatch.setattr(painel_service, "listar_processos", fake_listar)

        async with await _client() as client:
            resposta = await client.get("/processos")

        assert resposta.status_code == 200
        corpo = resposta.json()
        assert len(corpo) == 1
        assert corpo[0]["id"] == str(PROCESSO_ID)
        assert "id_esaj" not in corpo[0]
        assert "id_esaj" not in str(corpo)

    @pytest.mark.asyncio
    async def test_detalhe_de_outro_usuario_retorna_404(self, client_factory, monkeypatch):
        app.dependency_overrides[get_current_user] = lambda: _user()

        async def fake_detalhe(db, user_id, processo_id):
            assert user_id == USER_ID
            return None

        monkeypatch.setattr(painel_service, "buscar_processo_detalhe", fake_detalhe)

        async with await _client() as client:
            resposta = await client.get(f"/processos/{PROCESSO_ID}")

        assert resposta.status_code == 404
        assert resposta.json()["detail"] == "Processo não encontrado"

    @pytest.mark.asyncio
    async def test_detalhe_do_dono_nao_inclui_id_esaj(self, client_factory, monkeypatch):
        app.dependency_overrides[get_current_user] = lambda: _user()
        detalhe = ProcessoDetalheSchema(
            id=PROCESSO_ID,
            tribunal="esaj_tjsp",
            nu_processo="1002561-84.2026.8.26.0100",
            intimacoes=[
                IntimacaoPublicSchema(id=uuid4(), titulo="Mero expediente", ciencia=False)
            ],
            audiencias=[],
        )

        async def fake_detalhe(db, user_id, processo_id):
            return detalhe

        monkeypatch.setattr(painel_service, "buscar_processo_detalhe", fake_detalhe)

        async with await _client() as client:
            resposta = await client.get(f"/processos/{PROCESSO_ID}")

        assert resposta.status_code == 200
        corpo = resposta.json()
        assert "id_esaj" not in corpo
        assert "id_esaj" not in corpo["intimacoes"][0]

    @pytest.mark.asyncio
    async def test_detalhe_inclui_movimentacoes_sem_campos_internos(self, client_factory, monkeypatch):
        app.dependency_overrides[get_current_user] = lambda: _user()
        detalhe = ProcessoDetalheSchema(
            id=PROCESSO_ID,
            tribunal="esaj_tjsp",
            nu_processo="1002561-84.2026.8.26.0100",
            movimentacoes=[
                MovimentacaoPublicSchema(
                    id=uuid4(),
                    titulo="Certidão de Publicação Expedida",
                    descricao="Certidão de Publicação Expedida\nRelação: 999/2026",
                    data_movimentacao=datetime(2026, 8, 18, tzinfo=UTC),
                )
            ],
        )

        async def fake_detalhe(db, user_id, processo_id):
            return detalhe

        monkeypatch.setattr(painel_service, "buscar_processo_detalhe", fake_detalhe)

        async with await _client() as client:
            resposta = await client.get(f"/processos/{PROCESSO_ID}")

        assert resposta.status_code == 200
        corpo = resposta.json()
        assert len(corpo["movimentacoes"]) == 1
        assert corpo["movimentacoes"][0]["titulo"] == "Certidão de Publicação Expedida"
        assert "descricao_hash" not in str(corpo)
        assert "processo_id" not in corpo["movimentacoes"][0]

    @pytest.mark.asyncio
    async def test_fixar_de_outro_usuario_retorna_404(self, client_factory, monkeypatch):
        app.dependency_overrides[get_current_user] = lambda: _user()

        async def fake_fixar(db, user_id, processo_id, *, fixado):
            assert user_id == USER_ID
            assert fixado is True
            return None

        monkeypatch.setattr(painel_service, "atualizar_fixado", fake_fixar)

        async with await _client() as client:
            resposta = await client.patch(
                f"/processos/{PROCESSO_ID}", json={"fixado": True}
            )

        assert resposta.status_code == 404
        assert resposta.json()["detail"] == "Processo não encontrado"

    @pytest.mark.asyncio
    async def test_fixar_do_dono_retorna_id_e_flag(self, client_factory, monkeypatch):
        app.dependency_overrides[get_current_user] = lambda: _user()

        async def fake_fixar(db, user_id, processo_id, *, fixado):
            assert user_id == USER_ID
            assert processo_id == PROCESSO_ID
            assert fixado is False
            return ProcessoListSchema(
                id=PROCESSO_ID,
                tribunal="esaj_tjsp",
                nu_processo="1002561-84.2026.8.26.0100",
                fixado=False,
            )

        monkeypatch.setattr(painel_service, "atualizar_fixado", fake_fixar)

        async with await _client() as client:
            resposta = await client.patch(
                f"/processos/{PROCESSO_ID}", json={"fixado": False}
            )

        assert resposta.status_code == 200
        corpo = resposta.json()
        assert corpo == {"id": str(PROCESSO_ID), "fixado": False}
        assert "nu_processo" not in corpo
        assert "id_esaj" not in corpo

    @pytest.mark.asyncio
    async def test_lista_intimacoes_sem_token_retorna_401(self, client_factory):
        async with await _client() as client:
            resposta = await client.get("/intimacoes")
        assert resposta.status_code == 401

    @pytest.mark.asyncio
    async def test_lista_intimacoes_so_do_jwt_sem_id_esaj(self, client_factory, monkeypatch):
        app.dependency_overrides[get_current_user] = lambda: _user()

        async def fake_listar(db, user_id):
            assert user_id == USER_ID
            return [
                IntimacaoPainelSchema(
                    id=uuid4(),
                    processo_id=PROCESSO_ID,
                    nu_processo="1002561-84.2026.8.26.0100",
                    tribunal="esaj_tjsp",
                    titulo="Mero expediente",
                    descricao="texto",
                    ciencia=False,
                )
            ]

        monkeypatch.setattr(painel_service, "listar_intimacoes_painel", fake_listar)

        async with await _client() as client:
            resposta = await client.get("/intimacoes")

        assert resposta.status_code == 200
        corpo = resposta.json()
        assert len(corpo) == 1
        assert "id_esaj" not in corpo[0]
        assert "oab" not in str(corpo).lower()

    @pytest.mark.asyncio
    async def test_lista_audiencias_so_do_jwt_sem_id_esaj(self, client_factory, monkeypatch):
        app.dependency_overrides[get_current_user] = lambda: _user()

        async def fake_listar(db, user_id):
            assert user_id == USER_ID
            return [
                AudienciaPainelSchema(
                    id=uuid4(),
                    processo_id=PROCESSO_ID,
                    nu_processo="1002561-84.2026.8.26.0100",
                    tribunal="esaj_tjsp",
                    titulo="Instrução",
                    fonte="agenda",
                )
            ]

        monkeypatch.setattr(painel_service, "listar_audiencias_painel", fake_listar)

        async with await _client() as client:
            resposta = await client.get("/audiencias")

        assert resposta.status_code == 200
        corpo = resposta.json()
        assert corpo[0]["titulo"] == "Instrução"
        assert "id_esaj" not in corpo[0]


class TestRotasNotifications:
    @pytest.mark.asyncio
    async def test_sem_token_retorna_401(self, client_factory):
        async with await _client() as client:
            resposta = await client.get("/notifications")
        assert resposta.status_code == 401

    @pytest.mark.asyncio
    async def test_lista_filtra_pelo_usuario_do_jwt(self, client_factory, monkeypatch):
        app.dependency_overrides[get_current_user] = lambda: _user()

        async def fake_listar(db, user_id, *, somente_nao_lidas=False):
            assert user_id == USER_ID
            assert somente_nao_lidas is False
            return [
                NotificationPublicSchema(
                    id=NOTIF_ID,
                    processo_id=PROCESSO_ID,
                    tipo="intimacao",
                    titulo="Nova intimação: Mero expediente",
                    message="Texto",
                    is_read=False,
                    created_at=datetime.now(UTC),
                )
            ]

        monkeypatch.setattr(painel_service, "listar_notificacoes", fake_listar)

        async with await _client() as client:
            resposta = await client.get("/notifications")

        assert resposta.status_code == 200
        corpo = resposta.json()
        assert corpo[0]["id"] == str(NOTIF_ID)
        assert "id_esaj" not in corpo[0]

    @pytest.mark.asyncio
    async def test_marcar_lida_de_outro_usuario_retorna_404(self, client_factory, monkeypatch):
        app.dependency_overrides[get_current_user] = lambda: _user()

        async def fake_marcar(db, user_id, notificacao_id):
            assert user_id == USER_ID
            return None

        monkeypatch.setattr(painel_service, "marcar_notificacao_lida", fake_marcar)

        async with await _client() as client:
            resposta = await client.patch(f"/notifications/{NOTIF_ID}", json={"is_read": True})

        assert resposta.status_code == 404

    @pytest.mark.asyncio
    async def test_marcar_todas_lidas(self, client_factory, monkeypatch):
        app.dependency_overrides[get_current_user] = lambda: _user()

        async def fake_todas(db, user_id):
            assert user_id == USER_ID
            return 3

        monkeypatch.setattr(painel_service, "marcar_todas_lidas", fake_todas)

        async with await _client() as client:
            resposta = await client.post("/notifications/marcar-lidas")

        assert resposta.status_code == 200
        assert resposta.json() == NotificationsMarcadasSchema(marcadas=3).model_dump()
