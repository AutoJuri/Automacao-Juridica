"""Testes da decisão por advogado do job de 10 minutos
(`scheduler_jobs._processar_advogado`) — sem banco real: `TribunalSession`
transiente só para setar os atributos que a decisão lê, e
`validar_credencial_esaj` / `executar_ciclo_usuario` / `_reativar_apos_bloqueio`
mockados via monkeypatch (são as únicas funções que tocam o banco)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.models.tribunal import (
    SESSION_STATUS_ATIVO,
    SESSION_STATUS_BLOQUEADO,
    SESSION_STATUS_CODIGO_NAO_ENCONTRADO,
    SESSION_STATUS_CREDENCIAL_INVALIDA,
    SESSION_STATUS_EMAIL_DESCONECTADO,
    SESSION_STATUS_PORTAL_INDISPONIVEL,
    SESSION_STATUS_REAUTH_PENDENTE,
    TribunalSession,
)
from app.services import scheduler_jobs
from app.services.scheduler_jobs import _processar_advogado, job_renovacao_diaria

USER_ID = uuid4()


class _Spy:
    def __init__(self) -> None:
        self.chamadas: list[tuple] = []

    async def __call__(self, *args, **kwargs) -> None:
        self.chamadas.append((args, kwargs))


@pytest.fixture()
def spies(monkeypatch: pytest.MonkeyPatch):
    validar = _Spy()
    executar = _Spy()
    reativar = _Spy()
    monkeypatch.setattr(scheduler_jobs, "validar_credencial_esaj", validar)
    monkeypatch.setattr(scheduler_jobs, "executar_ciclo_usuario", executar)
    monkeypatch.setattr(scheduler_jobs, "_reativar_apos_bloqueio", reativar)
    monkeypatch.setattr(scheduler_jobs, "validacao_em_andamento", lambda _uid: False)
    return {"validar": validar, "executar": executar, "reativar": reativar}


def _sessao(status: str, **overrides) -> TribunalSession:
    base = {"status": status, "proximo_retry": None, "updated_at": datetime.now(UTC)}
    base.update(overrides)
    return TribunalSession(**base)


def _sessao_ativa(**overrides) -> TribunalSession:
    agora = datetime.now(UTC)
    base = {
        "status": SESSION_STATUS_ATIVO,
        "cookie_encrypted": b"cookie",
        "expires_at": agora + timedelta(hours=10),
        "proximo_retry": None,
        "updated_at": agora,
    }
    base.update(overrides)
    return TribunalSession(**base)


class TestProcessarAdvogado:
    @pytest.mark.asyncio
    async def test_sem_sessao_dispara_reauth(self, spies):
        await _processar_advogado(USER_ID, None, datetime.now(UTC))

        assert len(spies["validar"].chamadas) == 1
        assert len(spies["executar"].chamadas) == 0

    @pytest.mark.asyncio
    async def test_ativo_roda_ciclo_de_pipes(self, spies):
        sessao = _sessao_ativa()

        await _processar_advogado(USER_ID, sessao, datetime.now(UTC))

        assert len(spies["executar"].chamadas) == 1
        assert len(spies["validar"].chamadas) == 0

    @pytest.mark.asyncio
    async def test_ativo_com_cookie_expirado_dispara_reauth_sem_pipes(self, spies):
        sessao = _sessao_ativa(expires_at=datetime.now(UTC) - timedelta(minutes=1))

        await _processar_advogado(USER_ID, sessao, datetime.now(UTC))

        assert len(spies["validar"].chamadas) == 1
        assert len(spies["executar"].chamadas) == 0

    @pytest.mark.asyncio
    async def test_validacao_em_andamento_pula_pipes_e_reauth(self, spies, monkeypatch):
        monkeypatch.setattr(scheduler_jobs, "validacao_em_andamento", lambda _uid: True)
        sessao = _sessao_ativa()

        await _processar_advogado(USER_ID, sessao, datetime.now(UTC))

        assert len(spies["executar"].chamadas) == 0
        assert len(spies["validar"].chamadas) == 0

    @pytest.mark.asyncio
    async def test_bloqueado_com_backoff_expirado_reativa_e_roda_pipes(self, spies):
        agora = datetime.now(UTC)
        sessao = _sessao(SESSION_STATUS_BLOQUEADO, proximo_retry=agora - timedelta(minutes=1))

        await _processar_advogado(USER_ID, sessao, agora)

        assert len(spies["reativar"].chamadas) == 1
        assert len(spies["executar"].chamadas) == 1
        assert len(spies["validar"].chamadas) == 0

    @pytest.mark.asyncio
    async def test_bloqueado_com_backoff_pendente_nao_faz_nada(self, spies):
        agora = datetime.now(UTC)
        sessao = _sessao(SESSION_STATUS_BLOQUEADO, proximo_retry=agora + timedelta(minutes=10))

        await _processar_advogado(USER_ID, sessao, agora)

        assert len(spies["reativar"].chamadas) == 0
        assert len(spies["executar"].chamadas) == 0
        assert len(spies["validar"].chamadas) == 0

    @pytest.mark.asyncio
    async def test_bloqueado_sem_proximo_retry_e_tratado_como_expirado(self, spies):
        sessao = _sessao(SESSION_STATUS_BLOQUEADO, proximo_retry=None)

        await _processar_advogado(USER_ID, sessao, datetime.now(UTC))

        assert len(spies["reativar"].chamadas) == 1
        assert len(spies["executar"].chamadas) == 1

    @pytest.mark.asyncio
    async def test_reauth_pendente_recente_tambem_dispara_validacao(self, spies):
        agora = datetime.now(UTC)
        sessao = _sessao(SESSION_STATUS_REAUTH_PENDENTE, updated_at=agora - timedelta(minutes=1))

        await _processar_advogado(USER_ID, sessao, agora)

        assert len(spies["validar"].chamadas) == 1
        assert len(spies["executar"].chamadas) == 0

    @pytest.mark.parametrize(
        "status",
        [SESSION_STATUS_EMAIL_DESCONECTADO, SESSION_STATUS_PORTAL_INDISPONIVEL, SESSION_STATUS_CODIGO_NAO_ENCONTRADO],
    )
    @pytest.mark.asyncio
    async def test_erros_elegiveis_com_backoff_expirado_disparam_reauth(self, spies, status):
        agora = datetime.now(UTC)
        sessao = _sessao(status, proximo_retry=agora - timedelta(seconds=1))

        await _processar_advogado(USER_ID, sessao, agora)

        assert len(spies["validar"].chamadas) == 1

    @pytest.mark.parametrize(
        "status",
        [SESSION_STATUS_EMAIL_DESCONECTADO, SESSION_STATUS_PORTAL_INDISPONIVEL, SESSION_STATUS_CODIGO_NAO_ENCONTRADO],
    )
    @pytest.mark.asyncio
    async def test_erros_elegiveis_com_backoff_pendente_nao_disparam_nada(self, spies, status):
        agora = datetime.now(UTC)
        sessao = _sessao(status, proximo_retry=agora + timedelta(minutes=5))

        await _processar_advogado(USER_ID, sessao, agora)

        assert len(spies["validar"].chamadas) == 0
        assert len(spies["executar"].chamadas) == 0

    @pytest.mark.asyncio
    async def test_credencial_invalida_nao_faz_nada(self, spies):
        sessao = _sessao(SESSION_STATUS_CREDENCIAL_INVALIDA)

        await _processar_advogado(USER_ID, sessao, datetime.now(UTC))

        assert len(spies["validar"].chamadas) == 0
        assert len(spies["executar"].chamadas) == 0
        assert len(spies["reativar"].chamadas) == 0


class TestJobRenovacaoDiaria:
    @pytest.mark.asyncio
    async def test_isola_falha_por_advogado(self, monkeypatch: pytest.MonkeyPatch):
        primeiro, segundo = uuid4(), uuid4()

        class _Resultado:
            def scalars(self):
                return self

            def all(self):
                return [primeiro, segundo]

        class _SessaoFake:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def execute(self, *_args, **_kwargs):
                return _Resultado()

        monkeypatch.setattr(scheduler_jobs, "SessionLocal", lambda: _SessaoFake())

        chamadas: list = []

        async def validar(user_id, **_kwargs):
            chamadas.append(user_id)
            if user_id == primeiro:
                raise RuntimeError("falha isolada")

        monkeypatch.setattr(scheduler_jobs, "validar_credencial_esaj", validar)

        await job_renovacao_diaria()

        assert chamadas == [primeiro, segundo]
