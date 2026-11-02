"""Decisão por documento, sem banco e sem rede.

Quem grava a ficha é `app.services.dossie`. Aqui só sai o que aconteceu
com um arquivo: status, texto curto e se o lote precisa parar.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.models.processo_documento import (
    STATUS_DOC_ERRO,
    STATUS_DOC_ILEGIVEL,
    STATUS_DOC_LIDO,
    STATUS_DOC_PARCIAL,
    STATUS_DOC_PENDENTE,
    STATUS_DOC_SEM_ACESSO,
)
from app.services.dossie_prompt import (
    dividir_blocos,
    hash_url,
    juntar_fichas_parciais,
    reaproveitar,
)
from app.services.esaj_documentos import EsajDocumentoGrandeError, EsajDocumentoNaoPdfError
from app.services.esaj_http import (
    EsajPortalIndisponivelError,
    EsajRateLimitError,
    EsajSessaoInvalidaError,
)
from app.services.llm.base import LLMAutenticacaoError, LLMLimiteAtingidoError
from app.services.pdf_texto import PdfIlegivelError

logger = logging.getLogger(__name__)

MAX_DOCUMENTOS_POR_LEITURA = 40
MAX_LINHA_TEMPO = 40
PAUSA_ENTRE_DOCUMENTOS_SEGUNDOS = 1.0
_SP = ZoneInfo("America/Sao_Paulo")

BaixarFn = Callable[[str], Awaitable[bytes]]
ExtrairFn = Callable[[bytes], Awaitable[object]]
ResumirFn = Callable[[str, str | None, str | None], Awaitable[str]]


@dataclass(frozen=True, slots=True)
class ResultadoDocumento:
    status: str
    ficha: str | None = None
    paginas: int | None = None
    paginas_ocr: int | None = None
    url_hash: str | None = None
    baixou: bool = False
    parar: str | None = None


def data_curta(valor: datetime | None) -> str | None:
    if valor is None:
        return None
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=UTC)
    return valor.astimezone(_SP).strftime("%d/%m/%Y")


def frase_movimentacao(titulo: str | None, descricao: str) -> str:
    base = (titulo or "").strip()
    if not base:
        base = (descricao or "").strip().split("\n", 1)[0].strip()
    base = base.split("http")[0].strip()
    if len(base) > 180:
        base = base[:179].rstrip() + "…"
    return base or "movimentação sem descrição"


def linha_do_tempo_curta(
    itens: list[tuple[datetime | None, str | None, str]],
) -> tuple[str, ...]:
    """No máximo 40 linhas, da mais antiga à mais nova, entre as mais recentes."""
    com_data = [item for item in itens if item[0] is not None]
    sem_data = [item for item in itens if item[0] is None]
    com_data.sort(key=lambda item: item[0] or datetime.min.replace(tzinfo=UTC))
    escolhidos = (com_data + sem_data)[-MAX_LINHA_TEMPO:]
    linhas: list[str] = []
    for quando, titulo, descricao in escolhidos:
        dia = data_curta(quando) or "sem data"
        linhas.append(f"{dia} — {frase_movimentacao(titulo, descricao)}")
    return tuple(linhas)


def _texto_paginas(extracao: object) -> tuple[str, int, int, bool]:
    paginas = getattr(extracao, "paginas", ())
    parcial = bool(getattr(extracao, "parcial", False))
    pedacos: list[str] = []
    ocr = 0
    for pagina in paginas:
        if getattr(pagina, "usou_ocr", False):
            ocr += 1
        texto = (getattr(pagina, "texto", "") or "").strip()
        if texto:
            pedacos.append(texto)
    return "\n\n".join(pedacos), len(tuple(paginas)), ocr, parcial


async def resumir_em_blocos(
    resumir: ResumirFn,
    texto: str,
    *,
    titulo: str | None,
    data: str | None,
) -> str:
    blocos = dividir_blocos(texto)
    if not blocos:
        return ""
    fichas: list[str] = []
    for indice, bloco in enumerate(blocos, start=1):
        titulo_bloco = titulo
        if len(blocos) > 1:
            titulo_bloco = f"{titulo or 'Documento'} (parte {indice} de {len(blocos)})"
        fichas.append(await resumir(bloco, titulo_bloco, data))
    return juntar_fichas_parciais(fichas)


async def classificar_documento(
    *,
    url: str | None,
    titulo: str | None,
    data: str | None,
    status_anterior: str | None,
    url_hash_anterior: str | None,
    baixar: BaixarFn,
    extrair: ExtrairFn,
    resumir: ResumirFn,
) -> ResultadoDocumento:
    """Um documento. Falha daqui não decide os outros, salvo `parar`."""
    if not url:
        return ResultadoDocumento(status=STATUS_DOC_SEM_ACESSO)

    atual = hash_url(url)
    if reaproveitar(status_anterior, url_hash_anterior, atual):
        return ResultadoDocumento(status=status_anterior or STATUS_DOC_PENDENTE, url_hash=atual)

    try:
        pdf = await baixar(url)
    except EsajSessaoInvalidaError:
        return ResultadoDocumento(status=STATUS_DOC_PENDENTE, parar="sessao_expirada", baixou=True)
    except EsajRateLimitError:
        return ResultadoDocumento(status=STATUS_DOC_PENDENTE, parar="bloqueado", baixou=True)
    except EsajDocumentoGrandeError:
        return ResultadoDocumento(status=STATUS_DOC_ILEGIVEL, url_hash=atual, baixou=True)
    except EsajDocumentoNaoPdfError:
        return ResultadoDocumento(status=STATUS_DOC_ILEGIVEL, url_hash=atual, baixou=True)
    except EsajPortalIndisponivelError:
        return ResultadoDocumento(status=STATUS_DOC_ERRO, url_hash=atual, baixou=True)

    try:
        extracao = await extrair(pdf)
    except PdfIlegivelError:
        return ResultadoDocumento(status=STATUS_DOC_ILEGIVEL, url_hash=atual, baixou=True)
    finally:
        pdf = b""

    texto, paginas, ocr, parcial = _texto_paginas(extracao)
    if not texto.strip():
        return ResultadoDocumento(
            status=STATUS_DOC_ILEGIVEL,
            paginas=paginas,
            paginas_ocr=ocr,
            url_hash=atual,
            baixou=True,
        )

    try:
        ficha = await resumir_em_blocos(resumir, texto, titulo=titulo, data=data)
    except LLMLimiteAtingidoError:
        return ResultadoDocumento(
            status=STATUS_DOC_PENDENTE,
            paginas=paginas,
            paginas_ocr=ocr,
            url_hash=atual,
            baixou=True,
            parar="limite_ia",
        )
    except LLMAutenticacaoError:
        return ResultadoDocumento(
            status=STATUS_DOC_PENDENTE,
            paginas=paginas,
            paginas_ocr=ocr,
            url_hash=atual,
            baixou=True,
            parar="ia_recusada",
        )
    except Exception as exc:
        logger.info("Resumo do documento falhou (causa=%s)", type(exc).__name__)
        return ResultadoDocumento(
            status=STATUS_DOC_ERRO,
            paginas=paginas,
            paginas_ocr=ocr,
            url_hash=atual,
            baixou=True,
        )

    if not ficha.strip():
        return ResultadoDocumento(
            status=STATUS_DOC_ILEGIVEL,
            paginas=paginas,
            paginas_ocr=ocr,
            url_hash=atual,
            baixou=True,
        )

    return ResultadoDocumento(
        status=STATUS_DOC_PARCIAL if parcial else STATUS_DOC_LIDO,
        ficha=ficha,
        paginas=paginas,
        paginas_ocr=ocr,
        url_hash=atual,
        baixou=True,
    )
