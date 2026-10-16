"""Pacote de contexto enviado ao LLM (ADR-016 §1).

Fatos do processo vão em campos estruturados, nunca como blob de HTML/CPO
cru — quem monta isso é `app.services.elaboracao_prompt`, nunca o
provider. O provider só recebe o que precisa para redigir, nada de CPF,
senha, cookie do e-SAJ ou token OAuth2 (isso nunca entra aqui).
"""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class FichaProcessoContexto:
    """Subconjunto público da ficha — só o que ajuda a redigir a peça."""

    cnj: str | None
    classe: str | None
    assunto: str | None
    autor: str | None
    reu: str | None
    foro: str | None
    vara: str | None
    juiz: str | None
    valor_causa: str | None
    enderecamento: str


@dataclass(frozen=True, slots=True)
class ElaboracaoContexto:
    """Pacote completo passado a `LLMProvider.gerar_minuta`.

    `jurisprudencia_marcada` e `anexos_descricao` ficam previstos aqui para
    as Fases 5/6 do ADR-016, mas chegam sempre vazios nesta etapa — ninguém
    ainda alimenta esses campos.
    """

    ficha: FichaProcessoContexto
    peca: str
    fatos_extras: str | None = None
    estilo_perfil: str | None = None
    jurisprudencia_marcada: tuple[str, ...] = field(default_factory=tuple)
    anexos_descricao: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SinaisSugestaoPeca:
    """Pacote enviado a `LLMProvider.sugerir_peca` (ADR-016 Fase 1).

    Só sinais públicos do processo — nunca CPF, senha, cookie ou token
    OAuth2. O select do frontend continua livre; isto é só um palpite.
    """

    classe: str | None
    assunto: str | None
    ultima_intimacao_titulo: str | None
    ultima_movimentacao_titulo: str | None


@dataclass(frozen=True, slots=True)
class SugestaoPeca:
    """Resposta de `LLMProvider.sugerir_peca` — `peca` é sempre um id do
    catálogo (`app.services.elaboracao_pecas.PECAS_IDS_VALIDOS`)."""

    peca: str
    explicacao: str
