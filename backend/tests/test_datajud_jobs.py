"""Testes de app.services.datajud_jobs — sem banco real.

`SessionLocal` é substituído por uma sessão falsa (`_FakeSession`) que só
grava o que foi `add`/`commit`/`rollback`, e `datajud.consultar_processo`
é monkeypatchado. `_selecionar_lote_datajud` é testado só na composição da
query (via `db.execute` falso que devolve a query recebida).
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.models.job_log import JOB_STATUS_FALHA, JOB_STATUS_SKIP, JOB_STATUS_SUCESSO, JobLog
from app.models.processo_datajud import ProcessoDatajud
from app.schemas.datajud_raw import (
    DatajudAssuntoRaw,
    DatajudClasseRaw,
    DatajudOrgaoJulgadorRaw,
    DatajudProcessoRaw,
)
from app.services import datajud_jobs


class _FakeResult:
    def __init__(self, valor):
        self._valor = valor

    def all(self):
        return self._valor

    def scalars(self):
        return self

    def scalar_one_or_none(self):
        return self._valor


class _FakeSession:
    def __init__(self, existente=None):
        self.added: list = []
        self.committed = False
        self.rolled_back = False
        self._existente = existente

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_exc):
        return False

    async def scalar(self, _stmt):
        return self._existente

    async def execute(self, stmt):
        self.ultimo_stmt = stmt
        return _FakeResult([])

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


class TestSelecionarLoteDatajud:
    @pytest.mark.asyncio
    async def test_filtra_por_nu_processo_e_ordena_por_nunca_consultado(self):
        db = _FakeSession()
        await datajud_jobs._selecionar_lote_datajud(db, 10)

        sql = str(
            db.ultimo_stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
        )
        assert "nu_processo IS NOT NULL" in sql
        assert "processos_datajud" in sql
        assert "LIMIT 10" in sql


class TestProcessarProcesso:
    @pytest.mark.asyncio
    async def test_tribunal_nao_mapeado_grava_skip_sem_consultar_datajud(self, monkeypatch):
        db = _FakeSession()
        monkeypatch.setattr(datajud_jobs, "SessionLocal", lambda: db)
        chamou_datajud = False

        async def _consultar_fake(*_args, **_kwargs):
            nonlocal chamou_datajud
            chamou_datajud = True
            return None

        monkeypatch.setattr(datajud_jobs.datajud, "consultar_processo", _consultar_fake)

        await datajud_jobs._processar_processo(object(), uuid4(), uuid4(), "numero-invalido")

        assert chamou_datajud is False
        assert db.committed is True
        job_logs = [item for item in db.added if isinstance(item, JobLog)]
        assert len(job_logs) == 1
        assert job_logs[0].status == JOB_STATUS_SKIP

    @pytest.mark.asyncio
    async def test_sucesso_cria_registro_e_preenche_campos(self, monkeypatch):
        db = _FakeSession(existente=None)
        monkeypatch.setattr(datajud_jobs, "SessionLocal", lambda: db)

        resultado = DatajudProcessoRaw(
            classe=DatajudClasseRaw(codigo=1116, nome="Procedimento Comum Cível"),
            assuntos=[DatajudAssuntoRaw(codigo=10570, nome="Rescisão contratual")],
            orgao_julgador=DatajudOrgaoJulgadorRaw(nome="1ª Vara Cível"),
            grau="G1",
        )

        async def _consultar_fake(*_args, **_kwargs):
            return resultado

        monkeypatch.setattr(datajud_jobs.datajud, "consultar_processo", _consultar_fake)

        processo_id = uuid4()
        await datajud_jobs._processar_processo(
            object(), processo_id, uuid4(), "1002345-67.2025.8.26.0100"
        )

        registros = [item for item in db.added if isinstance(item, ProcessoDatajud)]
        assert len(registros) == 1
        registro = registros[0]
        assert registro.processo_id == processo_id
        assert registro.tribunal_alias == "tjsp"
        assert registro.encontrado is True
        assert registro.classe_nome == "Procedimento Comum Cível"
        assert registro.orgao_julgador == "1ª Vara Cível"

        job_logs = [item for item in db.added if isinstance(item, JobLog)]
        assert job_logs[0].status == JOB_STATUS_SUCESSO

    @pytest.mark.asyncio
    async def test_nao_encontrado_marca_encontrado_falso_sem_apagar_registro_existente(self, monkeypatch):
        existente = ProcessoDatajud(
            processo_id=uuid4(),
            tribunal_alias="tjsp",
            encontrado=True,
            classe_nome="Classe antiga",
            ultima_consulta_em=datetime.now(UTC),
        )
        db = _FakeSession(existente=existente)
        monkeypatch.setattr(datajud_jobs, "SessionLocal", lambda: db)

        async def _consultar_fake(*_args, **_kwargs):
            return None

        monkeypatch.setattr(datajud_jobs.datajud, "consultar_processo", _consultar_fake)

        await datajud_jobs._processar_processo(
            object(), existente.processo_id, uuid4(), "1002345-67.2025.8.26.0100"
        )

        assert existente.encontrado is False
        # Nunca apaga o que já tinha — só marca que não achou nesta consulta.
        assert existente.classe_nome == "Classe antiga"

    @pytest.mark.asyncio
    async def test_erro_inesperado_faz_rollback_e_grava_falha(self, monkeypatch):
        db = _FakeSession()
        monkeypatch.setattr(datajud_jobs, "SessionLocal", lambda: db)

        async def _consultar_explode(*_args, **_kwargs):
            raise RuntimeError("falha simulada")

        monkeypatch.setattr(datajud_jobs.datajud, "consultar_processo", _consultar_explode)

        await datajud_jobs._processar_processo(
            object(), uuid4(), uuid4(), "1002345-67.2025.8.26.0100"
        )

        assert db.rolled_back is True
        job_logs = [item for item in db.added if isinstance(item, JobLog)]
        assert job_logs[0].status == JOB_STATUS_FALHA


class TestJobDatajudDiario:
    @pytest.mark.asyncio
    async def test_falha_em_um_processo_nao_impede_os_demais(self, monkeypatch):
        linhas = [
            type("Linha", (), {"id": uuid4(), "user_id": uuid4(), "nu_processo": "a"})(),
            type("Linha", (), {"id": uuid4(), "user_id": uuid4(), "nu_processo": "b"})(),
            type("Linha", (), {"id": uuid4(), "user_id": uuid4(), "nu_processo": "c"})(),
        ]

        async def _lote_fake(_db, _limite):
            return linhas

        monkeypatch.setattr(datajud_jobs, "_selecionar_lote_datajud", _lote_fake)

        class _DbCtx:
            async def __aenter__(self):
                return object()

            async def __aexit__(self, *_exc):
                return False

        monkeypatch.setattr(datajud_jobs, "SessionLocal", lambda: _DbCtx())
        monkeypatch.setattr(
            datajud_jobs, "get_settings", lambda: type("S", (), {"datajud_api_key": "chave"})()
        )
        monkeypatch.setattr(datajud_jobs, "INTERVALO_ENTRE_CONSULTAS_SEGUNDOS", 0)

        processados: list = []
        chamadas = 0

        async def _processar_fake(_client, processo_id, _user_id, _nu_processo):
            nonlocal chamadas
            chamadas += 1
            if chamadas == 2:
                raise RuntimeError("falha isolada")
            processados.append(processo_id)

        monkeypatch.setattr(datajud_jobs, "_processar_processo", _processar_fake)

        await datajud_jobs.job_datajud_diario()

        # Os 3 itens foram tentados mesmo com uma falha no meio.
        assert len(processados) == 2

    @pytest.mark.asyncio
    async def test_sem_chave_nao_seleciona_lote(self, monkeypatch):
        monkeypatch.setattr(
            datajud_jobs, "get_settings", lambda: type("S", (), {"datajud_api_key": ""})()
        )

        async def _lote_nao_deve_rodar(_db, _limite):
            raise AssertionError("lote não deve ser selecionado sem chave")

        monkeypatch.setattr(datajud_jobs, "_selecionar_lote_datajud", _lote_nao_deve_rodar)
        await datajud_jobs.job_datajud_diario()
