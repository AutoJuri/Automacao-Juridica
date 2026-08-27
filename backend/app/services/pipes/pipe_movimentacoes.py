"""PIPE E — histórico de movimentações via HTML do CPO (`cpopg/show.do`).

Diferente dos outros pipes (uma chamada JSON por advogado), aqui é uma
chamada HTML **por processo** — mais caro, por isso o chamador já manda uma
lista pequena e pré-filtrada pelo throttle (ver `coleta_esaj._selecionar_lote_movimentacoes`,
coluna `Processo.movimentacoes_synced_at`, ADR-012).

`EsajPortalIndisponivelError` num processo não aborta os demais — só aquele
processo fica sem atualização neste ciclo (item ausente no resultado).
`EsajSessaoInvalidaError` / `EsajRateLimitError` sobem para o chamador: a
sessão toda ficou ruim, não é um problema de um processo isolado.
"""

import logging

import httpx

from app.schemas.esaj_cpo_raw import CpoDetalheRaw
from app.services.esaj_cpo_parser import parsear_cpo_html, url_cpo_publica
from app.services.esaj_http import ESAJ_BASE_URL, EsajPortalIndisponivelError, buscar_html

logger = logging.getLogger(__name__)

REFERER = f"{ESAJ_BASE_URL}/tarefas-adv/processos"

# Cada fetch é uma página HTML inteira (bem mais pesada que os GETs JSON) e
# o ciclo tem orçamento de 60s por advogado (`TIMEOUT_CICLO_SEGUNDOS`) — só
# um lote pequeno por ciclo, com round-robin entre ciclos.
MOVIMENTACOES_LOTE = 5


async def coletar(
    client: httpx.AsyncClient, processos: list[tuple[str, str]]
) -> dict[str, CpoDetalheRaw]:
    """`processos` é `[(cd_processo, url_cpo), ...]`, já filtrado e limitado
    pelo chamador. Devolve só os que tiveram fetch bem sucedido — um
    `cd_processo` ausente no resultado significa "sem atualização neste
    ciclo", não falha do lote inteiro.
    """
    resultado: dict[str, CpoDetalheRaw] = {}
    for cd_processo, url_cpo in processos:
        url_segura = url_cpo_publica(url_cpo)
        if url_segura is None:
            logger.info("Falha ao buscar CPO de um processo (causa=url_cpo_invalida)")
            continue
        try:
            html = await buscar_html(client, url_segura, referer=REFERER)
        except EsajPortalIndisponivelError as exc:
            logger.info("Falha ao buscar CPO de um processo (causa=%s)", type(exc).__name__)
            continue
        resultado[cd_processo] = parsear_cpo_html(html)
    return resultado
