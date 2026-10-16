"""Validação da capa de elaboração — sem banco."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.elaboracao import ElaboracaoCreateSchema, ElaboracaoUpdateSchema


def _manual() -> dict:
    return {"titulo": "Peça de teste"}


class TestCriarElaboracao:
    def test_processo_e_manual_juntos_recusa(self):
        with pytest.raises(ValidationError):
            ElaboracaoCreateSchema.model_validate(
                {"peca": "contestacao", "processo_id": str(uuid4()), "manual": _manual()}
            )

    def test_sem_origem_recusa(self):
        with pytest.raises(ValidationError):
            ElaboracaoCreateSchema.model_validate({"peca": "contestacao"})

    def test_peca_desconhecida_recusa(self):
        with pytest.raises(ValidationError):
            ElaboracaoCreateSchema.model_validate({"peca": "habeas", "manual": _manual()})

    def test_campo_extra_recusa(self):
        with pytest.raises(ValidationError):
            ElaboracaoCreateSchema.model_validate(
                {"peca": "contestacao", "manual": _manual(), "user_id": str(uuid4())}
            )

    def test_manual_sem_titulo_recusa(self):
        with pytest.raises(ValidationError):
            ElaboracaoCreateSchema.model_validate(
                {"peca": "contestacao", "manual": {"titulo": "  "}}
            )

    def test_manual_aceito(self):
        dados = ElaboracaoCreateSchema.model_validate(
            {"peca": "contestacao", "manual": {"titulo": " Teste ", "nu_processo": "  "}}
        )
        assert dados.manual is not None
        assert dados.manual.titulo == "Teste"
        assert dados.manual.nu_processo is None


class TestAtualizarElaboracao:
    def test_peca_desconhecida_recusa(self):
        with pytest.raises(ValidationError):
            ElaboracaoUpdateSchema.model_validate({"peca": "habeas"})

    def test_corpo_vazio_e_toque(self):
        dados = ElaboracaoUpdateSchema.model_validate({})
        assert dados.peca is None
        assert dados.manual is None
