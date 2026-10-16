"""Monta o "pacote" da elaboração (ADR-016 §1) a partir da ficha real.

Só usa o que já está no banco (`Processo`) — nunca chama e-SAJ, Playwright
ou DataJud daqui. Fatos extras chegam já descriptografados (em memória, só
para esta chamada) por quem invoca — este módulo não sabe de cifra.
"""

from app.models.processo import Processo
from app.services.llm.contexto import ElaboracaoContexto, FichaProcessoContexto


def _nome_parte(parte: dict | None) -> str | None:
    if not parte:
        return None
    nome = parte.get("nome") or parte.get("nomeSocial")
    return nome if isinstance(nome, str) and nome.strip() else None


def montar_enderecamento(processo: Processo) -> str:
    """Mesma regra de `frontend/src/features/elaboracao/elaboracao.processo.ts`
    (`montarEnderecamento`) — mantém consistência entre o que o advogado viu
    antes de clicar Elaborar e o que o LLM recebe."""
    vara = (processo.vara or "").strip()
    foro = (processo.foro or "").strip()
    if vara and foro:
        return f"EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA {vara.upper()} DO {foro.upper()}"
    if vara:
        return f"EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA {vara.upper()}"
    if foro:
        return f"EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DO {foro.upper()}"
    return "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO"


def montar_ficha_contexto(processo: Processo) -> FichaProcessoContexto:
    return FichaProcessoContexto(
        cnj=processo.nu_processo,
        classe=processo.de_classe,
        assunto=processo.de_assunto,
        autor=_nome_parte(processo.parte_ativa),
        reu=_nome_parte(processo.parte_passiva),
        foro=processo.foro,
        vara=processo.vara,
        juiz=processo.juiz,
        valor_causa=processo.valor_acao,
        enderecamento=montar_enderecamento(processo),
    )


def montar_contexto_elaboracao(
    processo: Processo,
    *,
    peca: str,
    fatos_extras: str | None,
    estilo_perfil: str | None = None,
) -> ElaboracaoContexto:
    """Pacote completo passado ao provider — anexos e jurisprudência marcada
    (Fases 5/6 do ADR-016) ainda chegam vazios, esta etapa cobre Fases 2, 3 e 4."""
    return ElaboracaoContexto(
        ficha=montar_ficha_contexto(processo),
        peca=peca,
        fatos_extras=fatos_extras,
        estilo_perfil=estilo_perfil,
    )
