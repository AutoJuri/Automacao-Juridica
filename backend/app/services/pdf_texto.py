"""Extrai texto de um PDF que só existe em memória (ADR-024).

Página com camada de texto usa essa camada. OCR (Tesseract, português)
só roda na página sem texto útil. O binário não é gravado em disco.
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pymupdf

logger = logging.getLogger(__name__)

TAMANHO_MAX_BYTES = 15 * 1024 * 1024
MAX_PAGINAS = 40
MAX_PAGINAS_OCR = 8
MIN_CHARS_TEXTO = 40
OCR_DPI = 200

OcrFn = Callable[[bytes], str]

# O carimbo do e-SAJ vem na camada de texto até de página que é só imagem.
# Ele não conta como conteúdo: senão o OCR nunca roda.
_LINHA_FLS = re.compile(r"^\s*fls\.\s*\d+\s*$", re.IGNORECASE)


class PdfIlegivelError(Exception):
    """O arquivo não é um PDF legível. A mensagem é um código, nunca o conteúdo."""


@dataclass(frozen=True, slots=True)
class PaginaTexto:
    numero: int
    texto: str
    usou_ocr: bool


@dataclass(frozen=True, slots=True)
class ExtracaoPdf:
    paginas: tuple[PaginaTexto, ...]
    parcial: bool


def _sem_carimbo(texto: str) -> str:
    linhas: list[str] = []
    for linha in texto.splitlines():
        baixa = linha.lower()
        if "para conferir o original" in baixa:
            continue
        if "cópia do original" in baixa or "copia do original" in baixa:
            continue
        if _LINHA_FLS.match(linha):
            continue
        linhas.append(linha)
    return "\n".join(linhas).strip()


def _texto_util(texto: str) -> bool:
    letras = sum(1 for ch in texto if ch.isalnum())
    return letras >= MIN_CHARS_TEXTO


_TESSDATA_LOCAL = Path(__file__).resolve().parents[2] / ".tessdata"


def _comando_tesseract() -> str | None:
    achado = shutil.which("tesseract")
    if achado:
        return achado
    candidato = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if candidato.is_file():
        return str(candidato)
    return None


def _ocr_padrao(png: bytes) -> str:
    """Tesseract em português. Falha vira texto vazio — a ficha não inventa."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        logger.info("OCR indisponivel (causa=import)")
        return ""
    comando = _comando_tesseract()
    if comando is None:
        logger.info("OCR indisponivel (causa=tesseract_ausente)")
        return ""
    pytesseract.pytesseract.tesseract_cmd = comando
    if (_TESSDATA_LOCAL / "por.traineddata").is_file():
        os.environ["TESSDATA_PREFIX"] = str(_TESSDATA_LOCAL)
    try:
        imagem = Image.open(io.BytesIO(png))
        return pytesseract.image_to_string(imagem, lang="por") or ""
    except Exception as exc:
        logger.info("OCR indisponivel (causa=%s)", type(exc).__name__)
        return ""


def _render_png(page: pymupdf.Page) -> bytes:
    pix = page.get_pixmap(dpi=OCR_DPI, alpha=False)
    try:
        return pix.tobytes("png")
    finally:
        pix = None


def extrair_texto_pdf(
    dados: bytes,
    *,
    ocr: OcrFn | None = None,
    max_paginas: int = MAX_PAGINAS,
    max_paginas_ocr: int = MAX_PAGINAS_OCR,
    tamanho_max: int = TAMANHO_MAX_BYTES,
) -> ExtracaoPdf:
    """Devolve o texto página a página. Ultrapassar o teto marca `parcial`."""
    if not dados.startswith(b"%PDF"):
        raise PdfIlegivelError("nao_pdf")
    if len(dados) > tamanho_max:
        raise PdfIlegivelError("tamanho")

    leitor = ocr or _ocr_padrao
    doc: pymupdf.Document | None = None
    try:
        try:
            doc = pymupdf.open(stream=dados, filetype="pdf")
        except Exception as exc:
            raise PdfIlegivelError("parse") from exc

        total = doc.page_count
        limite = min(total, max_paginas)
        parcial = total > max_paginas
        ocr_feitos = 0
        paginas: list[PaginaTexto] = []

        for indice in range(limite):
            page = doc.load_page(indice)
            bruto = page.get_text("text") or ""
            texto = _sem_carimbo(bruto)
            usou_ocr = False
            if not _texto_util(texto):
                if ocr_feitos < max_paginas_ocr:
                    texto = _sem_carimbo(leitor(_render_png(page)) or "")
                    usou_ocr = True
                    ocr_feitos += 1
                else:
                    texto = ""
                    parcial = True
            paginas.append(
                PaginaTexto(numero=indice + 1, texto=texto.strip(), usou_ocr=usou_ocr)
            )
        return ExtracaoPdf(paginas=tuple(paginas), parcial=parcial)
    finally:
        if doc is not None:
            doc.close()


_semaforo: asyncio.Semaphore | None = None


def _semaforo_ocr() -> asyncio.Semaphore:
    global _semaforo
    if _semaforo is None:
        # Uma página por vez: o pixmap em 200 dpi não disputa CPU com a API.
        _semaforo = asyncio.Semaphore(1)
    return _semaforo


async def extrair_texto_pdf_async(
    dados: bytes,
    *,
    max_paginas: int = MAX_PAGINAS,
    max_paginas_ocr: int = MAX_PAGINAS_OCR,
) -> ExtracaoPdf:
    async with _semaforo_ocr():
        return await asyncio.to_thread(
            extrair_texto_pdf,
            dados,
            max_paginas=max_paginas,
            max_paginas_ocr=max_paginas_ocr,
        )
