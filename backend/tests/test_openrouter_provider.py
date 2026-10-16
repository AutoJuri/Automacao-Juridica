"""OpenRouter (ADR-016) — sem rede.

Confere a chave obrigatória, o slug padrão do Qwen grátis e o formato
da chamada (Bearer + chat completions). A resposta é um transporte falso.
"""

import json
from types import SimpleNamespace

import httpx
import pytest

from app.services.llm.contexto import ElaboracaoContexto, FichaProcessoContexto, SinaisSugestaoPeca
from app.services.llm.factory import LLMProviderDesconhecidoError, get_llm_provider
from app.services.llm.base import LLMLimiteAtingidoError
from app.services.llm.openrouter_provider import (
    DEFAULT_MODEL,
    OPENROUTER_API_URL,
    LLMProviderNaoConfiguradoError,
    OpenRouterProvider,
)


def _settings(
    *, chave: str = "sk-or-teste", modelo: str = "", development: bool = True
) -> SimpleNamespace:
    return SimpleNamespace(
        openrouter_api_key=chave,
        llm_model=modelo,
        llm_max_output_tokens=4000,
        llm_provider="openrouter",
        is_development=development,
    )


def _ficha() -> FichaProcessoContexto:
    return FichaProcessoContexto(
        cnj=None,
        classe=None,
        assunto=None,
        autor=None,
        reu=None,
        foro=None,
        vara=None,
        juiz=None,
        valor_causa=None,
        enderecamento="EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO",
    )


class _ClienteFalso:
    """Substitui `httpx.AsyncClient` e guarda o último POST."""

    ultimo: dict | None = None
    conteudo: str = "<p>Rascunho</p>"
    status: int = 200

    def __init__(self, *args, **kwargs) -> None:
        self.timeout = kwargs.get("timeout")

    async def __aenter__(self) -> "_ClienteFalso":
        return self

    async def __aexit__(self, *args) -> None:
        return None

    async def post(self, url: str, *, headers: dict, json: dict) -> httpx.Response:
        _ClienteFalso.ultimo = {"url": url, "headers": headers, "json": json}
        pedido = httpx.Request("POST", url)
        if self.status != 200:
            return httpx.Response(self.status, json={"error": {"message": "falha"}}, request=pedido)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": self.conteudo}}]},
            request=pedido,
        )


@pytest.fixture
def cliente_falso(monkeypatch):
    _ClienteFalso.ultimo = None
    _ClienteFalso.conteudo = "<p>Rascunho</p>"
    _ClienteFalso.status = 200
    monkeypatch.setattr(
        "app.services.llm.openrouter_provider.get_settings",
        lambda: _settings(),
    )
    monkeypatch.setattr("app.services.llm.openrouter_provider.httpx.AsyncClient", _ClienteFalso)
    return _ClienteFalso


class TestOpenRouterProvider:
    def test_sem_chave_nao_cai_para_o_stub(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.llm.openrouter_provider.get_settings",
            lambda: _settings(chave=""),
        )
        with pytest.raises(LLMProviderNaoConfiguradoError):
            OpenRouterProvider()

    def test_modelo_vazio_usa_o_qwen_gratis(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.llm.openrouter_provider.get_settings",
            lambda: _settings(modelo=""),
        )
        assert OpenRouterProvider()._model == DEFAULT_MODEL

    def test_modelo_explicito_vence_o_padrao(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.llm.openrouter_provider.get_settings",
            lambda: _settings(modelo="anthropic/claude-sonnet-4.5"),
        )
        assert OpenRouterProvider()._model == "anthropic/claude-sonnet-4.5"

    @pytest.mark.asyncio
    async def test_modelo_free_fora_de_development_nao_chama_http(self, cliente_falso, monkeypatch):
        monkeypatch.setattr(
            "app.services.llm.openrouter_provider.get_settings",
            lambda: _settings(development=False),
        )

        with pytest.raises(LLMProviderNaoConfiguradoError):
            await OpenRouterProvider().gerar_minuta(
                ElaboracaoContexto(ficha=_ficha(), peca="contestacao")
            )

        assert cliente_falso.ultimo is None

    @pytest.mark.asyncio
    async def test_gerar_minuta_manda_bearer_modelo_e_estilo(self, cliente_falso):
        contexto = ElaboracaoContexto(
            ficha=_ficha(),
            peca="contestacao",
            fatos_extras="Fato inventado.",
            estilo_perfil='{"tom": "formal"}',
        )

        html = await OpenRouterProvider().gerar_minuta(contexto)

        assert html == "<p>Rascunho</p>"
        pedido = cliente_falso.ultimo
        assert pedido["url"] == OPENROUTER_API_URL
        assert pedido["headers"]["Authorization"] == "Bearer sk-or-teste"
        assert pedido["json"]["model"] == DEFAULT_MODEL
        assert pedido["json"]["max_tokens"] == 4000
        assert pedido["json"]["reasoning"] == {"effort": "none"}
        usuario = pedido["json"]["messages"][1]["content"]
        assert "Fato inventado." in usuario
        assert '{"tom": "formal"}' in usuario
        assert "sk-or-teste" not in usuario

    @pytest.mark.asyncio
    async def test_tira_cerca_de_codigo_da_resposta(self, cliente_falso):
        cliente_falso.conteudo = "```html\n<p>Dentro da cerca</p>\n```"
        html = await OpenRouterProvider().gerar_minuta(
            ElaboracaoContexto(ficha=_ficha(), peca="contestacao")
        )
        assert html == "<p>Dentro da cerca</p>"

    @pytest.mark.asyncio
    async def test_sugerir_peca_rejeita_id_fora_do_catalogo(self, cliente_falso):
        cliente_falso.conteudo = json.dumps(
            {"peca": "habeas_corpus", "explicacao": "inventado"}
        )
        sinais = SinaisSugestaoPeca(
            classe=None,
            assunto=None,
            ultima_intimacao_titulo="Citação",
            ultima_movimentacao_titulo=None,
        )
        assert await OpenRouterProvider().sugerir_peca(sinais) is None

    @pytest.mark.asyncio
    async def test_429_nao_trata_como_texto_gerado(self, cliente_falso):
        cliente_falso.status = 429

        with pytest.raises(LLMLimiteAtingidoError):
            await OpenRouterProvider().gerar_minuta(
                ElaboracaoContexto(ficha=_ficha(), peca="contestacao")
            )

    def test_factory_devolve_openrouter(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.llm.factory.get_settings",
            lambda: SimpleNamespace(llm_provider="openrouter"),
        )
        monkeypatch.setattr(
            "app.services.llm.openrouter_provider.get_settings",
            lambda: _settings(),
        )
        provider = get_llm_provider()
        assert provider.nome == "openrouter"

    def test_factory_rejeita_provider_desconhecido(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.llm.factory.get_settings",
            lambda: SimpleNamespace(llm_provider="gemini"),
        )
        with pytest.raises(LLMProviderDesconhecidoError):
            get_llm_provider()
