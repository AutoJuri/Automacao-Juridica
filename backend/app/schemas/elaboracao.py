"""Schemas da IA da elaboração (ADR-016).

Nenhum schema de resposta expõe `fatos_extras_encrypted`,
`instrucao_encrypted`, `trecho_alvo_encrypted` ou `conteudo_encrypted` —
os campos públicos decriptam em memória, no serviço, e devolvem texto
puro só para o próprio dono (o mesmo usuário que escreveu o dado).
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.services.elaboracao_pecas import PECAS_IDS_VALIDOS

FATOS_EXTRAS_MAX = 8000
INSTRUCAO_MAX = 4000
TRECHO_SELECIONADO_MAX = 4000
PECA_MAX = 100
# Cabe um modelo de peça inteiro colado/lido de TXT (ADR-016 Fase 3).
ESTILO_TEXTO_MAX = 50_000


class ElaboracaoCreateSchema(BaseModel):
    processo_id: UUID
    peca: str = Field(min_length=1, max_length=PECA_MAX)

    @field_validator("peca")
    @classmethod
    def peca_do_catalogo(cls, valor: str) -> str:
        if valor not in PECAS_IDS_VALIDOS:
            raise ValueError("Peça fora do catálogo.")
        return valor


class FatosExtrasUpdateSchema(BaseModel):
    # None/"" apaga o campo — o advogado pode limpar o que escreveu.
    fatos_extras: str | None = Field(default=None, max_length=FATOS_EXTRAS_MAX)


class EditarMinutaSchema(BaseModel):
    instrucao: str = Field(min_length=1, max_length=INSTRUCAO_MAX)
    # Presente = edição de grifo (trecho específico); ausente = chat (documento todo).
    trecho_selecionado: str | None = Field(default=None, max_length=TRECHO_SELECIONADO_MAX)


class EstiloTextoSchema(BaseModel):
    """Texto de um modelo de peça (TXT já lido no browser, ou colado)
    (ADR-016 Fase 3). PDF/DOCX ainda não têm extração — ficam só anexados."""

    texto: str = Field(min_length=1, max_length=ESTILO_TEXTO_MAX)


class ElaboracaoPublicSchema(BaseModel):
    id: UUID
    processo_id: UUID
    peca: str
    fatos_extras: str | None = None
    # JSON (string) do perfil de estilo extraído do último modelo enviado
    # (ADR-016 Fase 3) — `None` até o advogado aplicar um modelo.
    estilo_perfil: str | None = None
    created_at: datetime
    updated_at: datetime


class SugestaoPecaSchema(BaseModel):
    """Resposta de `GET /elaboracoes/sugestao-peca` (ADR-016 Fase 1).

    `peca=None` = sem sinal suficiente; o select do frontend continua livre
    e cai no valor padrão."""

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
