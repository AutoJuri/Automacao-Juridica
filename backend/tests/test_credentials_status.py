"""GET /credentials/status — `validacao_em_andamento` distinto de `reauth_pendente`."""

from types import SimpleNamespace
from uuid import uuid4

from app.api.credentials import _status_apos_disparo, _status_schema
from app.models.tribunal import SESSION_STATUS_REAUTH_PENDENTE
from app.services import credential_validation


def _credencial(user_id=None):
    return SimpleNamespace(
        user_id=user_id or uuid4(),
        tribunal="esaj_tjsp",
        cpf_mascarado="***.456.789-**",
        email_provider="outlook",
        email_oauth_token_encrypted=b"blob",
        last_validated_at=None,
        is_active=True,
    )


def _sessao(status=SESSION_STATUS_REAUTH_PENDENTE):
    return SimpleNamespace(status=status, cookie_expirado=lambda: False)


class TestStatusSchemaValidacaoEmAndamento:
    def test_reauth_pendente_sem_playwright_nao_e_validacao_em_andamento(self):
        schema = _status_schema(_credencial(), _sessao())

        assert schema.session_status == SESSION_STATUS_REAUTH_PENDENTE
        assert schema.validacao_em_andamento is False

    def test_reflete_o_set_em_memoria(self, monkeypatch):
        user_id = uuid4()
        monkeypatch.setattr(
            credential_validation, "_VALIDACOES_EM_ANDAMENTO", {user_id}
        )

        schema = _status_schema(_credencial(user_id), _sessao())

        assert schema.validacao_em_andamento is True

    def test_sem_credencial_nao_expoe_validacao(self):
        schema = _status_schema(None)

        assert schema.cadastrado is False
        assert schema.validacao_em_andamento is False

    def test_resposta_apos_disparo_marca_validacao_mesmo_sem_set(self):
        schema = _status_apos_disparo(_credencial(), _sessao())

        assert schema.validacao_em_andamento is True
        assert schema.session_status == SESSION_STATUS_REAUTH_PENDENTE
