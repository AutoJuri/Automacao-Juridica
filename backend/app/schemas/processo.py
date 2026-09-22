"""Schemas públicos do painel de processos.

Nunca incluem `id_esaj` (intimação leva OAB) nem campos `*_encrypted`.
O id público é o UUID nosso.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    fixado: bool = False


class ProcessoFixarSchema(BaseModel):
    fixado: bool


class ProcessoFixadoSchema(BaseModel):
    id: UUID
    fixado: bool


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


class IntimacaoPainelSchema(BaseModel):
    """Intimação na lista da seção Intimações Diretas — sem `id_esaj`."""

    id: UUID
    processo_id: UUID | None = None
    nu_processo: str | None = None
    tribunal: str | None = None
    instancia: str | None = None
    titulo: str | None = None
    descricao: str | None = None
    data_movimentacao: datetime | None = None
    ciencia: bool = False
    foro: str | None = None
    vara: str | None = None


class AudienciaPainelSchema(BaseModel):
    """Audiência na lista da seção Pautas — sem `id_esaj`."""

    id: UUID
    processo_id: UUID | None = None
    nu_processo: str | None = None
    tribunal: str | None = None
    titulo: str
    data_audiencia: datetime | None = None
    local: str | None = None
    situacao: str | None = None
    parte_ativa: PartePublicSchema | None = None
    parte_passiva: PartePublicSchema | None = None
    foro: str | None = None
    vara: str | None = None
    juiz: str | None = None
    # Assunto do processo (`Processo.de_assunto`) — objeto do requerimento na pauta.
    de_assunto: str | None = None
    fonte: Literal["agenda", "cpo"] = "agenda"


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


class DatajudAssuntoPublicSchema(BaseModel):
    codigo: int | None = None
    nome: str | None = None


class DatajudMovimentoPublicSchema(BaseModel):
    codigo: int | None = None
    nome: str | None = None
    data_hora: datetime | None = None


class ProcessoDatajudPublicSchema(BaseModel):
    """Complemento somente-leitura do DataJud (Etapa 9 / ADR-015) — nunca
    sobrescreve os campos do e-SAJ, é sempre uma seção separada."""

    model_config = ConfigDict(from_attributes=True)

    classe_nome: str | None = None
    assuntos: list[DatajudAssuntoPublicSchema] = Field(default_factory=list)
    orgao_julgador: str | None = None
    data_ajuizamento: datetime | None = None
    grau: str | None = None
    formato: str | None = None
    movimentos: list[DatajudMovimentoPublicSchema] = Field(default_factory=list)
    encontrado: bool = False
    ultima_consulta_em: datetime | None = None

    @field_validator("assuntos", "movimentos", mode="before")
    @classmethod
    def _jsonb_nulo_vira_lista(cls, valor: object) -> object:
        # Job DataJud grava JSONB nulo quando não há assuntos/movimentos
        # (encontrado=false ou lista vazia persistida como None). Sem isso
        # GET /processos/{id} estoura 500 — default_factory não aplica em None explícito.
        return [] if valor is None else valor


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
    datajud: ProcessoDatajudPublicSchema | None = None
