"""Capa da elaboração e respostas da IA.

A capa não leva credencial. A minuta gerada sai só decriptada, nos schemas
da IA — nunca os campos `*_encrypted`.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.elaboracao import PECAS
from app.schemas.processo import UltimaAtividadeSchema


def _vazio(valor: str | None) -> str | None:
    if valor is None:
        return None
    texto = valor.strip()
    return texto or None


class ElaboracaoManualSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    titulo: str = Field(min_length=1, max_length=120)
    nu_processo: str | None = Field(default=None, max_length=50)
    parte_ativa: str | None = Field(default=None, max_length=255)
    parte_passiva: str | None = Field(default=None, max_length=255)
    classe: str | None = Field(default=None, max_length=255)
    assunto: str | None = Field(default=None, max_length=255)
    foro_vara: str | None = Field(default=None, max_length=255)
    valor_causa: str | None = Field(default=None, max_length=100)
    juiz: str | None = Field(default=None, max_length=255)

    @field_validator(
        "nu_processo",
        "parte_ativa",
        "parte_passiva",
        "classe",
        "assunto",
        "foro_vara",
        "valor_causa",
        "juiz",
    )
    @classmethod
    def _opcional(cls, valor: str | None) -> str | None:
        return _vazio(valor)


class ElaboracaoCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    peca: str = Field(min_length=1, max_length=100)
    processo_id: UUID | None = None
    manual: ElaboracaoManualSchema | None = None

    @model_validator(mode="after")
    def _um_ou_outro(self) -> "ElaboracaoCreateSchema":
        if self.peca not in PECAS:
            raise ValueError("Peça desconhecida")
        tem_processo = self.processo_id is not None
        tem_manual = self.manual is not None
        if tem_processo == tem_manual:
            raise ValueError("Informe o processo ou os dados manuais, não os dois")
        return self


class ElaboracaoUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    peca: str | None = Field(default=None, min_length=1, max_length=100)
    manual: ElaboracaoManualSchema | None = None

    @model_validator(mode="after")
    def _peca_conhecida(self) -> "ElaboracaoUpdateSchema":
        if self.peca is not None and self.peca not in PECAS:
            raise ValueError("Peça desconhecida")
        return self


class ElaboracaoCardSchema(BaseModel):
    id: UUID
    peca: str
    rotulo: str
    titulo: str | None
    nu_processo: str | None
    autor: str | None
    reu: str | None
    tem_processo: bool
    updated_at: datetime


class ElaboracaoDetalheSchema(ElaboracaoCardSchema):
    processo_id: UUID | None
    manual: ElaboracaoManualSchema | None


class ProcessoParaIniciarSchema(BaseModel):
    id: UUID
    nu_processo: str | None
    tribunal: str
    classe: str | None
    autor: str | None
    reu: str | None
    ultima_atividade: UltimaAtividadeSchema | None


class PaginaProcessosParaIniciarSchema(BaseModel):
    items: list[ProcessoParaIniciarSchema]
    total: int


FATOS_EXTRAS_MAX = 8000
INSTRUCAO_MAX = 4000
TRECHO_SELECIONADO_MAX = 4000
ESTILO_TEXTO_MAX = 50_000


class FatosExtrasUpdateSchema(BaseModel):
    fatos_extras: str | None = Field(default=None, max_length=FATOS_EXTRAS_MAX)


class EditarMinutaSchema(BaseModel):
    instrucao: str = Field(min_length=1, max_length=INSTRUCAO_MAX)
    trecho_selecionado: str | None = Field(default=None, max_length=TRECHO_SELECIONADO_MAX)


class EstiloTextoSchema(BaseModel):
    texto: str = Field(min_length=1, max_length=ESTILO_TEXTO_MAX)


class ElaboracaoPublicSchema(BaseModel):
    id: UUID
    processo_id: UUID | None
    peca: str
    fatos_extras: str | None = None
    estilo_perfil: str | None = None
    created_at: datetime
    updated_at: datetime


class SugestaoPecaSchema(BaseModel):
    peca: str | None = None
    explicacao: str | None = None


class VersaoMinutaPublicSchema(BaseModel):
    id: UUID
    origem: Literal["geracao", "chat", "grifo"]
    instrucao: str | None = None
    trecho_selecionado: str | None = None
    conteudo_html: str
    llm_provider: str
    llm_model: str | None = None
    criado_em: datetime
