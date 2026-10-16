"""Pastas do Drive. Nenhum id do Google, token ou byte de arquivo entra aqui."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _nome_valido(valor: str) -> str:
    nome = valor.strip()
    if not nome:
        raise ValueError("Informe o nome da pasta")
    if any(ord(caractere) < 32 for caractere in nome):
        raise ValueError("O nome da pasta tem caracteres inválidos")
    return nome


class PastaCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(min_length=1, max_length=120)
    processo_id: UUID | None = None

    @field_validator("nome")
    @classmethod
    def _nome(cls, valor: str) -> str:
        return _nome_valido(valor)


class PastaUpdateSchema(BaseModel):
    """Campos ausentes ficam como estão. `processo_id: null` solta o vínculo."""

    model_config = ConfigDict(extra="forbid")

    nome: str | None = Field(default=None, min_length=1, max_length=120)
    processo_id: UUID | None = None

    @field_validator("nome")
    @classmethod
    def _nome(cls, valor: str | None) -> str | None:
        return None if valor is None else _nome_valido(valor)

    @model_validator(mode="after")
    def _nome_nao_nulo(self) -> "PastaUpdateSchema":
        if "nome" in self.model_fields_set and self.nome is None:
            raise ValueError("Informe o nome da pasta")
        return self


class PastaProcessoSchema(BaseModel):
    id: UUID
    nu_processo: str | None
    autor: str | None
    reu: str | None


class PastaSchema(BaseModel):
    id: UUID
    nome: str
    processo: PastaProcessoSchema | None
    total_arquivos: int
    updated_at: datetime


# --- Google Drive -----------------------------------------------------------
# Nenhum token, e-mail da conta ou id interno do Google sai por aqui. O link
# do arquivo no Drive é montado a partir do id e não carrega segredo.


class DriveStatusSchema(BaseModel):
    configurado: bool
    picker_configurado: bool
    conectado: bool


class PickerTokenSchema(BaseModel):
    """Token curto só para o seletor do Google (exceção da ADR-022)."""

    access_token: str
    expires_in: int
    api_key: str
    app_id: str


class ArquivoSchema(BaseModel):
    id: UUID
    pasta_id: UUID
    nome: str
    mime_type: str
    tamanho: int | None
    origem: str
    ausente_no_google: bool
    url_drive: str
    created_at: datetime


class VincularArquivoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    google_file_id: str = Field(pattern=r"^[A-Za-z0-9_-]{10,100}$")


class MoverArquivoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pasta_id: UUID
