"""ETL de normalização do payload bruto do e-SAJ para os campos dos models.

Funções puras, sem I/O — pensadas para serem testadas sem banco nem rede.
Timestamps da API chegam sem offset (ver `docs/modulos/esaj-apis.md`); o
padrão do projeto é interpretá-los como `America/Sao_Paulo` e gravar
`timestamptz`.
"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo
import hashlib

from app.schemas.esaj_cpo_raw import (
    AudienciaCpoRaw,
    CapaCpoRaw,
    MovimentacaoRaw,
    ParteCpoRaw,
    PeticaoDiversaRaw,
)
from app.schemas.esaj_raw import AudienciaRaw, IntimacaoRaw, ParteRaw, ProcessoRaw
from app.services.esaj_cpo_parser import url_cpo_publica, url_documento_publica

TIMEZONE_SP = ZoneInfo("America/Sao_Paulo")

# Colunas VARCHAR(255) em intimacoes/audiencias — corta no ETL para o
# insert não estourar (título longo no id composto de audiência).
TITULO_MAX = 255
LOCAL_MAX = 255
ID_ESAJ_MAX = 255
URL_DOCUMENTO_MAX = 2048
VALOR_ACAO_MAX = 100
CONTROLE_MAX = 50
AREA_MAX = 50
PROTOCOLO_MAX = 100
SITUACAO_MAX = 100
QT_PESSOAS_MAX = 20


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


def parse_data_movimentacao_cpo(valor: str | None) -> datetime | None:
    """Converte a data "dd/mm/aaaa" (sem hora) de `td.dataMovimentacao` do
    CPO — formato diferente do ISO sem-offset das APIs JSON de
    `tarefas-adv` (ver `parse_datetime_esaj`). Meia-noite em
    `America/Sao_Paulo`; `None` se não vier no formato esperado (nunca
    inventa uma data).
    """
    if not valor:
        return None
    try:
        dt = datetime.strptime(valor.strip(), "%d/%m/%Y")
    except ValueError:
        return None
    return dt.replace(tzinfo=TIMEZONE_SP)


def movimentacao_para_campos(raw: MovimentacaoRaw) -> dict[str, Any]:
    url = url_documento_publica(raw.url_documento)
    if url and len(url) > URL_DOCUMENTO_MAX:
        url = None
    return {
        "data_movimentacao": parse_data_movimentacao_cpo(raw.data),
        "descricao": raw.descricao,
        "titulo": _cortar(raw.titulo, TITULO_MAX),
        "tem_documento": raw.tem_documento,
        "url_documento": url,
    }


def processo_para_campos(raw: ProcessoRaw) -> dict[str, Any]:
    return {
        "cd_processo": raw.cd_processo,
        "nu_processo": raw.nu_processo,
        "de_classe": raw.de_classe,
        "de_assunto": raw.de_assunto,
        "instancia": raw.instancia,
        "parte_ativa": _parte_para_dict(raw.parte_ativa),
        "parte_passiva": _parte_para_dict(raw.parte_passiva),
        "url_cpo": url_cpo_publica(raw.url_cpo),
        "url_pasta": raw.url_pasta,
    }


def capa_cpo_para_campos(capa: CapaCpoRaw | None) -> dict[str, Any]:
    """Só campos que o JSON de processos não traz. Não inclui classe/assunto."""
    if capa is None:
        return {}
    return {
        "foro": _cortar(capa.foro, TITULO_MAX),
        "vara": _cortar(capa.vara, TITULO_MAX),
        "juiz": _cortar(capa.juiz, TITULO_MAX),
        "distribuicao": _cortar(capa.distribuicao, TITULO_MAX),
        "controle": _cortar(capa.controle, CONTROLE_MAX),
        "area": _cortar(capa.area, AREA_MAX),
        "valor_acao": _cortar(capa.valor_acao, VALOR_ACAO_MAX),
    }


def partes_cpo_para_json(partes: list[ParteCpoRaw]) -> list[dict[str, Any]]:
    return [parte.model_dump() for parte in partes]


def _hash_identidade(chave: str) -> str:
    return hashlib.sha256(chave.encode("utf-8")).hexdigest()


def peticao_identidade_hash(raw: PeticaoDiversaRaw) -> str:
    if raw.protocolo:
        return _hash_identidade(f"p|{raw.protocolo.strip()}")
    return _hash_identidade(f"d|{raw.data}|{raw.tipo}|{raw.texto_extra}")


def peticao_para_campos(raw: PeticaoDiversaRaw) -> dict[str, Any]:
    return {
        "data_peticao": parse_data_movimentacao_cpo(raw.data),
        "tipo": _cortar(raw.tipo, TITULO_MAX) or "",
        "protocolo": _cortar(raw.protocolo, PROTOCOLO_MAX),
        "identidade_hash": peticao_identidade_hash(raw),
    }


def audiencia_cpo_identidade_hash(raw: AudienciaCpoRaw) -> str:
    return _hash_identidade(
        f"{raw.data}|{raw.titulo}|{raw.situacao or ''}|{raw.qt_pessoas or ''}"
    )


def audiencia_cpo_para_campos(raw: AudienciaCpoRaw) -> dict[str, Any]:
    return {
        "data_audiencia": parse_data_movimentacao_cpo(raw.data),
        "titulo": _cortar(raw.titulo, TITULO_MAX) or "",
        "situacao": _cortar(raw.situacao, SITUACAO_MAX),
        "qt_pessoas": _cortar(raw.qt_pessoas, QT_PESSOAS_MAX),
        "identidade_hash": audiencia_cpo_identidade_hash(raw),
    }
