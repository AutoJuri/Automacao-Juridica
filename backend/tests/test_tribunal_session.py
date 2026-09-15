"""Testes do helper `TribunalSession.cookie_expirado` — sem banco."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.models.tribunal import SESSION_STATUS_ATIVO, SESSION_STATUS_REAUTH_PENDENTE, TribunalSession


def _sessao(**kwargs) -> TribunalSession:
    padrao = {
        "user_id": uuid4(),
        "tribunal": "esaj_tjsp",
        "cookie_encrypted": b"blob",
        "status": SESSION_STATUS_ATIVO,
        "expires_at": datetime.now(UTC) + timedelta(hours=12),
    }
    padrao.update(kwargs)
    return TribunalSession(**padrao)


class TestCookieExpirado:
    def test_ativo_com_prazo_futuro_nao_expirou(self):
        assert _sessao().cookie_expirado() is False

    def test_ativo_com_prazo_passado_expirou(self):
        sessao = _sessao(expires_at=datetime.now(UTC) - timedelta(hours=1))
        assert sessao.cookie_expirado() is True

    def test_ativo_sem_cookie_conta_como_expirado(self):
        sessao = _sessao(cookie_encrypted=None)
        assert sessao.cookie_expirado() is True

    def test_status_diferente_de_ativo_nao_e_expirado(self):
        sessao = _sessao(
            status=SESSION_STATUS_REAUTH_PENDENTE,
            expires_at=datetime.now(UTC) - timedelta(hours=1),
            cookie_encrypted=None,
        )
        assert sessao.cookie_expirado() is False
