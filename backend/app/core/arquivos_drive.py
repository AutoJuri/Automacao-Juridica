"""Regras dos arquivos do Drive: tipos, tamanho, nome e conferência do conteúdo.

O frontend repete parte disto só para avisar cedo. Quem decide é este módulo.
Nunca se confia no tipo que o cliente declara: o tipo sai da extensão e é
conferido contra os primeiros bytes. Executável não entra.
"""

import io
import re
import zipfile

TAMANHO_MAX = 25 * 1024 * 1024
NOME_MAX = 255

MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MIME_ODT = "application/vnd.oasis.opendocument.text"

MIME_POR_EXTENSAO: dict[str, str] = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": MIME_DOCX,
    ".odt": MIME_ODT,
    ".txt": "text/plain",
    ".rtf": "application/rtf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}
MIMES_PERMITIDOS = frozenset(MIME_POR_EXTENSAO.values())

_ASSINATURAS_EXECUTAVEIS = (b"MZ", b"\x7fELF", b"#!", b"\xca\xfe\xba\xbe", b"\xcf\xfa\xed\xfe")
_OLE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_PNG = b"\x89PNG\r\n\x1a\n"
_CARACTERES_INVALIDOS = re.compile(r'[\x00-\x1f\x7f<>:"/\\|?*]')


class ArquivoInvalidoError(ValueError):
    """Arquivo recusado. A mensagem é segura para ir à tela."""


def extensao(nome: str) -> str:
    ponto = nome.rfind(".")
    return nome[ponto:].lower() if ponto != -1 else ""


def sanitizar_nome(nome: str | None) -> str:
    """Tira caminho, caracteres de controle e símbolos que quebram nome de arquivo."""
    bruto = (nome or "").replace("\\", "/").rsplit("/", 1)[-1]
    limpo = _CARACTERES_INVALIDOS.sub("_", bruto).strip(" .")
    if not limpo:
        raise ArquivoInvalidoError("O arquivo precisa ter um nome")
    if len(limpo) > NOME_MAX:
        ext = extensao(limpo)
        limpo = limpo[: NOME_MAX - len(ext)] + ext
    return limpo


def mime_da_extensao(nome: str) -> str:
    mime = MIME_POR_EXTENSAO.get(extensao(nome))
    if mime is None:
        raise ArquivoInvalidoError(
            "Tipo de arquivo não aceito. Use PDF, Word, ODT, TXT, RTF, PNG ou JPG."
        )
    return mime


def _zip_tem(conteudo: bytes, *nomes: str) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(conteudo)) as pacote:
            presentes = set(pacote.namelist())
    except (zipfile.BadZipFile, ValueError):
        return False
    return all(nome in presentes for nome in nomes)


def _confere_conteudo(mime: str, conteudo: bytes) -> bool:
    cabeca = conteudo[:8192]
    if mime == "application/pdf":
        return b"%PDF-" in cabeca[:1024]
    if mime == "application/msword":
        return cabeca.startswith(_OLE)
    if mime == MIME_DOCX:
        return cabeca.startswith(b"PK\x03\x04") and _zip_tem(conteudo, "word/document.xml")
    if mime == MIME_ODT:
        return cabeca.startswith(b"PK\x03\x04") and _zip_tem(conteudo, "mimetype", "content.xml")
    if mime == "application/rtf":
        return cabeca.lstrip().startswith(b"{\\rtf")
    if mime == "image/png":
        return cabeca.startswith(_PNG)
    if mime == "image/jpeg":
        return cabeca.startswith(b"\xff\xd8\xff")
    if mime == "text/plain":
        return b"\x00" not in cabeca
    return False


def validar_envio(nome: str | None, conteudo: bytes) -> tuple[str, str]:
    """Devolve `(nome_limpo, mime)` ou levanta `ArquivoInvalidoError`."""
    limpo = sanitizar_nome(nome)
    mime = mime_da_extensao(limpo)
    if not conteudo:
        raise ArquivoInvalidoError("O arquivo está vazio")
    if len(conteudo) > TAMANHO_MAX:
        raise ArquivoInvalidoError("O arquivo passa de 25 MB")
    if conteudo.startswith(_ASSINATURAS_EXECUTAVEIS):
        raise ArquivoInvalidoError("Arquivo executável não é aceito")
    if not _confere_conteudo(mime, conteudo):
        raise ArquivoInvalidoError("O conteúdo não corresponde ao tipo do arquivo")
    return limpo, mime


def validar_metadados_google(mime: str | None, tamanho: int | None) -> None:
    """Arquivo escolhido no seletor: só a ficha é gravada, mas o tipo e o tamanho contam."""
    if mime not in MIMES_PERMITIDOS:
        raise ArquivoInvalidoError(
            "Tipo de arquivo não aceito. Documentos do Google precisam ser baixados como PDF ou Word."
        )
    if tamanho is not None and tamanho > TAMANHO_MAX:
        raise ArquivoInvalidoError("O arquivo passa de 25 MB")
