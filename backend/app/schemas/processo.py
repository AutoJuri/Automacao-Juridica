"""Schemas públicos do painel de processos.

Nunca incluem `id_esaj` (intimação leva OAB) nem campos `*_encrypted`.
O id público é o UUID nosso.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PartePublicSchema(BaseModel):
    nome: str | None = None
    representada: bool | None = None


class UltimaAtividadeSchema(BaseModel):
    tipo: Literal["intimacao", "audiencia"]
    titulo: str | None = None
    data: datetime | None = None


class ProcessoListSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tribunal: str
    nu_processo: str | None = None
    de_classe: str | None = None
    de_assunto: str | None = None
    instancia: str | None = None
    parte_ativa: PartePublicSchema | None = None
    parte_passiva: PartePublicSchema | None = None
    last_synced_at: datetime | None = None
    ultima_atividade: UltimaAtividadeSchema | None = None


class IntimacaoPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str | None = None
    descricao: str | None = None
    instancia: str | None = None
    data_movimentacao: datetime | None = None
    ciencia: bool = False


class AudienciaPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str | None = None
    data_audiencia: datetime | None = None
    local: str | None = None


class MovimentacaoPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str | None = None
    descricao: str
    data_movimentacao: datetime | None = None
    tem_documento: bool = False
    # Só https://esaj.tjsp.jus.br/cpopg/abrirDocumentoVinculadoMovimentacao.do
    # — nunca hash de senha dos autos, nunca cookie.
    url_documento: str | None = None


class ParteCpoPublicSchema(BaseModel):
    papel: str
    nome: str | None = None
    advogados: str | None = None


class PeticaoDiversaPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    data_peticao: datetime | None = None
    tipo: str
    protocolo: str | None = None


class AudienciaCpoPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    data_audiencia: datetime | None = None
    titulo: str
    situacao: str | None = None
    qt_pessoas: str | None = None


# `ok` = já há andamentos; `pendente` = o throttle ainda não buscou o CPO;
# `indisponivel` = o CPO foi buscado mas a tabela de movimentações não veio
# (segredo de justiça / sem vínculo pleno — nunca pedimos senha dos autos).
MovimentacoesStatus = Literal["ok", "pendente", "indisponivel"]


class ProcessoDetalheSchema(ProcessoListSchema):
    url_cpo: str | None = None
    url_pasta: str | None = None
    foro: str | None = None
    vara: str | None = None
    juiz: str | None = None
    distribuicao: str | None = None
    controle: str | None = None
    area: str | None = None
    valor_acao: str | None = None
    partes_cpo: list[ParteCpoPublicSchema] = Field(default_factory=list)
    intimacoes: list[IntimacaoPublicSchema] = Field(default_factory=list)
    audiencias: list[AudienciaPublicSchema] = Field(default_factory=list)
    movimentacoes: list[MovimentacaoPublicSchema] = Field(default_factory=list)
    peticoes_diversas: list[PeticaoDiversaPublicSchema] = Field(default_factory=list)
    audiencias_cpo: list[AudienciaCpoPublicSchema] = Field(default_factory=list)
    movimentacoes_status: MovimentacoesStatus = "pendente"
    sem_incidentes: bool | None = None
    sem_apensos: bool | None = None
