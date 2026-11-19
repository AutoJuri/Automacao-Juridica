"""Pasta digital: lista de PDFs e recusa de login. Sem rede."""

import httpx
import pytest

from app.services.esaj_http import EsajSessaoInvalidaError
from app.services.esaj_pasta import abrir_pasta, listar_pecas, pecas_da_arvore

URL = (
    "https://esaj.tjsp.jus.br/cpopg/abrirPastaDigitalIntegracao.do"
    "?cdProcesso=1&modoServico=false"
)
HTML = """
<html><body>
<a href="/pastadigital/getPDF.do?cdDocumento=1">Petição inicial</a>
<a href="https://evil.test/pastadigital/getPDF.do?cdDocumento=2">fora</a>
<a href="/pastadigital/abrirDocumentoEdt.do?id=3">Decisão</a>
</body></html>
"""


def test_arvore_vira_getpdf_do_proprio_host():
    html = """
    <script>
    var requestScope = [{"parametros": "cdDocumento=10&origemDocumento=P", "title": "Petição"}];
    </script>
    """
    pecas = pecas_da_arvore(html)
    assert [peca.titulo for peca in pecas] == ["Petição"]
    assert pecas[0].url == (
        "https://esaj.tjsp.jus.br/pastadigital/getPDF.do?cdDocumento=10&origemDocumento=P"
    )


def test_arvore_ignora_parametro_que_nao_e_query():
    html = """
    var requestScope = [{"parametros": "https://evil.test/getPDF.do?cdDocumento=1", "title": "Fora"}];
    """
    assert pecas_da_arvore(html) == []


def test_lista_so_pdf_do_proprio_host():
    pecas = listar_pecas(HTML)
    assert [peca.titulo for peca in pecas] == ["Petição inicial", "Decisão"]
    assert all(peca.url.startswith("https://esaj.tjsp.jus.br/pastadigital/") for peca in pecas)


@pytest.mark.asyncio
async def test_login_da_pasta_nao_parece_pdf():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="<html>usernameForm passwordForm</html>",
            headers={"content-type": "text/html"},
            request=request,
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, follow_redirects=True) as client:
        with pytest.raises(EsajSessaoInvalidaError):
            await abrir_pasta(client, URL, referer="https://esaj.tjsp.jus.br/cpopg/show.do")
