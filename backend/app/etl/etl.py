"""ETL de normalização do payload bruto do e-SAJ para os campos dos models.

Funções puras, sem I/O — pensadas para serem testadas sem banco nem rede.
Timestamps da API chegam sem offset (ver `docs/modulos/esaj-apis.md`); o
padrão do projeto é interpretá-los como `America/Sao_Paulo` e gravar
`timestamptz`.
"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.schemas.esaj_raw import AudienciaRaw, IntimacaoRaw, ParteRaw, ProcessoRaw

TIMEZONE_SP = ZoneInfo("America/Sao_Paulo")

# Colunas VARCHAR(255) em intimacoes/audiencias — corta no ETL para o
# insert não estourar (título longo no id composto de audiência).
TITULO_MAX = 255
LOCAL_MAX = 255
ID_ESAJ_MAX = 255


def _cortar(valor: str | None, maximo: int) -> str | None:
    if valor is None:
        return None
    return valor[:maximo]


def parse_datetime_esaj(valor: str | None) -> datetime | None:
    """Converte a string ISO (sem offset) do e-SAJ num `datetime` aware.

    Se a string já vier com offset (não observado nas capturas, mas
    defensivo), preserva o offset em vez de sobrescrever.
    """
    if not valor:
        return None
    dt = datetime.fromisoformat(valor)
    if dt.tzinfo is not None:
        return dt
    return dt.replace(tzinfo=TIMEZONE_SP)


def montar_id_esaj_audiencia(
    cd_processo: str, data_audiencia: datetime | None, titulo: str | None
) -> str:
    """Id canônico estável para `audiencias.id_esaj` (ADR-010).

    A API não devolve `id` para audiências — sem essa chave composta, cada
    poll criaria um evento "novo" idêntico ao anterior. Se o composto
    passar de 255, trunca só o título (o prefixo `cdProcesso|dataAudiencia`
    permanece estável).
    """
    data_iso = data_audiencia.isoformat() if data_audiencia is not None else ""
    prefixo = f"cdProcesso={cd_processo}|dataAudiencia={data_iso}|titulo="
    restante = max(ID_ESAJ_MAX - len(prefixo), 0)
    return f"{prefixo}{(titulo or '')[:restante]}"[:ID_ESAJ_MAX]


def intimacao_para_campos(raw: IntimacaoRaw) -> dict[str, Any]:
    return {
        "id_esaj": raw.id[:ID_ESAJ_MAX],
        "titulo": _cortar(raw.titulo, TITULO_MAX),
        "descricao": raw.descricao,
        "instancia": raw.instancia,
        "data_movimentacao": parse_datetime_esaj(raw.data_movimentacao),
        "ciencia": raw.ciencia,
    }


def audiencia_para_campos(raw: AudienciaRaw, id_esaj: str) -> dict[str, Any]:
    return {
        "id_esaj": id_esaj[:ID_ESAJ_MAX],
        "titulo": _cortar(raw.titulo, TITULO_MAX),
        "data_audiencia": parse_datetime_esaj(raw.data_audiencia),
        "local": _cortar(raw.local, LOCAL_MAX),
    }


def _parte_para_dict(parte: ParteRaw | None) -> dict[str, Any] | None:
    if parte is None:
        return None
    return parte.model_dump(by_alias=True)


def processo_para_campos(raw: ProcessoRaw) -> dict[str, Any]:
    return {
        "cd_processo": raw.cd_processo,
        "nu_processo": raw.nu_processo,
        "de_classe": raw.de_classe,
        "de_assunto": raw.de_assunto,
        "instancia": raw.instancia,
        "parte_ativa": _parte_para_dict(raw.parte_ativa),
        "parte_passiva": _parte_para_dict(raw.parte_passiva),
        "url_cpo": raw.url_cpo,
        "url_pasta": raw.url_pasta,
    }
