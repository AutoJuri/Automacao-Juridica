"""Provider sem rede — testa a canaleta completa antes de existir uma chave.

Não é um "modelo pequeno": é uma função determinística que devolve HTML
plausível a partir do contexto, sempre com um aviso visível de que é modo
de teste. Serve para validar Elaborar → chat → grifo → nova versão de
ponta a ponta (frontend, endpoints, cifra, histórico) sem gastar tokens
nem exigir uma conta em provedor real.

`sugerir_peca` (Fase 1) e `extrair_perfil_estilo` (Fase 3) seguem o mesmo
espírito: nunca chamam rede, sempre deixam claro que é heurística/estatística
de teste — não é "IA de verdade" até `LLM_PROVIDER=anthropic` com chave.
"""

import json
from html import escape

from app.services.llm.base import LLMProvider
from app.services.llm.contexto import ElaboracaoContexto, SinaisSugestaoPeca, SugestaoPeca
from app.services.elaboracao_pecas import PECAS_CATALOGO

AVISO_MODO_TESTE = (
    "<p><strong>Rascunho de teste.</strong> "
    "A IA ainda não está conectada a um provedor real "
    "(LLM_PROVIDER=stub). Nenhum texto jurídico aqui foi redigido por um "
    "modelo de linguagem.</p>"
)


def _p(texto: str) -> str:
    return f"<p>{texto}</p>"


class StubLLMProvider(LLMProvider):
    nome = "stub"

    async def gerar_minuta(self, contexto: ElaboracaoContexto) -> str:
        f = contexto.ficha
        e = escape
        fatos = (
            _p(e(contexto.fatos_extras.strip()))
            if contexto.fatos_extras and contexto.fatos_extras.strip()
            else _p("Nenhum fato extra foi informado nesta sessão.")
        )
        estilo = (
            _p(
                "<em><strong>Perfil de estilo aplicado (modo stub).</strong> "
                "Não é análise real, só prova de que o pacote chegou até aqui.</em>"
            )
            if contexto.estilo_perfil and contexto.estilo_perfil.strip()
            else ""
        )

        partes = [
            AVISO_MODO_TESTE,
            f"<p><strong>{e(f.enderecamento)}</strong></p>",
            "<p></p>",
            _p(f"Processo nº: {e(f.cnj or 'Não disponível')}"),
            _p(f"Classe: {e(f.classe or 'Não disponível')}"),
            _p(f"Assunto: {e(f.assunto or 'Não disponível')}"),
            _p(f"Autor: {e(f.autor or 'Não disponível')}"),
            _p(f"Réu: {e(f.reu or 'Não disponível')}"),
            estilo,
            "<p></p>",
            _p(f"<strong>{e(contexto.peca.upper())}</strong>"),
            "<p></p>",
            _p("<strong>I. DOS FATOS</strong>"),
            fatos,
            "<p></p>",
            _p("<strong>II. DO DIREITO</strong>"),
            _p(
                "Fundamentação jurídica de teste — o modo stub nunca cita "
                "jurisprudência real (ADR-016 §3). Conecte um provedor real "
                "para gerar o texto de verdade."
            ),
            "<p></p>",
            _p("<strong>III. DOS PEDIDOS</strong>"),
            _p("Pedidos de teste — revise antes de protocolar."),
            "<p></p>",
            _p("Termos em que, pede deferimento."),
        ]
        return "".join(partes)

    async def editar_minuta(
        self,
        *,
        html_atual: str,
        instrucao: str,
        trecho_selecionado: str | None,
    ) -> str:
        instrucao_html = escape(instrucao.strip())

        if trecho_selecionado and trecho_selecionado.strip():
            trecho = trecho_selecionado.strip()
            anotacao = (
                f"<strong>{escape(trecho)}</strong>"
                f"<em> [grifo — teste: {instrucao_html}]</em>"
            )
            if trecho in html_atual:
                return html_atual.replace(trecho, anotacao, 1)
            # Trecho não casou (ex.: marcação HTML no meio) — não inventa
            # edição no corpo; deixa registrado ao final, visível na revisão.
            nota = _p(
                f"<em>[grifo — teste: instrução \"{instrucao_html}\" "
                f'recebida para o trecho "{escape(trecho[:120])}", '
                "mas o modo stub não localizou o texto exato para substituir]</em>"
            )
            return html_atual + nota

        nota = _p(
            f"<em>[chat — teste: instrução recebida — \"{instrucao_html}\"]</em>"
        )
        return html_atual + nota

    async def sugerir_peca(self, sinais: SinaisSugestaoPeca) -> SugestaoPeca | None:
        campos = (
            sinais.ultima_intimacao_titulo,
            sinais.ultima_movimentacao_titulo,
            sinais.assunto,
            sinais.classe,
        )
        texto_busca = " ".join(campo for campo in campos if campo).lower()
        if not texto_busca:
            return None

        for peca in PECAS_CATALOGO:
            for palavra in peca.palavras_chave:
                if palavra in texto_busca:
                    explicacao = (
                        f'Sugestão determinística de teste (LLM_PROVIDER=stub): '
                        f'encontrei "{palavra}" nos dados do processo, associada a '
                        f"{peca.nome}."
                    )
                    return SugestaoPeca(peca=peca.id, explicacao=explicacao)
        return None

    async def extrair_perfil_estilo(self, *, texto_amostra: str) -> str:
        texto = texto_amostra.strip()
        linhas = [linha for linha in texto.splitlines() if linha.strip()]
        palavras = texto.split()
        frases = [f for f in texto.replace("\n", " ").split(".") if f.strip()]
        tamanho_medio_frase = round(len(palavras) / len(frases), 1) if frases else 0.0

        perfil = {
            "modo": "stub",
            "aviso": (
                "Perfil de teste — estatística simples do texto enviado, não é "
                "análise de estilo por um modelo real (LLM_PROVIDER=stub)."
            ),
            "linhas_amostra": len(linhas),
            "palavras_amostra": len(palavras),
            "tamanho_medio_frase_em_palavras": tamanho_medio_frase,
        }
        return json.dumps(perfil, ensure_ascii=False)
