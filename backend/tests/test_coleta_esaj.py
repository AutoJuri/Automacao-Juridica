"""Testes do branch de rate limit (429) em `coleta_esaj._coletar_pipe` —
sem banco real: usa um "db" fake que só registra `add`/`commit`, e uma
`TribunalSession` transiente (nunca persistida) só para ler/escrever
atributos, como o código de produção faz antes do commit."""

from datetime import UTC, datetime, timedelta

import pytest

from app.models.job_log import JOB_STATUS_FALHA, JOB_STATUS_SUCESSO
from app.models.tribunal import SESSION_STATUS_ATIVO, SESSION_STATUS_BLOQUEADO, TribunalSession
from app.services.coleta_esaj import ERRO_RATE_LIMIT, _coletar_pipe
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
