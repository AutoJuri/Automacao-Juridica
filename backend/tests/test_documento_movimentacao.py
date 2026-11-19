"""PDF da movimentação (ADR-027): rota, erros e o que não pode vazar."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.main import app
from app.models.tribunal import SESSION_STATUS_ATIVO, SESSION_STATUS_BLOQUEADO
from app.services import documento_movimentacao as servico
from app.services.esaj_documentos import EsajDocumentoNaoPdfError
from app.services.esaj_http import EsajRateLimitError, EsajSessaoInvalidaError

URL_DOC = "https://esaj.tjsp.jus.br/cpopg/abrirDocumentoVinculadoMovimentacao.do?cdDocumento=123"
URL_CPO = "https://esaj.tjsp.jus.br/cpopg/show.do?processo.codigo=ABC"
URL_VIVA = "https://esaj.tjsp.jus.br/cpopg/abrirDocumentoVinculadoMovimentacao.do?cdDocumento=123&nmRecursoAcessado=vivo"
PDF = b"%PDF-1.7 conteudo"


async def _db_dummy():
    yield SimpleNamespace()


class _DbFalso:
    def __init__(self, resposta):
        self.resposta = resposta
        self.consultas: list[str] = []
        self.commits = 0

    async def scalar(self, consulta):
        self.consultas.append(str(consulta.compile(compile_kwargs={"literal_binds": False})))
        return self.resposta

    async def execute(self, consulta):
        self.consultas.append(str(consulta.compile(compile_kwargs={"literal_binds": False})))

        class _Linha:
            def first(inner_self):
                return self.resposta

        return _Linha()

    async def commit(self):
        self.commits += 1


def _sessao(**extra):
    base = dict(
        status=SESSION_STATUS_ATIVO,
        cookie_encrypted=b"x",
        tentativas_falha=0,
        proximo_retry=None,
        cookie_expirado=lambda: False,
    )
    base.update(extra)
    return SimpleNamespace(**base)


@asynccontextmanager
async def _client_falso(_cookies):
    yield object()


def _preparar_servico(monkeypatch, sessao, baixar, viva: str | None = URL_VIVA):
    async def url(*_a, **_k):
        return URL_DOC, URL_CPO

    async def ativa(*_a, **_k):
        return sessao

    async def localizar(*_a, **_k):
        return viva

    monkeypatch.setattr(servico, "_url_do_documento", url)
    monkeypatch.setattr(servico, "_sessao_ativa", ativa)
    monkeypatch.setattr(servico, "_cookies_da_sessao", lambda _s: {"JSESSIONID": "x"})
    monkeypatch.setattr(servico, "montar_client", _client_falso)
    monkeypatch.setattr(servico, "localizar_url_documento", localizar)
    monkeypatch.setattr(servico, "baixar_documento", baixar)


@pytest.mark.asyncio
async def test_consulta_do_documento_filtra_processo_e_usuario():
    db = _DbFalso((URL_DOC, URL_CPO))
    url, ficha = await servico._url_do_documento(db, uuid4(), uuid4(), uuid4())

    assert url == URL_DOC
    assert ficha == URL_CPO
    sql = db.consultas[0]
    assert "processos.user_id" in sql
    assert "processos.url_cpo" in sql
    assert "movimentacoes.processo_id" in sql
    assert "movimentacoes.id" in sql


@pytest.mark.asyncio
async def test_sem_url_publica_e_nao_encontrado():
    casos = [
        None,
        (None, URL_CPO),
        ("https://outro-host.com/x.pdf", URL_CPO),
        (URL_DOC, None),
        (URL_DOC, "https://outro-host.com/show.do"),
    ]
    for valor in casos:
        with pytest.raises(servico.DocumentoNaoEncontradoError):
            await servico._url_do_documento(_DbFalso(valor), uuid4(), uuid4(), uuid4())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sessao",
    [
        None,
        _sessao(cookie_encrypted=None),
        _sessao(status=SESSION_STATUS_BLOQUEADO),
        _sessao(cookie_expirado=lambda: True),
    ],
)
async def test_sem_sessao_ativa_pede_reconexao(sessao):
    with pytest.raises(servico.SessaoEsajIndisponivelError):
        await servico._sessao_ativa(_DbFalso(sessao), uuid4())


@pytest.mark.asyncio
async def test_devolve_os_bytes_do_pdf(monkeypatch):
    chamadas = []

    async def baixar(_client, url, **_k):
        chamadas.append(url)
        return PDF

    _preparar_servico(monkeypatch, _sessao(), baixar)
    assert await servico.baixar_pdf_da_movimentacao(_DbFalso(None), uuid4(), uuid4(), uuid4()) == PDF
    assert chamadas == [URL_VIVA]


@pytest.mark.asyncio
async def test_sem_link_vivo_nao_baixa(monkeypatch):
    chamadas: list[str] = []

    async def baixar(_client, url, **_k):
        chamadas.append(url)
        return PDF

    _preparar_servico(monkeypatch, _sessao(), baixar, viva=None)
    with pytest.raises(servico.DocumentoSemPdfError):
        await servico.baixar_pdf_da_movimentacao(_DbFalso(None), uuid4(), uuid4(), uuid4())
    assert chamadas == []


@pytest.mark.asyncio
async def test_login_do_portal_vira_sessao_indisponivel_sem_apagar_cookie(monkeypatch):
    async def baixar(*_a, **_k):
        raise EsajSessaoInvalidaError("redirecionado_para_login")

    sessao = _sessao()
    _preparar_servico(monkeypatch, sessao, baixar)
    with pytest.raises(servico.SessaoEsajIndisponivelError):
        await servico.baixar_pdf_da_movimentacao(_DbFalso(None), uuid4(), uuid4(), uuid4())
    assert sessao.cookie_encrypted == b"x"
    assert sessao.status == SESSION_STATUS_ATIVO


@pytest.mark.asyncio
async def test_429_nao_bloqueia_a_coleta(monkeypatch):
    async def baixar(*_a, **_k):
        raise EsajRateLimitError("status_429")

    sessao = _sessao()
    db = _DbFalso(None)
    _preparar_servico(monkeypatch, sessao, baixar)
    with pytest.raises(servico.PortalLimitandoError):
        await servico.baixar_pdf_da_movimentacao(db, uuid4(), uuid4(), uuid4())
    assert sessao.status == SESSION_STATUS_ATIVO
    assert sessao.tentativas_falha == 0
    assert sessao.cookie_encrypted == b"x"
    assert db.commits == 0


@pytest.mark.asyncio
async def test_resposta_sem_pdf_vira_documento_sem_pdf(monkeypatch):
    async def baixar(*_a, **_k):
        raise EsajDocumentoNaoPdfError("sem_pdf")

    _preparar_servico(monkeypatch, _sessao(), baixar)
    with pytest.raises(servico.DocumentoSemPdfError):
        await servico.baixar_pdf_da_movimentacao(_DbFalso(None), uuid4(), uuid4(), uuid4())


async def _chamar(monkeypatch, resultado):
    async def fake(*_a, **_k):
        if isinstance(resultado, Exception):
            raise resultado
        return resultado

    monkeypatch.setattr("app.api.documento_movimentacao.baixar_pdf_da_movimentacao", fake)
    limiter.enabled = False
    app.dependency_overrides[get_db] = _db_dummy
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4())
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(f"/processos/{uuid4()}/movimentacoes/{uuid4()}/documento")
    finally:
        app.dependency_overrides.clear()
        limiter.enabled = True


@pytest.mark.asyncio
async def test_rota_devolve_pdf_sem_cache_e_sem_cookie(monkeypatch):
    resposta = await _chamar(monkeypatch, PDF)

    assert resposta.status_code == 200
    assert resposta.content == PDF
    assert resposta.headers["content-type"] == "application/pdf"
    assert "no-store" in resposta.headers["cache-control"]
    assert resposta.headers["content-disposition"].startswith("inline")
    assert "set-cookie" not in resposta.headers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("erro", "codigo"),
    [
        (servico.DocumentoNaoEncontradoError(), 404),
        (servico.SessaoEsajIndisponivelError(), 409),
        (servico.PortalLimitandoError(), 429),
        (servico.DocumentoSemPdfError(), 422),
        (servico.PortalForaDoArError(), 502),
    ],
)
async def test_rota_mapeia_erros_sem_vazar_detalhe(monkeypatch, erro, codigo):
    resposta = await _chamar(monkeypatch, erro)

    assert resposta.status_code == codigo
    corpo = resposta.text
    assert "esaj.tjsp.jus.br" not in corpo
    assert "cdDocumento" not in corpo


@pytest.mark.asyncio
async def test_rota_exige_autenticacao():
    limiter.enabled = False
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resposta = await client.get(f"/processos/{uuid4()}/movimentacoes/{uuid4()}/documento")
    finally:
        limiter.enabled = True
    assert resposta.status_code in (401, 403)
