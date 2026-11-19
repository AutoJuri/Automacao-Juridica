"""Resposta da leitura dos autos. Sem URL, sem ficha crua, sem PDF."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentoDossieSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    movimentacao_id: UUID
    titulo: str | None = None
    data: datetime | None = None
    status: str


class RoteiroSchema(BaseModel):
    """O que o advogado confirma antes da minuta. Sem URL e sem PDF."""

    model_config = ConfigDict(extra="ignore")

    resumo: str = Field(default="", max_length=4000)
    tese: str = Field(default="", max_length=4000)
    pedidos: str = Field(default="", max_length=4000)
    acrescentar: str = Field(default="", max_length=4000)
    nao_incluir: str = Field(default="", max_length=4000)
    jurisprudencia: str = Field(default="", max_length=4000)


class DossiePublicSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    processo_id: UUID
    status: str
    lidos: int
    total: int
    gerado_em: datetime | None = None
    retomar_apos: datetime | None = None
    resumo: str | None = None
    roteiro: RoteiroSchema = Field(default_factory=RoteiroSchema)
    documentos: list[DocumentoDossieSchema]
