"""Provider OpenRouter — uma chave, vários modelos (teste e produção).

API compatível com chat completions em `https://openrouter.ai/api/v1`.
`LLM_PROVIDER=openrouter` sem `OPENROUTER_API_KEY` levanta
`LLMProviderNaoConfiguradoError` no primeiro uso, nunca cai para o stub.

Modelo padrão de teste (quando `LLM_MODEL` está vazio):
`qwen/qwen3.8-27b:free`. Fora de `APP_ENV=development` um id que termina
em `:free` é recusado antes do HTTP — a rota grátis pode reter o prompt.
Modelo pago depois é só trocar `LLM_MODEL`.

Não enviamos `provider.data_collection=deny`: com isso ligado, o catálogo
grátis costuma responder 404. A conta do OpenRouter deve manter desligados
o log de prompt e o uso de inputs para melhorar o produto.
"""

import json
import logging

import httpx

from app.core.config import get_settings
from app.services.elaboracao_pecas import PECAS_CATALOGO, PECAS_IDS_VALIDOS
from app.services.llm.base import LLMLimiteAtingidoError, LLMProvider
from app.services.llm.contexto import ElaboracaoContexto, SinaisSugestaoPeca, SugestaoPeca

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Slug oficial da página do modelo no OpenRouter (rota grátis de teste).
DEFAULT_MODEL = "qwen/qwen3.8-27b:free"
TIMEOUT_SEGUNDOS = 60.0

_SISTEMA_GERAR = (
    "Você é um assistente de redação jurídica que ajuda um advogado brasileiro a "
    "elaborar o RASCUNHO de uma peça processual. Responda apenas com HTML simples "
    "usando <p>, <strong>, <em> — sem <html>/<body>, sem cerca de código. Nunca "
    "invente jurisprudência, número de processo, nome de parte ou fato que não "
    "esteja no contexto enviado. Se um dado não foi informado, escreva "
    "'[a completar]' em vez de inventar. Se houver um perfil de estilo em JSON, "
    "siga o tom descrito sem copiar trechos longos do modelo original."
)

_SISTEMA_EDITAR = (
    "Você edita uma minuta jurídica em HTML já existente, a partir de uma instrução "
    "do advogado. Responda apenas com o HTML completo da minuta revisada (mesmas "
    "regras: <p>, <strong>, <em>, sem <html>/<body>, sem cerca de código, nunca "
    "inventar jurisprudência ou fato novo). Se `trecho_selecionado` for informado, "
    "a edição deve se concentrar nesse trecho; o resto do documento deve permanecer igual."
)

_SISTEMA_SUGERIR_PECA = (
    "Você sugere qual peça processual um advogado brasileiro deve redigir a "
    "seguir, com base em sinais do processo (classe, assunto, título da última "
    "intimação/movimentação). Responda APENAS com um JSON de uma linha no "
    'formato {"peca": "<id>", "explicacao": "<frase curta em português>"}, '
    "sem cerca de código. O campo peca DEVE ser exatamente um dos ids da lista "
    "fornecida — nunca invente um id novo. Se nenhum sinal for suficiente, "
    'responda {"peca": null, "explicacao": null}.'
)

_SISTEMA_ESTILO = (
    "Você analisa o texto de uma peça processual em português e devolve um "
    "perfil de estilo em JSON de uma linha, com campos curtos e objetivos "
    "(ex.: tom, uso de conectivos, tamanho médio de frase, formalidade). "
    "Responda APENAS com o JSON, sem cerca de código e sem comentário fora dele. "
    "Nunca reproduza trechos longos do texto original no JSON."
)


class LLMProviderNaoConfiguradoError(Exception):
    """OpenRouter sem chave, ou modelo `:free` fora de development."""


# Um aviso por processo: development pode usar `:free`, mas o log não
# repete a cada Elaborar.
_aviso_modelo_free_emitido = False


class OpenRouterRespostaInvalidaError(Exception):
    """A API respondeu sem o texto da conclusão (choices[0].message.content)."""


def _sem_cerca(texto: str) -> str:
    """Modelos grátis às vezes embrulham HTML/JSON em ``` ... ```."""
    texto = texto.strip()
    if not texto.startswith("```"):
        return texto
    linhas = texto.splitlines()
    if linhas and linhas[0].startswith("```"):
        linhas = linhas[1:]
    if linhas and linhas[-1].strip() == "```":
        linhas = linhas[:-1]
    return "\n".join(linhas).strip()


class OpenRouterProvider(LLMProvider):
    nome = "openrouter"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openrouter_api_key:
            raise LLMProviderNaoConfiguradoError(
                "OPENROUTER_API_KEY vazio — crie a chave em https://openrouter.ai/keys "
                "antes de usar LLM_PROVIDER=openrouter."
            )
        self._api_key = settings.openrouter_api_key
        self._model = settings.llm_model.strip() or DEFAULT_MODEL
        self._max_tokens = settings.llm_max_output_tokens

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            # Opcional no OpenRouter; não é segredo e não identifica o advogado.
            "X-OpenRouter-Title": "Automacao Juridica",
        }

    def _garantir_modelo_permitido(self) -> None:
        """`:free` só em development. Fora disso, nenhum prompt sai do processo."""
        global _aviso_modelo_free_emitido
        if not self._model.endswith(":free"):
            return
        if get_settings().is_development:
            if not _aviso_modelo_free_emitido:
                _aviso_modelo_free_emitido = True
                logger.warning(
                    "OpenRouter em development usando modelo gratuito (%s). "
                    "Fora de development essa rota é recusada.",
                    self._model,
                )
            return
        raise LLMProviderNaoConfiguradoError(
            "Modelo gratuito do OpenRouter só é permitido em development."
        )

    async def _completar(self, *, sistema: str, mensagem_usuario: str) -> str:
        self._garantir_modelo_permitido()
        payload = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            # Qwen gasta o teto de saída no raciocínio interno e devolve
            # `content` vazio (HTTP 200). Sem raciocínio, os tokens vão
            # para o texto da peça.
            "reasoning": {"effort": "none"},
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": mensagem_usuario},
            ],
        }
        async with httpx.AsyncClient(timeout=TIMEOUT_SEGUNDOS) as client:
            resposta = await client.post(
                OPENROUTER_API_URL, headers=self._headers(), json=payload
            )
        if resposta.status_code == 429:
            # Cota da rota (modelo grátis, em geral). O modelo não devolveu texto.
            raise LLMLimiteAtingidoError("OpenRouter recusou a chamada (429).")
        resposta.raise_for_status()
        corpo = resposta.json()
        escolhas = corpo.get("choices") or []
        if not escolhas:
            raise OpenRouterRespostaInvalidaError("Resposta sem choices")
        mensagem = escolhas[0].get("message") or {}
        conteudo = mensagem.get("content")
        if isinstance(conteudo, list):
            textos = [
                parte.get("text", "")
                for parte in conteudo
                if isinstance(parte, dict) and parte.get("type") == "text"
            ]
            conteudo = "".join(textos)
        if not isinstance(conteudo, str) or not conteudo.strip():
            raise OpenRouterRespostaInvalidaError("Resposta sem content")
        return _sem_cerca(conteudo)

    async def gerar_minuta(self, contexto: ElaboracaoContexto) -> str:
        f = contexto.ficha
        mensagem = (
            f"Peça a redigir: {contexto.peca}\n"
            f"Processo: {f.cnj or 'não informado'}\n"
            f"Classe: {f.classe or 'não informado'}\n"
            f"Assunto: {f.assunto or 'não informado'}\n"
            f"Autor: {f.autor or 'não informado'}\n"
            f"Réu: {f.reu or 'não informado'}\n"
            f"Foro/Vara: {f.foro or ''} {f.vara or ''}\n"
            f"Juiz: {f.juiz or 'não informado'}\n"
            f"Valor da causa: {f.valor_causa or 'não informado'}\n"
            f"Endereçamento: {f.enderecamento}\n"
            f"Fatos extras informados pelo advogado: {contexto.fatos_extras or 'nenhum'}\n"
            f"Perfil de estilo (JSON) desta sessão: {contexto.estilo_perfil or 'nenhum'}\n"
        )
        return await self._completar(sistema=_SISTEMA_GERAR, mensagem_usuario=mensagem)

    async def editar_minuta(
        self,
        *,
        html_atual: str,
        instrucao: str,
        trecho_selecionado: str | None,
    ) -> str:
        mensagem = (
            f"Instrução do advogado: {instrucao}\n"
            f"Trecho selecionado (grifo): {trecho_selecionado or '(nenhum — edição no documento todo)'}\n"
            f"HTML atual da minuta:\n{html_atual}"
        )
        return await self._completar(sistema=_SISTEMA_EDITAR, mensagem_usuario=mensagem)

    async def sugerir_peca(self, sinais: SinaisSugestaoPeca) -> SugestaoPeca | None:
        catalogo = ", ".join(f"{p.id} ({p.nome})" for p in PECAS_CATALOGO)
        mensagem = (
            f"Peças disponíveis: {catalogo}\n"
            f"Classe: {sinais.classe or 'não informado'}\n"
            f"Assunto: {sinais.assunto or 'não informado'}\n"
            f"Título da última intimação: {sinais.ultima_intimacao_titulo or 'não informado'}\n"
            f"Título da última movimentação: {sinais.ultima_movimentacao_titulo or 'não informado'}\n"
        )
        resposta = await self._completar(sistema=_SISTEMA_SUGERIR_PECA, mensagem_usuario=mensagem)
        try:
            corpo = json.loads(_sem_cerca(resposta))
        except (json.JSONDecodeError, TypeError):
            return None
        peca_id = corpo.get("peca") if isinstance(corpo, dict) else None
        explicacao = corpo.get("explicacao") if isinstance(corpo, dict) else None
        if not isinstance(peca_id, str) or peca_id not in PECAS_IDS_VALIDOS:
            return None
        return SugestaoPeca(peca=peca_id, explicacao=explicacao or "")

    async def extrair_perfil_estilo(self, *, texto_amostra: str) -> str:
        mensagem = f"Texto do modelo de peça:\n{texto_amostra}"
        return await self._completar(sistema=_SISTEMA_ESTILO, mensagem_usuario=mensagem)
