"""Provider real (Claude, produção padrão do ADR-016 §5) — via `httpx`.

Código completo, mas sem chave configurada ainda: `LLM_PROVIDER=anthropic`
sem `ANTHROPIC_API_KEY` levanta `LLMProviderNaoConfiguradoError` no
primeiro uso, nunca silenciosamente cai para o stub. Nenhum dado sensível
do e-SAJ (CPF, senha, cookie, token OAuth2) chega perto deste módulo — o
pacote já vem filtrado por `app.services.elaboracao_prompt`.
"""

import json

import httpx

from app.core.config import get_settings
from app.services.elaboracao_pecas import PECAS_CATALOGO, PECAS_IDS_VALIDOS
from app.services.llm.base import LLMProvider
from app.services.llm.contexto import ElaboracaoContexto, SinaisSugestaoPeca, SugestaoPeca

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-5-20260101"  # ver ADR-016 — confirmar nome oficial ao ligar a chave.
TIMEOUT_SEGUNDOS = 60.0

_SISTEMA_GERAR = (
    "Você é um assistente de redação jurídica que ajuda um advogado brasileiro a "
    "elaborar o RASCUNHO de uma peça processual. Responda apenas com HTML simples "
    "usando <p>, <strong>, <em> — sem <html>/<body>. Nunca invente jurisprudência, "
    "número de processo, nome de parte ou fato que não esteja no contexto enviado. "
    "Se um dado não foi informado, escreva '[a completar]' em vez de inventar. "
    "Se houver um perfil de estilo em JSON, siga o tom descrito sem copiar "
    "trechos longos do modelo original."
)

_SISTEMA_EDITAR = (
    "Você edita uma minuta jurídica em HTML já existente, a partir de uma instrução "
    "do advogado. Responda apenas com o HTML completo da minuta revisada (mesmas "
    "regras: <p>, <strong>, <em>, sem <html>/<body>, nunca inventar jurisprudência ou "
    "fato novo). Se `trecho_selecionado` for informado, a edição deve se concentrar "
    "nesse trecho; o resto do documento deve permanecer igual."
)

_SISTEMA_SUGERIR_PECA = (
    "Você sugere qual peça processual um advogado brasileiro deve redigir a "
    "seguir, com base em sinais do processo (classe, assunto, título da última "
    "intimação/movimentação). Responda APENAS com um JSON de uma linha no "
    'formato {"peca": "<id>", "explicacao": "<frase curta em português>"}. '
    "O campo peca DEVE ser exatamente um dos ids da lista fornecida — nunca "
    "invente um id novo. Se nenhum sinal for suficiente, responda "
    '{"peca": null, "explicacao": null}.'
)

_SISTEMA_ESTILO = (
    "Você analisa o texto de uma peça processual em português e devolve um "
    "perfil de estilo em JSON de uma linha, com campos curtos e objetivos "
    "(ex.: tom, uso de conectivos, tamanho médio de frase, formalidade). "
    "Responda APENAS com o JSON, sem comentário fora dele. Nunca reproduza "
    "trechos longos do texto original no JSON."
)


class LLMProviderNaoConfiguradoError(Exception):
    """`LLM_PROVIDER=anthropic` sem `ANTHROPIC_API_KEY` configurada."""


class AnthropicProvider(LLMProvider):
    nome = "anthropic"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise LLMProviderNaoConfiguradoError(
                "ANTHROPIC_API_KEY vazio — configure a chave antes de usar LLM_PROVIDER=anthropic."
            )
        self._api_key = settings.anthropic_api_key
        self._model = settings.llm_model or DEFAULT_MODEL
        self._max_tokens = settings.llm_max_output_tokens

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self._api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "content-type": "application/json",
        }

    async def _completar(self, *, sistema: str, mensagem_usuario: str) -> str:
        payload = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "system": sistema,
            "messages": [{"role": "user", "content": mensagem_usuario}],
        }
        async with httpx.AsyncClient(timeout=TIMEOUT_SEGUNDOS) as client:
            resposta = await client.post(
                ANTHROPIC_API_URL, headers=self._headers(), json=payload
            )
        resposta.raise_for_status()
        corpo = resposta.json()
        blocos = corpo.get("content") or []
        textos = [bloco.get("text", "") for bloco in blocos if bloco.get("type") == "text"]
        return "".join(textos).strip()

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
            corpo = json.loads(resposta)
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
