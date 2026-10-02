"""Escolhe o provider ativo a partir de `Settings.llm_provider`."""

from app.core.config import get_settings
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.base import LLMProvider
from app.services.llm.openrouter_provider import OpenRouterProvider
from app.services.llm.stub_provider import StubLLMProvider


class LLMProviderDesconhecidoError(Exception):
    """`LLM_PROVIDER` não é nenhum dos nomes suportados."""


def get_llm_provider() -> LLMProvider:
    provider = get_settings().llm_provider.strip().lower()
    if provider == "stub":
        return StubLLMProvider()
    if provider == "anthropic":
        return AnthropicProvider()
    if provider == "openrouter":
        return OpenRouterProvider()
    raise LLMProviderDesconhecidoError(
        f"LLM_PROVIDER={provider!r} não é suportado (use 'stub', 'anthropic' ou 'openrouter')."
    )
