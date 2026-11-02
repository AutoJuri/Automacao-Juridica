"""Baixa o PDF de uma movimentação para a memória e descarta em seguida.

A URL já passou por `url_documento_publica` na coleta. Aqui ela é
validada de novo. O corpo não é gravado, não volta na API e não entra
em log. HTML de visualizador só é seguido se apontar um path de PDF
no próprio host do e-SAJ (um salto).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from html import unescape
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.services.esaj_cpo_parser import url_documento_publica
from app.services.esaj_http import (
    ESAJ_BASE_URL,
    EsajPortalIndisponivelError,
    EsajRateLimitError,
    EsajSessaoInvalidaError,
    _headers_html,
    resposta_indica_login,
)
from app.services.pdf_texto import TAMANHO_MAX_BYTES

logger = logging.getLogger(__name__)

# Um salto a partir do HTML do visualizador. O path de
# `abrirDocumentoVinculadoMovimentacao.do` não entra: seguir de novo
# seria loop. Sem cookie, o portal devolve HTML de acesso inválido.
PATHS_PDF = (
    "/pastadigital/getPDF.do",
    "/pastadigital/abrirDocumentoEdt.do",
)
TIMEOUT_DOCUMENTO_SEGUNDOS = 45.0
REFERER_CPO = f"{ESAJ_BASE_URL}/cpopg/open.do"
_AMOSTRA_LOGIN = 1500
_AMOSTRA_HTML = 200_000


class EsajDocumentoNaoPdfError(Exception):
    """Resposta autenticada que não é PDF e não aponta um PDF no host."""


class EsajDocumentoGrandeError(Exception):
    """Passou do teto de bytes. Não vale insistir no mesmo arquivo."""


@dataclass(frozen=True, slots=True)
class SondaDocumento:
    """Metadados da resposta. Sem URL, sem query e sem corpo."""

    status_http: int | None
    content_type: str
    tamanho: int
    redirecionou: bool
    parece_pdf: bool
    caminho: str | None
    causa: str


@dataclass(frozen=True, slots=True)
class _Corpo:
    status_http: int
    content_type: str
    dados: bytes
    final_url: str
    redirecionou: bool


def url_pdf_permitida(url: str | None) -> str | None:
    """https no host do e-SAJ, path exatamente na lista, sem userinfo."""
    if not url:
        return None
    trimmed = unescape(url.strip())
    parsed = urlparse(trimmed)
    if parsed.scheme != "https" or parsed.netloc != "esaj.tjsp.jus.br":
        return None
    if parsed.username or parsed.password:
        return None
    if parsed.path not in PATHS_PDF:
        return None
    return trimmed


def _absoluto(href: str) -> str | None:
    if not href or href.startswith("#") or href.lower().startswith("javascript:"):
        return None
    if href.startswith("/"):
        return f"{ESAJ_BASE_URL}{href}"
    if href.startswith("https://"):
        return href
    return None


def primeiro_link_pdf(html: str) -> str | None:
    """Primeiro link allowlisted. O resto do HTML é ignorado."""
    amostra = html[:_AMOSTRA_HTML]
    soup = BeautifulSoup(amostra, "lxml")
    for tag in soup.find_all(["a", "iframe", "embed"]):
        for attr in ("href", "src"):
            valor = tag.get(attr)
            if not isinstance(valor, str):
                continue
            absoluto = _absoluto(valor.strip())
            permitido = url_pdf_permitida(absoluto)
            if permitido:
                return permitido
    return None


def _e_pdf(dados: bytes) -> bool:
    return dados.startswith(b"%PDF")


def _amostra_texto(dados: bytes) -> str:
    return dados[:_AMOSTRA_LOGIN].decode("utf-8", errors="ignore")


def _redirecionou(origem: str, final: str) -> bool:
    a = urlparse(origem)
    b = urlparse(final)
    return (a.scheme, a.netloc, a.path) != (b.scheme, b.netloc, b.path)


def _caminho(url: str | None) -> str | None:
    if not url:
        return None
    path = urlparse(url).path
    return path or None


async def _ler(
    client: httpx.AsyncClient,
    url: str,
    *,
    referer: str,
    tamanho_max: int,
) -> _Corpo:
    headers = _headers_html(referer)
    headers["Accept"] = "application/pdf,text/html;q=0.9,*/*;q=0.8"
    try:
        async with client.stream(
            "GET", url, headers=headers, timeout=TIMEOUT_DOCUMENTO_SEGUNDOS
        ) as response:
            final = str(response.url)
            if response.status_code == 429:
                raise EsajRateLimitError("status_429")
            declarado = response.headers.get("content-length", "")
            if declarado.isdigit() and int(declarado) > tamanho_max:
                raise EsajDocumentoGrandeError("corpo_grande")
            buf = bytearray()
            async for pedaco in response.aiter_bytes():
                if len(buf) + len(pedaco) > tamanho_max:
                    raise EsajDocumentoGrandeError("corpo_grande")
                buf.extend(pedaco)
            return _Corpo(
                status_http=response.status_code,
                content_type=response.headers.get("content-type", ""),
                dados=bytes(buf),
                final_url=final,
                redirecionou=_redirecionou(url, final),
            )
    except httpx.TimeoutException as exc:
        raise EsajPortalIndisponivelError("timeout") from exc
    except httpx.HTTPError as exc:
        raise EsajPortalIndisponivelError(type(exc).__name__) from exc


def _validar_corpo(corpo: _Corpo) -> None:
    if not _e_pdf(corpo.dados) and resposta_indica_login(
        corpo.content_type, _amostra_texto(corpo.dados), corpo.final_url
    ):
        raise EsajSessaoInvalidaError("redirecionado_para_login")
    if corpo.status_http != 200:
        raise EsajPortalIndisponivelError(f"status_{corpo.status_http}")


async def baixar_documento(
    client: httpx.AsyncClient,
    url: str,
    *,
    tamanho_max: int = TAMANHO_MAX_BYTES,
) -> bytes:
    """Bytes do PDF. Quem chama descarta a variável ao terminar."""
    if url_documento_publica(url) is None:
        raise EsajPortalIndisponivelError("url_documento_invalida")

    primeiro = await _ler(client, url, referer=REFERER_CPO, tamanho_max=tamanho_max)
    _validar_corpo(primeiro)
    if _e_pdf(primeiro.dados):
        return primeiro.dados

    texto = primeiro.dados.decode("utf-8", errors="ignore")
    hop = primeiro_link_pdf(texto)
    if hop is None:
        raise EsajDocumentoNaoPdfError("sem_pdf")

    segundo = await _ler(client, hop, referer=url, tamanho_max=tamanho_max)
    _validar_corpo(segundo)
    if _e_pdf(segundo.dados):
        return segundo.dados
    raise EsajDocumentoNaoPdfError("hop_sem_pdf")


async def sondar_documento(
    client: httpx.AsyncClient,
    url: str,
    *,
    tamanho_max: int = TAMANHO_MAX_BYTES,
) -> SondaDocumento:
    """O que a URL devolve, sem guardar o corpo. Usado pelo script de laboratório."""
    vazio = SondaDocumento(
        status_http=None,
        content_type="",
        tamanho=0,
        redirecionou=False,
        parece_pdf=False,
        caminho=None,
        causa="url_invalida",
    )
    if url_documento_publica(url) is None:
        return vazio

    try:
        primeiro = await _ler(client, url, referer=REFERER_CPO, tamanho_max=tamanho_max)
        _validar_corpo(primeiro)
    except EsajSessaoInvalidaError:
        return SondaDocumento(None, "", 0, False, False, None, "sessao_invalida")
    except EsajRateLimitError:
        return SondaDocumento(429, "", 0, False, False, None, "rate_limit")
    except EsajDocumentoGrandeError:
        return SondaDocumento(None, "", 0, False, False, None, "corpo_grande")
    except EsajPortalIndisponivelError as exc:
        logger.info("Sonda de documento falhou (causa=%s)", type(exc).__name__)
        return SondaDocumento(None, "", 0, False, False, None, "portal")

    if _e_pdf(primeiro.dados):
        return SondaDocumento(
            primeiro.status_http,
            primeiro.content_type,
            len(primeiro.dados),
            primeiro.redirecionou,
            True,
            None,
            "ok",
        )

    hop = primeiro_link_pdf(primeiro.dados.decode("utf-8", errors="ignore"))
    if hop is None:
        return SondaDocumento(
            primeiro.status_http,
            primeiro.content_type,
            len(primeiro.dados),
            primeiro.redirecionou,
            False,
            None,
            "sem_pdf",
        )

    try:
        segundo = await _ler(client, hop, referer=url, tamanho_max=tamanho_max)
        _validar_corpo(segundo)
    except EsajSessaoInvalidaError:
        return SondaDocumento(None, "", 0, False, False, _caminho(hop), "sessao_invalida")
    except EsajRateLimitError:
        return SondaDocumento(429, "", 0, False, False, _caminho(hop), "rate_limit")
    except EsajDocumentoGrandeError:
        return SondaDocumento(None, "", 0, False, False, _caminho(hop), "corpo_grande")
    except EsajPortalIndisponivelError:
        return SondaDocumento(None, "", 0, False, False, _caminho(hop), "portal")

    return SondaDocumento(
        segundo.status_http,
        segundo.content_type,
        len(segundo.dados),
        segundo.redirecionou or primeiro.redirecionou,
        _e_pdf(segundo.dados),
        _caminho(hop),
        "ok" if _e_pdf(segundo.dados) else "sem_pdf",
    )
