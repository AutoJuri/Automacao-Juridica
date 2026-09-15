"""Parser do HTML do CPO (`cpopg/show.do`) — movimentações e blocos extras.

Contrato real (capturas ao vivo, ADR-012 / ADR-013):

- Movimentações: `tbody#tabelaTodasMovimentacoes` (completo, `display:none`).
  `tabelaUltimasMovimentacoes` nunca é fonte.
- Capa complementar (foro, vara, juiz, distribuição, controle, área, valor):
  ids `*Processo` no header. Classe/assunto já vêm do JSON — não entram aqui.
- Partes: `table#tableTodasPartes` (completa, `display:none`) quando existe.
  Se o HTML não trouxer essa tabela (comum quando há poucas partes), usa
  `tablePartesPrincipais` — a lista visível na tela.
- Petições diversas / audiências do CPO: tabela seguinte ao `h2.tituloDoBloco`.
  Primeira `tr.label` é cabeçalho (Data / Tipo) — descartar.
- Incidentes/apensos preenchidos ainda sem fixture: só os marcadores de
  vazio `td#processoSemIncidentes` e `tbody#dadosApensosNaoDisponiveis`.
- Sem `tabelaTodasMovimentacoes` ⇒ `requer_senha_processo=True` e nada mais
  (não pede senha dos autos).

Nunca solicita nem guarda senha de autos.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from urllib.parse import ParseResult, urlparse

from bs4 import BeautifulSoup, Tag

from app.schemas.esaj_cpo_raw import (
    AudienciaCpoRaw,
    CapaCpoRaw,
    CpoDetalheRaw,
    MovimentacaoRaw,
    ParteCpoRaw,
    PeticaoDiversaRaw,
)
from app.services.esaj_http import ESAJ_BASE_URL

logger = logging.getLogger(__name__)

ID_TABELA_TODAS_MOVIMENTACOES = "tabelaTodasMovimentacoes"
ID_TABELA_TODAS_PARTES = "tableTodasPartes"
ID_TABELA_PARTES_PRINCIPAIS = "tablePartesPrincipais"
ID_SEM_INCIDENTES = "processoSemIncidentes"
ID_SEM_APENSOS = "dadosApensosNaoDisponiveis"
ID_SEM_AUDIENCIAS = "processoSemAudiencias"
CLASSE_LINK_DOCUMENTO = "linkMovVincProc"
PATH_DOCUMENTO_CPO = "/cpopg/abrirDocumentoVinculadoMovimentacao.do"
PREFIXO_PATH_CPO = "/cpopg/"
CLASSE_TITULO_BLOCO = "tituloDoBloco"

CAPA_IDS = {
    "foro": "foroProcesso",
    "vara": "varaProcesso",
    "juiz": "juizProcesso",
    "distribuicao": "dataHoraDistribuicaoProcesso",
    "controle": "numeroControleProcesso",
    "area": "areaProcesso",
    "valor_acao": "valorAcaoProcesso",
}

TITULO_PETICOES = "peticoes diversas"
TITULO_AUDIENCIAS = "audiencias"

PROTOCOLO_RE = re.compile(r"(?i)n[ºo°]\s*protocolo:\s*([A-Za-z0-9.\-]+)")


def _url_https_esaj(url: str | None) -> tuple[str, ParseResult] | None:
    """https://esaj.tjsp.jus.br sem credencial na URL. Devolve (trimmed, parsed)."""
    if not url:
        return None
    trimmed = url.strip()
    parsed = urlparse(trimmed)
    if parsed.scheme != "https" or parsed.netloc != "esaj.tjsp.jus.br":
        return None
    if parsed.username or parsed.password:
        return None
    return trimmed, parsed


def url_documento_publica(url: str | None) -> str | None:
    """Só aceita https://esaj.tjsp.jus.br/cpopg/abrirDocumentoVinculadoMovimentacao.do?...

    Rejeita `javascript:`, outros hosts e o hash `#liberarAutoPorSenha`.
    """
    parsed_ok = _url_https_esaj(url)
    if parsed_ok is None:
        return None
    trimmed, parsed = parsed_ok
    if parsed.path != PATH_DOCUMENTO_CPO:
        return None
    return trimmed


def url_cpo_publica(url: str | None) -> str | None:
    """Só aceita https://esaj.tjsp.jus.br/cpopg/... (ficha `show.do`).

    Rejeita `javascript:`, hosts internos, userinfo e path fora de `/cpopg/`.
    """
    parsed_ok = _url_https_esaj(url)
    if parsed_ok is None:
        return None
    trimmed, parsed = parsed_ok
    if not parsed.path.startswith(PREFIXO_PATH_CPO):
        return None
    return trimmed


def _url_documento_segura(href: str | None) -> str | None:
    if not href:
        return None
    href = href.strip()
    if href.startswith("#") or href.lower().startswith("javascript:"):
        return None
    if href.startswith(PATH_DOCUMENTO_CPO):
        return url_documento_publica(f"{ESAJ_BASE_URL}{href}")
    return url_documento_publica(href)


def _extrair_documento(celula) -> tuple[bool, str | None]:
    if celula is None:
        return False, None
    links = celula.find_all("a", class_=CLASSE_LINK_DOCUMENTO)
    if not links:
        return False, None
    for link in links:
        url = _url_documento_segura(link.get("href"))
        if url:
            return True, url
    return True, None


def _extrair_titulo_e_descricao(celula) -> tuple[str | None, str]:
    linhas = [linha.strip() for linha in celula.get_text("\n", strip=True).split("\n") if linha.strip()]
    if not linhas:
        return None, ""
    return linhas[0], "\n".join(linhas)


def _parsear_linha(linha) -> MovimentacaoRaw | None:
    data_td = linha.find("td", class_="dataMovimentacao")
    desc_td = linha.find("td", class_="descricaoMovimentacao")
    data_texto = data_td.get_text(strip=True) if data_td else ""
    titulo, descricao = _extrair_titulo_e_descricao(desc_td) if desc_td else (None, "")
    tem_documento, url_documento = _extrair_documento(desc_td)

    if not data_texto or not descricao:
        logger.info("Linha de movimentação do CPO omitida (data ou descrição ausente)")
        return None

    return MovimentacaoRaw(
        data=data_texto,
        titulo=titulo,
        descricao=descricao,
        tem_documento=tem_documento,
        url_documento=url_documento,
    )


def _texto_id(soup: BeautifulSoup, elemento_id: str) -> str | None:
    el = soup.find(id=elemento_id)
    if el is None:
        return None
    texto = el.get_text(" ", strip=True)
    return texto or None


def _normalizar_titulo(texto: str) -> str:
    nfd = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def _tabela_do_bloco(soup: BeautifulSoup, titulo_normalizado: str) -> Tag | None:
    for h2 in soup.select("h2.tituloDoBloco"):
        if _normalizar_titulo(h2.get_text()) == titulo_normalizado:
            proxima = h2.find_next("table")
            return proxima if isinstance(proxima, Tag) else None
    return None


def _celulas_texto(linha: Tag) -> list[str]:
    return [cel.get_text(" ", strip=True) for cel in linha.find_all(["td", "th"])]


def _eh_cabecalho_lista(linha: Tag) -> bool:
    classes = linha.get("class") or []
    if "label" in classes:
        return True
    celulas = [c.lower() for c in _celulas_texto(linha)]
    return bool(celulas) and celulas[0] == "data"


def _parsear_capa(soup: BeautifulSoup) -> CapaCpoRaw:
    return CapaCpoRaw(**{campo: _texto_id(soup, elemento_id) for campo, elemento_id in CAPA_IDS.items()})


def _linhas_partes(tabela: Tag) -> list[ParteCpoRaw]:
    partes: list[ParteCpoRaw] = []
    for linha in tabela.find_all("tr"):
        papel_td = linha.find("td", class_="label")
        nome_td = linha.find("td", class_="nomeParteEAdvogado")
        papel = papel_td.get_text(" ", strip=True) if papel_td else ""
        if not papel:
            continue
        linhas_nome: list[str] = []
        if nome_td is not None:
            linhas_nome = [
                linha_txt.strip()
                for linha_txt in nome_td.get_text("\n", strip=True).split("\n")
                if linha_txt.strip()
            ]
        partes.append(
            ParteCpoRaw(
                papel=papel,
                nome=linhas_nome[0] if linhas_nome else None,
                advogados="\n".join(linhas_nome[1:]) if len(linhas_nome) > 1 else None,
            )
        )
    return partes


def _parsear_partes(soup: BeautifulSoup) -> list[ParteCpoRaw]:
    todas = soup.find(id=ID_TABELA_TODAS_PARTES)
    if isinstance(todas, Tag):
        partes = _linhas_partes(todas)
        if partes:
            return partes
    principais = soup.find(id=ID_TABELA_PARTES_PRINCIPAIS)
    if isinstance(principais, Tag):
        return _linhas_partes(principais)
    return []


def _parsear_peticoes(soup: BeautifulSoup) -> list[PeticaoDiversaRaw]:
    tabela = _tabela_do_bloco(soup, TITULO_PETICOES)
    if tabela is None:
        return []
    peticoes: list[PeticaoDiversaRaw] = []
    for linha in tabela.find_all("tr"):
        if _eh_cabecalho_lista(linha):
            continue
        tds = linha.find_all("td")
        if len(tds) < 2:
            continue
        data = tds[0].get_text(" ", strip=True)
        tipo = _tipo_peticao(tds[1])
        if not data or not tipo:
            continue
        texto_linha = linha.get_text(" ", strip=True)
        protocolo_m = PROTOCOLO_RE.search(texto_linha)
        extra_partes = [c.get_text(" ", strip=True) for c in tds[2:] if c.get_text(strip=True)]
        peticoes.append(
            PeticaoDiversaRaw(
                data=data,
                tipo=tipo,
                protocolo=protocolo_m.group(1) if protocolo_m else None,
                texto_extra=" ".join(extra_partes),
            )
        )
    return peticoes


def _tipo_peticao(celula) -> str:
    texto = celula.get_text("\n", strip=True)
    primeira = next((linha.strip() for linha in texto.split("\n") if linha.strip()), "")
    corte = re.search(r"(?i)n[ºo°]\s*protocolo:", primeira)
    if corte:
        primeira = primeira[: corte.start()].strip()
    return primeira


def _parsear_audiencias_cpo(soup: BeautifulSoup) -> list[AudienciaCpoRaw]:
    if soup.find(id=ID_SEM_AUDIENCIAS) is not None:
        return []
    tabela = _tabela_do_bloco(soup, TITULO_AUDIENCIAS)
    if tabela is None:
        return []
    audiencias: list[AudienciaCpoRaw] = []
    for linha in tabela.find_all("tr"):
        if _eh_cabecalho_lista(linha):
            continue
        celulas = _celulas_texto(linha)
        if len(celulas) < 2:
            continue
        data, titulo = celulas[0], celulas[1]
        if not data or not titulo:
            continue
        audiencias.append(
            AudienciaCpoRaw(
                data=data,
                titulo=titulo,
                situacao=celulas[2] if len(celulas) > 2 and celulas[2] else None,
                qt_pessoas=celulas[3] if len(celulas) > 3 and celulas[3] else None,
            )
        )
    return audiencias


def parsear_cpo_html(html: str) -> CpoDetalheRaw:
    """Extrai movimentações e blocos complementares do HTML do CPO.

    Nunca levanta exceção por HTML malformado — na dúvida, devolve lista
    vazia (o chamador decide o que fazer, ex.: não atualizar nada naquele
    ciclo). Linha individual malformada é omitida, não derruba o parse.
    """
    soup = BeautifulSoup(html, "lxml")
    tbody = soup.find(id=ID_TABELA_TODAS_MOVIMENTACOES)
    if tbody is None:
        return CpoDetalheRaw(requer_senha_processo=True)

    movimentacoes: list[MovimentacaoRaw] = []
    for linha in tbody.find_all("tr", class_="containerMovimentacao"):
        raw = _parsear_linha(linha)
        if raw is not None:
            movimentacoes.append(raw)

    return CpoDetalheRaw(
        requer_senha_processo=False,
        movimentacoes=movimentacoes,
        capa=_parsear_capa(soup),
        partes=_parsear_partes(soup),
        peticoes=_parsear_peticoes(soup),
        audiencias_cpo=_parsear_audiencias_cpo(soup),
        sem_incidentes=soup.find(id=ID_SEM_INCIDENTES) is not None,
        sem_apensos=soup.find(id=ID_SEM_APENSOS) is not None,
    )
