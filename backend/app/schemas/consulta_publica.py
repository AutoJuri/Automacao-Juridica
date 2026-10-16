"""Ficha pública de um CNJ que não está na carteira.

Só o que a API do DataJud devolve. Sem partes, sem advogado, sem documento.
Nada disso é gravado.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.processo import DatajudAssuntoPublicSchema

SituacaoConsultaPublica = Literal[
    "encontrado",
    "ausente",
    "indisponivel",
    "tribunal_nao_suportado",
]


class MovimentoConsultaPublicaSchema(BaseModel):
    codigo: int | None = None
    nome: str | None = None
    data_hora: datetime | None = None
    orgao_julgador: str | None = None
    complementos: list[str] = Field(default_factory=list)


class ConsultaPublicaSchema(BaseModel):
    numero: str
    tribunal: str | None
    situacao: SituacaoConsultaPublica
    classe_nome: str | None = None
    assuntos: list[DatajudAssuntoPublicSchema] = Field(default_factory=list)
    orgao_julgador: str | None = None
    data_ajuizamento: datetime | None = None
    grau: str | None = None
    formato: str | None = None
    sistema: str | None = None
    atualizado_em: datetime | None = None
    sigilo: str | None = None
    movimentos_total: int = 0
    movimentos: list[MovimentoConsultaPublicaSchema] = Field(default_factory=list)
