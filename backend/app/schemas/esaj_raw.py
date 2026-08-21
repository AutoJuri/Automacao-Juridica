"""Schemas Pydantic do payload bruto das APIs internas do e-SAJ.

Contrato observado em `docs/modulos/esaj-apis.md`. `extra="ignore"` porque
o e-SAJ pode devolver campos que o MVP não usa — nunca falhar a validação
por causa de um campo extra que a gente simplesmente descarta.
"""

from pydantic import BaseModel, ConfigDict, Field


class ParteRaw(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    nome: str | None = None
    nome_social: str | None = Field(default=None, alias="nomeSocial")
    representada: bool | None = None


class IntimacaoRaw(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    # Composto pela API (contém OAB) — nunca logar.
    id: str
    titulo: str | None = None
    descricao: str | None = None
    cd_processo: str = Field(alias="cdProcesso")
    instancia: str | None = None
    # String crua sem timezone — parseada pelo ETL.
    data_movimentacao: str | None = Field(default=None, alias="dataMovimentacao")
    ciencia: bool = False


class AudienciaRaw(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    # `situacao` e `dataMovimentacao` não persistem no MVP (ADR-010) — nem
    # entram neste schema.
    data_audiencia: str | None = Field(default=None, alias="dataAudiencia")
    titulo: str | None = None
    local: str | None = None
    cd_processo: str = Field(alias="cdProcesso")


class ProcessoRaw(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    cd_processo: str = Field(alias="cdProcesso")
    nu_processo: str | None = Field(default=None, alias="nuProcesso")
    de_classe: str | None = Field(default=None, alias="deClasse")
    de_assunto: str | None = Field(default=None, alias="deAssunto")
    instancia: str | None = None
    parte_ativa: ParteRaw | None = Field(default=None, alias="parteAtiva")
    parte_passiva: ParteRaw | None = Field(default=None, alias="partePassiva")
    url_cpo: str | None = Field(default=None, alias="urlCpo")
    url_pasta: str | None = Field(default=None, alias="urlPasta")
