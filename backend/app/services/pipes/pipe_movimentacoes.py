"""PIPE E — histórico de movimentações via HTML do CPO (`cpopg/show.do`).

Diferente dos outros pipes (uma chamada JSON por advogado), aqui é uma
chamada HTML **por processo** — mais caro, por isso o chamador já manda uma
lista pequena e pré-filtrada pelo throttle (ver `coleta_esaj._selecionar_lote_movimentacoes`,
coluna `Processo.movimentacoes_synced_at`, ADR-012).

Quando a ficha traz `#btnExibirMovimentacoes` em vez de
`tbody#tabelaTodasMovimentacoes`, as linhas vêm de
`carregarMovimentacoesAjax.do`, paginadas por um cursor opaco. O cursor
não é logado nem gravado.

`EsajPortalIndisponivelError` num processo não aborta os demais — só aquele
processo fica sem atualização neste ciclo (item ausente no resultado).
`EsajSessaoInvalidaError` / `EsajRateLimitError` sobem para o chamador: a
sessão toda ficou ruim, não é um problema de um processo isolado.
"""

import logging
import re
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from app.schemas.esaj_cpo_raw import CpoDetalheRaw, MovimentacaoRaw
from app.services.esaj_cpo_parser import (
    parsear_cpo_html,
    parsear_fragmento_movimentacoes,
    url_cpo_publica,
)
from app.services.esaj_http import (
    ESAJ_BASE_URL,
    EsajPortalIndisponivelError,
    buscar_html,
)

logger = logging.getLogger(__name__)

REFERER = f"{ESAJ_BASE_URL}/tarefas-adv/processos"
PATH_MOVIMENTACOES_AJAX = "/cpopg/carregarMovimentacoesAjax.do"

# Cada fetch é uma página HTML inteira (bem mais pesada que os GETs JSON) e
# o ciclo tem orçamento de 60s por advogado (`TIMEOUT_CICLO_SEGUNDOS`) — só
# um lote pequeno por ciclo, com round-robin entre ciclos.
MOVIMENTACOES_LOTE = 5

# A página do AJAX traz poucas linhas (na captura de 2026-09-29, 5 por
# página). 40 páginas cobrem um histórico longo sem estourar o ciclo
# quando o lote inteiro precisa paginar.
MAX_PAGINAS_MOVIMENTACOES = 40

_CODIGO_PROCESSO_RE = re.compile(r"^[A-Za-z0-9]{1,40}$")
_CURSOR_RE = re.compile(r"^[A-Za-z0-9+/=_-]{1,512}$")


def _codigo_processo(url_cpo: str) -> str | None:
    valores = parse_qs(urlparse(url_cpo).query).get("processo.codigo") or []
    if len(valores) != 1:
        return None
    codigo = valores[0].strip()
    if _CODIGO_PROCESSO_RE.fullmatch(codigo):
        return codigo
    return None


def _url_ajax(codigo: str, cursor: str | None) -> str | None:
    params = {"processo.codigo": codigo}
    if cursor is not None:
        params["cursor"] = cursor
    url = f"{ESAJ_BASE_URL}{PATH_MOVIMENTACOES_AJAX}?{urlencode(params)}"
    return url_cpo_publica(url)


async def _buscar_fragmento(
    client: httpx.AsyncClient, url_cpo: str, codigo: str, cursor: str | None
) -> tuple[list[MovimentacaoRaw], str | None]:
    url = _url_ajax(codigo, cursor)
    if url is None:
        raise EsajPortalIndisponivelError("url_ajax_invalida")
    html = await buscar_html(client, url, referer=url_cpo, ajax=True)
    return parsear_fragmento_movimentacoes(html)


async def _completar_movimentacoes(
    client: httpx.AsyncClient, url_cpo: str, detalhe: CpoDetalheRaw
) -> CpoDetalheRaw:
    """Busca as páginas que o botão 'Exibir movimentações' carregaria.

    Falha de portal sobe para o chamador, que tira o processo deste ciclo
    em vez de marcá-lo como sem acesso.
    """
    codigo = _codigo_processo(url_cpo)
    if codigo is None:
        raise EsajPortalIndisponivelError("codigo_ausente")

    cursor = detalhe.cursor_movimentacoes
    paginas = 0
    if detalhe.movimentacoes_sob_demanda:
        linhas, cursor = await _buscar_fragmento(client, url_cpo, codigo, None)
        detalhe.movimentacoes.extend(linhas)
        paginas = 1

    while cursor and paginas < MAX_PAGINAS_MOVIMENTACOES:
        if _CURSOR_RE.fullmatch(cursor) is None:
            break
        linhas, cursor = await _buscar_fragmento(client, url_cpo, codigo, cursor)
        detalhe.movimentacoes.extend(linhas)
        paginas += 1

    if cursor and paginas >= MAX_PAGINAS_MOVIMENTACOES:
        logger.info("Paginação de movimentações parou no limite de páginas")

    detalhe.movimentacoes_sob_demanda = False
    detalhe.cursor_movimentacoes = None
    return detalhe


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
        detalhe = parsear_cpo_html(html)
        if detalhe.requer_senha_processo:
            logger.info(
                "Ficha CPO sem tabela de movimentações e sem botão de exibir"
            )
        if detalhe.movimentacoes_sob_demanda or detalhe.cursor_movimentacoes:
            try:
                detalhe = await _completar_movimentacoes(client, url_segura, detalhe)
            except EsajPortalIndisponivelError as exc:
                logger.info(
                    "Falha ao buscar movimentações paginadas (causa=%s)",
                    type(exc).__name__,
                )
                continue
        resultado[cd_processo] = detalhe
    return resultado
