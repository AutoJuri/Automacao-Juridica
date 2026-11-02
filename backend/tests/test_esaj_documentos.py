"""Download em memória do documento do e-SAJ. Sem rede e sem gravar corpo."""

import logging

import httpx
import pytest

from app.services.esaj_documentos import (
    EsajDocumentoGrandeError,
    EsajDocumentoNaoPdfError,
    baixar_documento,
    primeiro_link_pdf,
    sondar_documento,
)
from app.services.esaj_http import (
    EsajPortalIndisponivelError,
    EsajRateLimitError,
    EsajSessaoInvalidaError,
)

URL = (
    "https://esaj.tjsp.jus.br/cpopg/abrirDocumentoVinculadoMovimentacao.do"
    "?processo.codigo=SEGREDO99&cdDocumento=1"
)
PDF = b"%PDF-1.4\n%teste\n"


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)


@pytest.mark.asyncio
async def test_pdf_direto():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=PDF, headers={"content-type": "application/pdf"})

    async with _client(handler) as client:
        dados = await baixar_documento(client, URL)
    assert dados.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_html_segue_um_salto_allowlisted():
    caminhos: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        caminhos.append(request.url.path)
        if request.url.path.endswith("getPDF.do"):
            return httpx.Response(200, content=PDF, headers={"content-type": "application/pdf"})
        html = '<a href="/pastadigital/getPDF.do?cdDocumento=9">abrir</a>'
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    async with _client(handler) as client:
        dados = await baixar_documento(client, URL)
        sonda = await sondar_documento(client, URL)
    assert dados.startswith(b"%PDF")
    assert caminhos[0].endswith("abrirDocumentoVinculadoMovimentacao.do")
    assert caminhos[1] == "/pastadigital/getPDF.do"
    assert sonda.parece_pdf is True
    assert sonda.caminho == "/pastadigital/getPDF.do"
    assert "cdDocumento" not in (sonda.caminho or "")


@pytest.mark.asyncio
async def test_nao_segue_outro_host_nem_javascript():
    chamadas = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal chamadas
        chamadas += 1
        html = (
            '<a href="javascript:alert(1)">x</a>'
            '<a href="https://evil.test/pastadigital/getPDF.do?q=1">x</a>'
        )
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    async with _client(handler) as client:
        with pytest.raises(EsajDocumentoNaoPdfError):
            await baixar_documento(client, URL)
    assert chamadas == 1
    assert primeiro_link_pdf(html_de_teste()) is None


def html_de_teste() -> str:
    return (
        '<a href="javascript:alert(1)">x</a>'
        '<a href="https://evil.test/pastadigital/getPDF.do?q=1">x</a>'
    )


@pytest.mark.asyncio
async def test_url_fora_do_host_nao_dispara_get():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("nao deveria chamar a rede")

    async with _client(handler) as client:
        with pytest.raises(EsajPortalIndisponivelError):
            await baixar_documento(
                client,
                "https://evil.test/cpopg/abrirDocumentoVinculadoMovimentacao.do?x=1",
            )


@pytest.mark.asyncio
async def test_sessao_invalida_rate_limit_e_corpo_grande():
    login = "<html><form id='usernameForm'></form><form id='passwordForm'></form></html>"

    async with _client(lambda request: httpx.Response(200, text=login, headers={"content-type": "text/html"})) as client:
        with pytest.raises(EsajSessaoInvalidaError):
            await baixar_documento(client, URL)

    async with _client(lambda request: httpx.Response(429, text="")) as client:
        with pytest.raises(EsajRateLimitError):
            await baixar_documento(client, URL)

    async with _client(lambda request: httpx.Response(200, content=b"%PDF-1.4 grande")) as client:
        with pytest.raises(EsajDocumentoGrandeError):
            await baixar_documento(client, URL, tamanho_max=8)


@pytest.mark.asyncio
async def test_log_nao_leva_a_url(caplog):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="fora")

    with caplog.at_level(logging.INFO):
        async with _client(handler) as client:
            sonda = await sondar_documento(client, URL)
    assert sonda.causa == "portal"
    assert "SEGREDO99" not in caplog.text
    assert "cdDocumento" not in caplog.text
