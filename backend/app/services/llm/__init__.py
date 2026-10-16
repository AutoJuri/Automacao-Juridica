"""Adapter de LLM da elaboração (ADR-016).

Ninguém fora deste pacote sabe qual provedor está ativo — o resto do
produto só vê `LLMProvider`. Trocar de `stub` para `anthropic` ou
`openrouter` é variável de ambiente (`LLM_PROVIDER`), nunca um `if`
espalhado pela feature.
"""

from app.services.llm.base import LLMProvider
from app.services.llm.contexto import ElaboracaoContexto
from app.services.llm.factory import get_llm_provider

__all__ = ["ElaboracaoContexto", "LLMProvider", "get_llm_provider"]
