"""Testes do branch de rate limit (429) em `coleta_esaj._coletar_pipe` —
sem banco real: usa um "db" fake que só registra `add`/`commit`, e uma
`TribunalSession` transiente (nunca persistida) só para ler/escrever
atributos, como o código de produção faz antes do commit."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.job_log import JOB_STATUS_FALHA, JOB_STATUS_SUCESSO
from app.models.tribunal import SESSION_STATUS_ATIVO, SESSION_STATUS_BLOQUEADO, TribunalSession
from app.schemas.esaj_cpo_raw import CpoDetalheRaw
from app.services.coleta_esaj import ERRO_RATE_LIMIT, _aplicar_detalhes_cpo, _coletar_pipe
from app.services.esaj_http import EsajRateLimitError


class _FakeDb:
    def __init__(self) -> None:
        self.job_logs: list = []

    def add(self, obj) -> None:
        self.job_logs.append(obj)

    async def commit(self) -> None:
        pass


def _sessao_ativa(**overrides) -> TribunalSession:
    base = {
        "status": SESSION_STATUS_ATIVO,
        "cookie_encrypted": b"cookie-fake",
        "tentativas_falha": 0,
        "proximo_retry": None,
    }
    base.update(overrides)
    return TribunalSession(**base)


class TestColetarPipeRateLimit:
    @pytest.mark.asyncio
    async def test_429_marca_bloqueado_e_seta_backoff_sem_anular_cookie(self):
        db = _FakeDb()
        sessao = _sessao_ativa()

        async def pipe_com_rate_limit():
            raise EsajRateLimitError("status_429")

        resultado = await _coletar_pipe(db, sessao, "user-1", "pipe_intimacoes", pipe_com_rate_limit())

        assert resultado is None
        assert sessao.status == SESSION_STATUS_BLOQUEADO
        assert sessao.tentativas_falha == 1
        assert sessao.proximo_retry is not None
        assert sessao.proximo_retry > datetime.now(UTC)
        # Rate limit não é sessão inválida — cookie continua lá.
        assert sessao.cookie_encrypted == b"cookie-fake"

        assert len(db.job_logs) == 1
        assert db.job_logs[0].status == JOB_STATUS_FALHA
        assert db.job_logs[0].erro == ERRO_RATE_LIMIT

    @pytest.mark.asyncio
    async def test_segunda_falha_seguida_aumenta_o_backoff(self):
        db = _FakeDb()
        sessao = _sessao_ativa(status=SESSION_STATUS_BLOQUEADO, tentativas_falha=1)

        async def pipe_com_rate_limit():
            raise EsajRateLimitError("status_429")

        await _coletar_pipe(db, sessao, "user-1", "pipe_intimacoes", pipe_com_rate_limit())

        assert sessao.tentativas_falha == 2

    @pytest.mark.asyncio
    async def test_sucesso_depois_de_bloqueio_zera_o_backoff(self):
        db = _FakeDb()
        sessao = _sessao_ativa(
            tentativas_falha=2, proximo_retry=datetime.now(UTC) + timedelta(minutes=15)
        )

        async def pipe_ok():
            return ["item"]

        resultado = await _coletar_pipe(db, sessao, "user-1", "pipe_intimacoes", pipe_ok())

        assert resultado == ["item"]
        assert sessao.tentativas_falha == 0
        assert sessao.proximo_retry is None
        assert db.job_logs[-1].status == JOB_STATUS_SUCESSO

    @pytest.mark.asyncio
    async def test_sucesso_sem_backoff_previo_nao_grava_commit_extra(self):
        db = _FakeDb()
        sessao = _sessao_ativa()

        async def pipe_ok():
            return []

        await _coletar_pipe(db, sessao, "user-1", "pipe_intimacoes", pipe_ok())

        assert sessao.tentativas_falha == 0
        assert sessao.proximo_retry is None


class _NestedOk:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeNestedDb:
    def begin_nested(self):
        return _NestedOk()


class TestAplicarDetalhesCpo:
    @pytest.mark.asyncio
    async def test_integrity_error_nao_avanca_throttle(self, monkeypatch):
        processo = SimpleNamespace(
            id=uuid4(),
            movimentacoes_synced_at=None,
            juiz=None,
            foro=None,
            partes_cpo=None,
            sem_incidentes=None,
            sem_apensos=None,
        )
        detalhe = CpoDetalheRaw()

        async def boom(*_args, **_kwargs):
            raise IntegrityError("INSERT", {}, Exception("unique"))

        monkeypatch.setattr(
            "app.services.coleta_esaj.diff_e_persistir_movimentacoes", boom
        )

        agora = datetime.now(UTC)
        novas = await _aplicar_detalhes_cpo(
            _FakeNestedDb(), {"CD": processo}, {"CD": detalhe}, agora
        )

        assert novas == []
        assert processo.movimentacoes_synced_at is None

    @pytest.mark.asyncio
    async def test_bloqueio_por_senha_avanca_throttle_sem_persistir(self):
        processo = SimpleNamespace(id=uuid4(), movimentacoes_synced_at=None)
        detalhe = CpoDetalheRaw(requer_senha_processo=True)
        agora = datetime.now(UTC)

        novas = await _aplicar_detalhes_cpo(
            _FakeNestedDb(), {"CD": processo}, {"CD": detalhe}, agora
        )

        assert novas == []
        assert processo.movimentacoes_synced_at == agora

    @pytest.mark.asyncio
    async def test_persistencia_ok_avanca_throttle(self, monkeypatch):
        processo = SimpleNamespace(
            id=uuid4(),
            movimentacoes_synced_at=None,
            juiz=None,
            foro=None,
            partes_cpo=None,
            sem_incidentes=None,
            sem_apensos=None,
        )
        detalhe = CpoDetalheRaw()

        async def vazio(*_args, **_kwargs):
            return []

        monkeypatch.setattr(
            "app.services.coleta_esaj.diff_e_persistir_movimentacoes", vazio
        )
        monkeypatch.setattr(
            "app.services.coleta_esaj.diff_e_persistir_peticoes_diversas", vazio
        )
        monkeypatch.setattr(
            "app.services.coleta_esaj.diff_e_persistir_audiencias_cpo", vazio
        )

        agora = datetime.now(UTC)
        novas = await _aplicar_detalhes_cpo(
            _FakeNestedDb(), {"CD": processo}, {"CD": detalhe}, agora
        )

        assert novas == []
        assert processo.movimentacoes_synced_at == agora
