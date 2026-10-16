"""Slug, matriz de papéis e log do convite — sem banco."""

import logging
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.permissions import ACOES_POR_PAPEL, papel_autorizado
from app.models.organization import (
    ROLE_ADMIN,
    ROLE_ADVOGADO,
    ROLE_ASSISTENTE,
    ROLE_ESTAGIARIO,
    ROLE_OWNER,
)
from app.schemas.organization import InviteCreateSchema, OrganizationCreateSchema
from app.services.organizations import registrar_link_convite, slugificar


class TestSlug:
    def test_remove_acento_e_simbolo(self):
        assert slugificar("Silva & Associados") == "silva-associados"
        assert slugificar("Ação Jurídica") == "acao-juridica"

    def test_nome_sem_letra_cai_no_fallback(self):
        assert slugificar("!!!") == "organizacao"


class TestMatrizDePapeis:
    def test_owner_e_admin_convidam_advogado_nao(self):
        assert papel_autorizado(ROLE_OWNER, "convidar")
        assert papel_autorizado(ROLE_ADMIN, "convidar")
        assert not papel_autorizado(ROLE_ADVOGADO, "convidar")
        assert not papel_autorizado(ROLE_ASSISTENTE, "convidar")
        assert not papel_autorizado(ROLE_ESTAGIARIO, "convidar")

    def test_so_owner_exclui_e_transfere(self):
        for acao in ("excluir_organizacao", "transferir_ownership"):
            assert papel_autorizado(ROLE_OWNER, acao)
            assert not papel_autorizado(ROLE_ADMIN, acao)
            assert not papel_autorizado(ROLE_ADVOGADO, acao)
            assert not papel_autorizado(ROLE_ESTAGIARIO, acao)

    def test_conjuntos_nao_incluem_papel_desconhecido(self):
        for papeis in ACOES_POR_PAPEL.values():
            assert "desconhecido" not in papeis


class TestLogDoConvite:
    def test_development_loga_o_link(self, monkeypatch, caplog):
        class Ambiente:
            is_development = True
            frontend_url = "http://localhost:3000"

        monkeypatch.setattr("app.services.organizations.get_settings", lambda: Ambiente())
        token = "11111111-1111-4111-8111-111111111111"
        with caplog.at_level(logging.WARNING):
            registrar_link_convite(uuid4(), token)

        assert f"http://localhost:3000/convite/{token}" in caplog.text

    def test_fora_de_development_nao_loga_o_token(self, monkeypatch, caplog):
        class Ambiente:
            is_development = False
            frontend_url = "https://app.exemplo.com"

        monkeypatch.setattr("app.services.organizations.get_settings", lambda: Ambiente())
        token = "22222222-2222-4222-8222-222222222222"
        with caplog.at_level(logging.INFO):
            registrar_link_convite(uuid4(), token)

        assert token not in caplog.text
        assert "convite/" not in caplog.text
        assert "@" not in caplog.text


class TestSchemaRecusaCampoExtra:
    def test_criar_organizacao_e_convite_recusam_campo_desconhecido(self):
        with pytest.raises(ValidationError):
            OrganizationCreateSchema.model_validate({"name": "Escritorio Silva", "token": "x"})
        with pytest.raises(ValidationError):
            InviteCreateSchema.model_validate(
                {"email": "ana@example.com", "role": "advogado", "user_id": str(uuid4())}
            )

    def test_convite_aceita_estagiario_e_recusa_owner(self):
        convite = InviteCreateSchema.model_validate(
            {"email": "ana@example.com", "role": "estagiario"}
        )
        assert convite.role == "estagiario"
        with pytest.raises(ValidationError):
            InviteCreateSchema.model_validate({"email": "ana@example.com", "role": "owner"})
