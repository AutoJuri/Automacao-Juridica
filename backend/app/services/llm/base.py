"""Interface que todo provedor de LLM da elaboração implementa."""

from abc import ABC, abstractmethod

from app.services.llm.contexto import ElaboracaoContexto, SinaisSugestaoPeca, SugestaoPeca


class LLMLimiteAtingidoError(Exception):
    """O provedor recusou a chamada por cota (HTTP 429).

    A geração não aconteceu — não há texto novo para gravar.
    """


class LLMProvider(ABC):
    """Nunca chamado do frontend — sempre atrás do FastAPI (ADR-016 §4)."""

    #: Nome curto salvo em `ElaboracaoVersao.llm_provider` (auditoria, não é segredo).
    nome: str

    @abstractmethod
    async def gerar_minuta(self, contexto: ElaboracaoContexto) -> str:
        """Primeiro rascunho (HTML) a partir do pacote da elaboração."""

    @abstractmethod
    async def editar_minuta(
        self,
        *,
        html_atual: str,
        instrucao: str,
        trecho_selecionado: str | None,
    ) -> str:
        """Edita a minuta já gerada — chat (`trecho_selecionado=None`) ou grifo."""

    @abstractmethod
    async def sugerir_peca(self, sinais: SinaisSugestaoPeca) -> SugestaoPeca | None:
        """Sugere uma peça do catálogo a partir de sinais do processo (ADR-016
        Fase 1). `None` quando não há sinal suficiente — o select do frontend
        continua livre e cai no valor padrão."""

    @abstractmethod
    async def extrair_perfil_estilo(self, *, texto_amostra: str) -> str:
        """Extrai um "perfil de estilo" (JSON serializado como string) a partir
        do texto de um modelo de peça (ADR-016 Fase 3). Alimenta
        `ElaboracaoContexto.estilo_perfil`."""
