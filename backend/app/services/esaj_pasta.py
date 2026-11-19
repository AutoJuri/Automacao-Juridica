"""Abre a pasta digital do processo (o mesmo link de "Baixar PDFs").

O PDF só existe em memória. A URL com parâmetros não entra em log.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.services.esaj_documentos import (
    PATHS_PDF,
    _e_pdf,
    _ler,
    _validar_corpo,
    url_pdf_permitida,
)
from app.services.esaj_http import (
    ESAJ_BASE_URL,
    EsajPortalIndisponivelError,
    EsajSessaoInvalidaError,
    resposta_indica_login,
)

logger = logging.getLogger(__name__)

PATH_ENTRADA = "/cpopg/abrirPastaDigitalIntegracao.do"
PATH_GET_PDF = "/pastadigital/getPDF.do"
MAX_PECAS = 60
MAX_LISTAS = 3
_MARCADOR_ARVORE = "var requestScope = "
_CAMINHO_PASTA = re.compile(r"/pastadigital/[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*\.do")
_PARAMS_PROIBIDOS = set("\r\n\t <>\"'")


@dataclass(frozen=True, slots=True)
class PecaPasta:
    titulo: str | None
    url: str


def url_pasta_permitida(url: str | None) -> str | None:
    """https no host do e-SAJ, no servlet da pasta que já vem na ficha."""
    if not url:
        return None
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or parsed.netloc != "esaj.tjsp.jus.br":
        return None
    if parsed.username or parsed.password:
        return None
    if parsed.path != PATH_ENTRADA:
        return None
    return url.strip()


def _titulo(tag) -> str | None:
    texto = tag.get_text(" ", strip=True)
    if not texto:
        return None
    return texto[:180]


def _url_getpdf(parametros: str) -> str | None:
    if not parametros or len(parametros) > 2000 or "cdDocumento=" not in parametros:
        return None
    if any(char in parametros for char in _PARAMS_PROIBIDOS):
        return None
    if "://" in parametros or parametros.startswith(("/", "?")):
        return None
    return url_pdf_permitida(f"{ESAJ_BASE_URL}{PATH_GET_PDF}?{parametros}")


def _titulo_arvore(valor: object) -> str | None:
    if not isinstance(valor, str):
        return None
    texto = valor.strip()
    if not texto:
        return None
    return texto[:180]


def pecas_da_arvore(html: str) -> list[PecaPasta]:
    """Documentos declarados na árvore da pasta. A query não sai desta função para log."""
    inicio = html.find(_MARCADOR_ARVORE)
    if inicio < 0:
        return []
    try:
        dados, _ = json.JSONDecoder().raw_decode(html[inicio + len(_MARCADOR_ARVORE) :].lstrip())
    except json.JSONDecodeError:
        return []

    pecas: list[PecaPasta] = []
    vistos: set[str] = set()

    def visitar(no: object) -> None:
        if len(pecas) >= MAX_PECAS:
            return
        if isinstance(no, dict):
            parametros = no.get("parametros")
            if isinstance(parametros, str) and no.get("documentoSigiloso") is not True:
                url = _url_getpdf(parametros)
                if url and url not in vistos:
                    vistos.add(url)
                    pecas.append(PecaPasta(titulo=_titulo_arvore(no.get("title")), url=url))
            for valor in no.values():
                visitar(valor)
        elif isinstance(no, list):
            for item in no:
                visitar(item)

    visitar(dados)
    return pecas


def listar_pecas(html: str) -> list[PecaPasta]:
    """PDFs da árvore da pasta, ou links já presentes no HTML."""
    da_arvore = pecas_da_arvore(html)
    if da_arvore:
        return da_arvore
    soup = BeautifulSoup(html[:500_000], "lxml")
    pecas: list[PecaPasta] = []
    vistos: set[str] = set()
    for tag in soup.find_all(["a", "iframe", "embed"]):
        bruto = tag.get("href") or tag.get("src")
        if not isinstance(bruto, str):
            continue
        absoluto = urljoin(ESAJ_BASE_URL, bruto.strip())
        permitido = url_pdf_permitida(absoluto)
        if permitido is None or permitido in vistos:
            continue
        vistos.add(permitido)
        pecas.append(PecaPasta(titulo=_titulo(tag), url=permitido))
        if len(pecas) >= MAX_PECAS:
            break
    return pecas


def links_de_lista(html: str) -> list[str]:
    """Pedidos da própria pasta citados no HTML. No máximo alguns, sem PDF."""
    vistos: list[str] = []
    for achado in _CAMINHO_PASTA.findall(html[:500_000]):
        if achado in PATHS_PDF or achado in vistos:
            continue
        vistos.append(achado)
        if len(vistos) >= MAX_LISTAS:
            break
    return vistos


@dataclass(frozen=True, slots=True)
class PastaAberta:
    html: str
    pdf: bytes


async def abrir_pasta(client: httpx.AsyncClient, url: str, *, referer: str) -> PastaAberta:
    """HTML da pasta, ou o PDF se o servlet já devolver o arquivo.

    Login do CAS vira sessão inválida. O cookie da ficha não é apagado.
    """
    if url_pasta_permitida(url) is None:
        raise EsajPortalIndisponivelError("url_pasta_invalida")
    corpo = await _ler(client, url, referer=referer, tamanho_max=4_000_000)
    _recusar_login(corpo.content_type, corpo.dados, corpo.final_url)
    _validar_corpo(corpo)
    if _e_pdf(corpo.dados):
        return PastaAberta(html="", pdf=corpo.dados)
    return PastaAberta(html=corpo.dados.decode("utf-8", errors="ignore"), pdf=b"")


async def carregar_pecas(
    client: httpx.AsyncClient, html: str, *, referer: str
) -> list[PecaPasta]:
    pecas = listar_pecas(html)
    if pecas:
        return pecas
    for caminho in links_de_lista(html):
        url = f"{ESAJ_BASE_URL}{caminho}"
        try:
            corpo = await _ler(client, url, referer=referer, tamanho_max=2_000_000)
        except (EsajPortalIndisponivelError, EsajSessaoInvalidaError):
            continue
        _recusar_login(corpo.content_type, corpo.dados, corpo.final_url)
        if _e_pdf(corpo.dados):
            continue
        achadas = listar_pecas(corpo.dados.decode("utf-8", errors="ignore"))
        if achadas:
            return achadas
    return []


async def baixar_pdf_pasta(client: httpx.AsyncClient, url: str) -> bytes:
    """Bytes do PDF da pasta. Quem chama descarta a variável."""
    if url_pdf_permitida(url) is None:
        raise EsajPortalIndisponivelError("url_pdf_invalida")
    corpo = await _ler(client, url, referer=f"{ESAJ_BASE_URL}{PATH_ENTRADA}", tamanho_max=15 * 1024 * 1024)
    _recusar_login(corpo.content_type, corpo.dados, corpo.final_url)
    _validar_corpo(corpo)
    if not _e_pdf(corpo.dados):
        from app.services.esaj_documentos import EsajDocumentoNaoPdfError

        raise EsajDocumentoNaoPdfError("sem_pdf")
    return corpo.dados


def _recusar_login(content_type: str, dados: bytes, final_url: str) -> None:
    amostra = dados[:1500].decode("utf-8", errors="ignore")
    if "sua sessão expirou" in amostra.lower():
        raise EsajSessaoInvalidaError("pasta_login")
    if resposta_indica_login(content_type, amostra, final_url):
        raise EsajSessaoInvalidaError("pasta_login")


def caminho_final(url: str) -> str:
    return urlparse(url).path or "-"
