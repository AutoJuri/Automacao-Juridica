"""Schema Pydantic do `_source` de um hit da API pública do DataJud (CNJ).

Contrato documentado no tutorial oficial do CNJ (ver `docs/modulos/datajud.md`).
`extra="ignore"` — a API devolve também `@timestamp`, `id` e códigos internos
que a ficha não mostra. A API pública não inclui partes nem advogados/OAB
(Portaria CNJ 160/2020).
"""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator


def interpretar_data_datajud(valor: object) -> object:
    """O CNJ manda o ajuizamento como `AAAAMMDDhhmmss`, sem separadores.

    O leitor padrão trata esse texto como timestamp Unix e gera um ano
    absurdo (ex.: 2611). Os 14 dígitos viram data em UTC: no mesmo
    processo, o movimento seguinte vem com `Z` poucos minutos depois.
    A tela converte para Brasília. ISO continua para o leitor padrão.
    """
    if not isinstance(valor, str):
        return valor
    texto = valor.strip()
    if len(texto) == 14 and texto.isdigit():
        return datetime.strptime(texto, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
    return valor


def interpretar_nivel_sigilo(valor: object) -> object:
    if valor is None or valor == "" or valor == "None":
        return None
    return valor


DatajudInstante = Annotated[datetime | None, BeforeValidator(interpretar_data_datajud)]
NivelSigilo = Annotated[int | None, BeforeValidator(interpretar_nivel_sigilo)]


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


class DatajudComplementoRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str | None = None
    descricao: str | None = None


class DatajudMovimentoRaw(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    codigo: int | None = None
    nome: str | None = None
    data_hora: DatajudInstante = Field(default=None, alias="dataHora")
    orgao_julgador: DatajudOrgaoJulgadorRaw | None = Field(default=None, alias="orgaoJulgador")
    complementos_tabelados: list[DatajudComplementoRaw] = Field(
        default_factory=list, alias="complementosTabelados"
    )

    @field_validator("complementos_tabelados", mode="before")
    @classmethod
    def _complementos_nulos(cls, valor: object) -> object:
        return [] if valor is None else valor


class DatajudProcessoRaw(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    numero_processo: str | None = Field(default=None, alias="numeroProcesso")
    classe: DatajudClasseRaw | None = None
    assuntos: list[DatajudAssuntoRaw] = Field(default_factory=list)
    orgao_julgador: DatajudOrgaoJulgadorRaw | None = Field(default=None, alias="orgaoJulgador")
    data_ajuizamento: DatajudInstante = Field(default=None, alias="dataAjuizamento")
    grau: str | None = None
    formato: DatajudFormatoRaw | None = None
    sistema: DatajudFormatoRaw | None = None
    data_hora_ultima_atualizacao: DatajudInstante = Field(
        default=None, alias="dataHoraUltimaAtualizacao"
    )
    nivel_sigilo: NivelSigilo = Field(default=None, alias="nivelSigilo")
    movimentos: list[DatajudMovimentoRaw] = Field(default_factory=list)
