"""Regras dos arquivos do Drive, sem banco e sem Google."""

import io
import zipfile

import pytest

from app.core import arquivos_drive as regras
from app.core.arquivos_drive import ArquivoInvalidoError


def _zip(*nomes: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as pacote:
        for nome in nomes:
            pacote.writestr(nome, "x")
    return buffer.getvalue()


class TestValidarEnvio:
    def test_aceita_cada_tipo_com_o_conteudo_certo(self):
        casos = {
            "peca.pdf": b"%PDF-1.7\n...",
            "peca.docx": _zip("word/document.xml", "[Content_Types].xml"),
            "peca.odt": _zip("mimetype", "content.xml"),
            "peca.doc": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 16,
            "nota.txt": "olá, mundo".encode(),
            "modelo.rtf": b"{\\rtf1\\ansi texto}",
            "foto.png": b"\x89PNG\r\n\x1a\n" + b"\x00" * 8,
            "foto.JPG": b"\xff\xd8\xff\xe0" + b"\x00" * 8,
            "foto.jpeg": b"\xff\xd8\xff\xe1" + b"\x00" * 8,
        }
        for nome, conteudo in casos.items():
            limpo, mime = regras.validar_envio(nome, conteudo)
            assert limpo == nome
            assert mime in regras.MIMES_PERMITIDOS

    def test_o_tipo_vem_da_extensao_e_nao_do_cliente(self):
        assert regras.validar_envio("a.PDF", b"%PDF-1.4")[1] == "application/pdf"

    @pytest.mark.parametrize("nome", ["virus.exe", "script.js", "pagina.html", "sem_extensao", "a.pdf.exe", "x.sh"])
    def test_recusa_extensao_fora_da_lista(self, nome):
        with pytest.raises(ArquivoInvalidoError):
            regras.validar_envio(nome, b"%PDF-1.4")

    def test_recusa_conteudo_que_nao_bate_com_o_tipo(self):
        for nome, conteudo in {
            "falso.pdf": b"MZ\x90\x00 programa",
            "falso.docx": _zip("outra/coisa.xml"),
            "falso.png": b"%PDF-1.4",
            "falso.jpg": b"\x89PNG\r\n\x1a\n",
            "falso.doc": b"texto comum",
            "falso.txt": b"binario\x00\x01",
        }.items():
            with pytest.raises(ArquivoInvalidoError):
                regras.validar_envio(nome, conteudo)

    def test_recusa_executavel_mesmo_com_extensao_de_texto(self):
        with pytest.raises(ArquivoInvalidoError):
            regras.validar_envio("leia-me.txt", b"MZ" + b"\x90" * 8)
        with pytest.raises(ArquivoInvalidoError):
            regras.validar_envio("leia-me.txt", b"#!/bin/sh\nrm -rf /")

    def test_recusa_vazio_e_acima_do_teto(self, monkeypatch):
        with pytest.raises(ArquivoInvalidoError):
            regras.validar_envio("a.pdf", b"")
        monkeypatch.setattr(regras, "TAMANHO_MAX", 16)
        with pytest.raises(ArquivoInvalidoError):
            regras.validar_envio("a.pdf", b"%PDF-" + b"0" * 32)


class TestSanitizarNome:
    def test_tira_caminho_e_caracteres_perigosos(self):
        assert regras.sanitizar_nome("../../etc/passwd.txt") == "passwd.txt"
        assert regras.sanitizar_nome("C:\\Users\\x\\peca.pdf") == "peca.pdf"
        assert regras.sanitizar_nome('a<b>:"c"|d?.pdf') == "a_b___c__d_.pdf"
        assert regras.sanitizar_nome("com\x00nulo\n.pdf") == "com_nulo_.pdf"

    def test_nome_vazio_e_recusado(self):
        for nome in (None, "", "   ", "...", "/"):
            with pytest.raises(ArquivoInvalidoError):
                regras.sanitizar_nome(nome)

    def test_nome_longo_preserva_a_extensao(self):
        limpo = regras.sanitizar_nome("a" * 400 + ".pdf")
        assert len(limpo) == regras.NOME_MAX
        assert limpo.endswith(".pdf")


class TestMetadadosDoGoogle:
    def test_recusa_pasta_e_documento_nativo_do_google(self):
        for mime in (
            "application/vnd.google-apps.folder",
            "application/vnd.google-apps.document",
            None,
            "application/x-msdownload",
        ):
            with pytest.raises(ArquivoInvalidoError):
                regras.validar_metadados_google(mime, 10)

    def test_aceita_tipo_permitido_e_recusa_tamanho(self):
        regras.validar_metadados_google("application/pdf", 10)
        regras.validar_metadados_google("application/pdf", None)
        with pytest.raises(ArquivoInvalidoError):
            regras.validar_metadados_google("application/pdf", regras.TAMANHO_MAX + 1)
