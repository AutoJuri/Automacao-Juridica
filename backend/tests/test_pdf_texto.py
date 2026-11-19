"""Extração de texto do PDF — arquivos gerados no teste, sem processo real."""

import pymupdf
import pytest

from app.services.pdf_texto import PdfIlegivelError, extrair_texto_pdf


def _pdf_com_texto() -> bytes:
    doc = pymupdf.open()
    pagina = doc.new_page()
    pagina.insert_text(
        (72, 72),
        "Peticao inicial de teste com texto suficiente para a camada.",
    )
    dados = doc.tobytes()
    doc.close()
    return dados


def _pdf_sem_texto(paginas: int = 1) -> bytes:
    doc = pymupdf.open()
    for _ in range(paginas):
        pagina = doc.new_page()
        pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 80, 40))
        pix.clear_with(255)
        pagina.insert_image(pymupdf.Rect(72, 72, 152, 112), pixmap=pix)
    dados = doc.tobytes()
    doc.close()
    return dados


def test_usa_camada_de_texto_sem_ocr():
    chamadas: list[bytes] = []

    def ocr(png: bytes) -> str:
        chamadas.append(png)
        return "nao deveria"

    extracao = extrair_texto_pdf(_pdf_com_texto(), ocr=ocr)
    assert chamadas == []
    assert extracao.parcial is False
    assert extracao.paginas[0].usou_ocr is False
    assert "Peticao inicial" in extracao.paginas[0].texto


_CARIMBO = (
    "Para conferir o original, acesse o site https://esaj.tjsp.jus.br/pastadigital/pg/abrirConferenciaDocumento.do, "
    "informe o processo 0000000-00.0000.0.00.0000 e código AbCd1234.\n"
    "Este documento é cópia do original, assinado digitalmente por NOME DE TESTE, "
    "protocolado em 01/01/2024 às 10:00, sob o número 00000000000000000000.\n"
    "fls. 33"
)


def _pdf_so_com_carimbo() -> bytes:
    doc = pymupdf.open()
    pagina = doc.new_page()
    pagina.insert_text((72, 72), _CARIMBO)
    dados = doc.tobytes()
    doc.close()
    return dados


def _pdf_com_texto_e_carimbo() -> bytes:
    doc = pymupdf.open()
    pagina = doc.new_page()
    pagina.insert_text((72, 72), "Peticao inicial de teste com texto suficiente para a camada.")
    pagina.insert_text((72, 120), _CARIMBO)
    dados = doc.tobytes()
    doc.close()
    return dados


def test_carimbo_sozinho_vai_para_o_ocr():
    chamadas: list[bytes] = []

    def ocr(png: bytes) -> str:
        chamadas.append(png)
        return "Pedido de reintegracao de posse com texto lido na imagem."

    extracao = extrair_texto_pdf(_pdf_so_com_carimbo(), ocr=ocr)
    assert len(chamadas) == 1
    assert extracao.paginas[0].usou_ocr is True
    assert "reintegracao" in extracao.paginas[0].texto
    assert "Para conferir" not in extracao.paginas[0].texto


def test_carimbo_nao_apaga_o_texto_selecionavel():
    chamadas: list[bytes] = []

    extracao = extrair_texto_pdf(
        _pdf_com_texto_e_carimbo(),
        ocr=lambda png: chamadas.append(png) or "ocr",
    )
    assert chamadas == []
    assert extracao.paginas[0].usou_ocr is False
    assert "Peticao inicial" in extracao.paginas[0].texto
    assert "Para conferir" not in extracao.paginas[0].texto
    assert "fls." not in extracao.paginas[0].texto


def test_pagina_sem_texto_chama_ocr():
    chamadas: list[bytes] = []

    def ocr(png: bytes) -> str:
        chamadas.append(png)
        return "Texto da imagem de teste com caracteres suficientes."

    extracao = extrair_texto_pdf(_pdf_sem_texto(), ocr=ocr)
    assert len(chamadas) == 1
    assert extracao.paginas[0].usou_ocr is True
    assert "Texto da imagem" in extracao.paginas[0].texto


def test_rejeita_o_que_nao_e_pdf():
    with pytest.raises(PdfIlegivelError):
        extrair_texto_pdf(b"isto nao e um pdf")
    with pytest.raises(PdfIlegivelError):
        extrair_texto_pdf(b"%PDF-1.4 lixo sem estrutura")


def test_corta_paginas_e_marca_parcial():
    doc = pymupdf.open()
    for indice in range(3):
        pagina = doc.new_page()
        pagina.insert_text(
            (72, 72),
            f"Pagina {indice} com texto suficiente para nao usar ocr neste documento de teste.",
        )
    dados = doc.tobytes()
    doc.close()

    extracao = extrair_texto_pdf(dados, max_paginas=2, ocr=lambda _: "ocr")
    assert extracao.parcial is True
    assert len(extracao.paginas) == 2
    assert all(not pagina.usou_ocr for pagina in extracao.paginas)


def test_limite_de_ocr_marca_parcial():
    extracao = extrair_texto_pdf(
        _pdf_sem_texto(3),
        max_paginas_ocr=1,
        ocr=lambda _: "Texto ocr com caracteres suficientes para a ficha.",
    )
    assert extracao.parcial is True
    assert sum(1 for pagina in extracao.paginas if pagina.usou_ocr) == 1
