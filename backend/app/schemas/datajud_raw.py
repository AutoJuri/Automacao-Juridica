"""Schema Pydantic do `_source` de um hit da API pública do DataJud (CNJ).

Contrato documentado no tutorial oficial do CNJ (ver `docs/modulos/datajud.md`).
`extra="ignore"` — a API pode devolver outros campos (ex.: `@timestamp`,
`dataHoraUltimaAtualizacao`, `tribunal`, `id`) que o MVP não usa. A API
pública **não** inclui partes nem advogados/OAB (Portaria CNJ 160/2020) —
nunca vai aparecer esse dado aqui.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DatajudClasseRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")

    codigo: int | None = None
    nome: str | None = None


class DatajudAssuntoRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")

    codigo: int | None = None
    nome: str | None = None


class DatajudOrgaoJulgadorRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str | None = None


class DatajudFormatoRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str | None = None


class DatajudMovimentoRaw(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    codigo: int | None = None
    nome: str | None = None
    data_hora: datetime | None = Field(default=None, alias="dataHora")


class DatajudProcessoRaw(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    numero_processo: str | None = Field(default=None, alias="numeroProcesso")
    classe: DatajudClasseRaw | None = None
    assuntos: list[DatajudAssuntoRaw] = Field(default_factory=list)
    orgao_julgador: DatajudOrgaoJulgadorRaw | None = Field(default=None, alias="orgaoJulgador")
    data_ajuizamento: datetime | None = Field(default=None, alias="dataAjuizamento")
    grau: str | None = None
    formato: DatajudFormatoRaw | None = None
    movimentos: list[DatajudMovimentoRaw] = Field(default_factory=list)
