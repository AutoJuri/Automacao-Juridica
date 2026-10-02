"""Catálogo de peças do seletor da elaboração (ADR-016 Fase 1).

Mesmo catálogo do frontend (`frontend/src/features/elaboracao/elaboracao.mock.ts`,
`modelosPeca`) — manter sincronizado manualmente. Não há hoje uma fonte única
compartilhada entre backend e frontend; unificar isso fica para uma iteração
futura. As palavras-chave abaixo só alimentam a heurística determinística do
`StubLLMProvider.sugerir_peca` — um provider real (Anthropic) não depende
delas, só usa a lista de ids válidos para validar a resposta do modelo.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PecaCatalogo:
    id: str
    nome: str
    # Palavras (minúsculas, sem acento não é necessário — comparação já
    # normaliza) que, se aparecerem no título da intimação/movimentação,
    # sugerem esta peça no modo `stub`.
    palavras_chave: tuple[str, ...]


PECAS_CATALOGO: tuple[PecaCatalogo, ...] = (
    PecaCatalogo("contestacao", "Contestação", ("citação", "citacao", "cite-se")),
    PecaCatalogo("replica", "Réplica", ("réplica", "replica", "impugnação à contestação")),
    PecaCatalogo(
        "recurso_inominado",
        "Recurso Inominado",
        ("recurso inominado", "juizado especial"),
    ),
    PecaCatalogo("apelacao", "Apelação", ("sentença", "sentenca", "julgo procedente", "julgo improcedente")),
    PecaCatalogo("agravo_interno", "Agravo Interno", ("agravo interno", "decisão monocrática")),
    PecaCatalogo("memoriais", "Memoriais", ("memoriais", "audiência de instrução")),
    PecaCatalogo("peticao_inicial", "Petição Inicial", ("distribuição", "distribuicao")),
    PecaCatalogo(
        "tutela_urgencia",
        "Tutela de Urgência",
        ("tutela de urgência", "tutela de urgencia", "liminar", "urgência"),
    ),
    PecaCatalogo(
        "impugnacao_contestacao",
        "Impugnação à Contestação",
        ("impugnação à contestação", "impugnacao a contestacao"),
    ),
    PecaCatalogo(
        "embargos_declaracao",
        "Embargos de Declaração",
        ("embargos de declaração", "embargos de declaracao", "omissão", "contradição"),
    ),
)

PECAS_IDS_VALIDOS: frozenset[str] = frozenset(p.id for p in PECAS_CATALOGO)


def nome_peca(peca_id: str) -> str | None:
    for peca in PECAS_CATALOGO:
        if peca.id == peca_id:
            return peca.nome
    return None
