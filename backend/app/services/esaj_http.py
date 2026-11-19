"""Client httpx autenticado para as APIs internas do e-SAJ (`tarefas-adv`).

Os cookies (`JSESSIONID`, `CASTGC`, `K-JSESSIONID-*`, `sajcasUrl`) já vêm
decriptados pelo chamador — este módulo nunca decripta nem loga cookie. O
padrão de headers/detecção de redirect segue o que o lab em `scripts/esaj`
validou contra o portal real (ver `docs/modulos/esaj-apis.md`).
"""

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from http.cookies import SimpleCookie
from typing import TypeVar
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# O logger padrão do httpx loga a URL completa de cada request em INFO —
# isso inclui `cdsProcesso` na query string do GET de processos. Silenciado
# aqui (não em `logging.basicConfig` global) para valer em qualquer lugar
# que importe este módulo: scheduler, scripts de smoke, testes.
logging.getLogger("httpx").setLevel(logging.WARNING)

ESAJ_BASE_URL = "https://esaj.tjsp.jus.br"

# Mesmo User-Agent usado no lab — o e-SAJ não exige nada além de parecer um
# navegador comum.
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36"
)

TIMEOUT_REQUISICAO_SEGUNDOS = 20.0


class EsajSessaoInvalidaError(Exception):
    """A resposta indica que o cookie de sessão não autentica mais — o
    e-SAJ redirecionou para a tela de login (SAJ/CAS). Nunca carrega HTML
    ou detalhe da resposta, só o fato.
    """


class EsajPortalIndisponivelError(Exception):
    """Falha de rede, timeout ou resposta inesperada do e-SAJ que não é um
    redirect de login — trata-se como instabilidade do portal, não como
    sessão inválida (o cookie pode continuar bom no próximo ciclo).
    """


class EsajRateLimitError(Exception):
    """O e-SAJ respondeu 429 — o cookie continua válido, só estamos sendo
    limitados temporariamente. Tratado com backoff próprio (ver
    `app.core.backoff`), nunca invalida a sessão.
    """


TModelo = TypeVar("TModelo", bound=BaseModel)


def validar_itens(modelo: type[TModelo], dados: list[dict], *, contexto: str) -> list[TModelo]:
    """Valida cada item do payload bruto. Item inválido é omitido — um
    registro malformado não derruba o pipe inteiro.

    O log nunca inclui o input: `id` de intimação carrega OAB (ver
    `docs/modulos/esaj-apis.md`).
    """
    resultado: list[TModelo] = []
    for item in dados:
        try:
            resultado.append(modelo.model_validate(item))
        except ValidationError as exc:
            campos: list[str] = []
            tipos: list[str] = []
            for err in exc.errors():
                loc = err.get("loc") or ()
                if loc:
                    campos.append(".".join(str(parte) for parte in loc))
                tipos.append(str(err.get("type", "validation_error")))
            logger.info(
                "Item do e-SAJ omitido na validação (pipe=%s, tipos=%s, campos=%s)",
                contexto,
                ",".join(tipos) or "validation_error",
                ",".join(campos) or "-",
            )
    return resultado


def _headers_base(referer: str) -> dict[str, str]:
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": referer,
        "User-Agent": USER_AGENT,
        "X-Requested-With": "XMLHttpRequest",
    }


def _headers_html(referer: str) -> dict[str, str]:
    # Sem `X-Requested-With`: essa é uma navegação de página inteira
    # (`cpopg/show.do`), não um XHR — igual ao que o navegador manda.
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": referer,
        "User-Agent": USER_AGENT,
    }


@dataclass(frozen=True, slots=True)
class CookiePortal:
    """Cookie já descriptografado. `path` decide em qual aplicativo ele vale."""

    name: str
    value: str
    path: str


def normalizar_cookies(bruto: Mapping[str, str] | Sequence[Mapping[str, str]]) -> tuple[CookiePortal, ...]:
    """Aceita o formato antigo (`nome → valor`, path `/`) e a lista com path."""
    if isinstance(bruto, Mapping):
        return tuple(
            CookiePortal(str(nome), str(valor), "/")
            for nome, valor in bruto.items()
            if isinstance(nome, str) and isinstance(valor, str) and valor
        )
    itens: list[CookiePortal] = []
    for item in bruto:
        nome = item.get("name")
        valor = item.get("value")
        path = item.get("path") or "/"
        if not isinstance(nome, str) or not isinstance(valor, str) or not valor:
            continue
        if not isinstance(path, str) or not path.startswith("/"):
            continue
        itens.append(CookiePortal(nome, valor, path))
    return tuple(itens)


def _caminho_casa(cookie_path: str, pedido: str) -> bool:
    if cookie_path == "/":
        return True
    base = cookie_path if cookie_path.endswith("/") else f"{cookie_path}/"
    alvo = pedido if pedido.endswith("/") else f"{pedido}/"
    return alvo.startswith(base)


def cookies_para_caminho(cookies: Sequence[CookiePortal], caminho: str) -> dict[str, str]:
    """Um valor por nome. Se houver dois `JSESSIONID`, fica o path mais específico."""
    melhor: dict[str, CookiePortal] = {}
    for cookie in cookies:
        if not _caminho_casa(cookie.path, caminho or "/"):
            continue
        atual = melhor.get(cookie.name)
        if atual is None or len(cookie.path) > len(atual.path):
            melhor[cookie.name] = cookie
    return {cookie.name: cookie.value for cookie in melhor.values()}


def _cookie_de_sessao(nome: str) -> bool:
    return (
        nome == "JSESSIONID"
        or nome == "CASTGC"
        or nome.startswith("K-JSESSIONID-")
    )


def absorver_set_cookie(jar: list[CookiePortal], brutos: Sequence[str]) -> None:
    """Guarda o cookie que o portal devolve no meio da leitura.

    A pasta digital troca o `JSESSIONID` ao abrir. O PDF só sai com esse
    valor novo. Ele vive na lista em memória e morre com o client.
    """
    for bruto in brutos:
        if not bruto or any(char in bruto for char in "\r\n"):
            continue
        lido = SimpleCookie()
        try:
            lido.load(bruto)
        except Exception:
            continue
        for nome, morsel in lido.items():
            if not _cookie_de_sessao(nome):
                continue
            valor = morsel.value
            path = morsel["path"] or "/"
            if not valor or not isinstance(path, str) or not path.startswith("/"):
                continue
            if any(char in valor for char in "\r\n;"):
                continue
            jar[:] = [cookie for cookie in jar if not (cookie.name == nome and cookie.path == path)]
            jar.append(CookiePortal(nome, valor, path))


def montar_client(cookies: Mapping[str, str] | Sequence[Mapping[str, str]]) -> httpx.AsyncClient:
    """Monta um `httpx.AsyncClient` autenticado com os cookies de sessão.

    Cada pedido leva só o cookie do path daquele aplicativo. O chamador
    descarta `cookies` e fecha o client em seguida — nunca reaproveitar
    entre advogados (ver `security.mdc`).
    """
    jar = list(normalizar_cookies(cookies))

    async def _ajustar(request: httpx.Request) -> None:
        partes = urlparse(str(request.url))
        if "cookie" in request.headers:
            del request.headers["cookie"]
        if partes.hostname != "esaj.tjsp.jus.br":
            return
        escolhidos = cookies_para_caminho(jar, partes.path or "/")
        if not escolhidos:
            return
        request.headers["Cookie"] = "; ".join(
            f"{nome}={valor}" for nome, valor in escolhidos.items()
        )

    async def _guardar(response: httpx.Response) -> None:
        if response.url.host != "esaj.tjsp.jus.br":
            return
        absorver_set_cookie(jar, response.headers.get_list("set-cookie"))

    return httpx.AsyncClient(
        base_url=ESAJ_BASE_URL,
        timeout=TIMEOUT_REQUISICAO_SEGUNDOS,
        follow_redirects=True,
        event_hooks={"request": [_ajustar], "response": [_guardar]},
    )


def _e_html_de_login(content_type: str, corpo: str) -> bool:
    if "text/html" not in content_type.lower():
        return False
    amostra = corpo[:1000].lower()
    if "usernameform" in amostra and "passwordform" in amostra:
        return True
    return "<!doctype html" in amostra and "sajcas" in amostra


def resposta_indica_login(content_type: str, corpo: str, final_url: str) -> bool:
    """Cookie não autentica mais: caiu no CAS ou na tela de login.

    `corpo` é só uma amostra. Quem chama não loga a URL nem o HTML.
    """
    if "/sajcas/" in final_url.lower():
        return True
    return _e_html_de_login(content_type, corpo)


async def buscar_json(
    client: httpx.AsyncClient,
    path: str,
    *,
    params: list[tuple[str, str]] | None = None,
    referer: str,
) -> list[dict]:
    """GET numa API JSON de `tarefas-adv` já com o warm-up assumido feito
    pelo login (ver `auth_esaj.TAREFAS_ADV_MODULES`).

    Levanta `EsajSessaoInvalidaError` se a resposta for a tela de login
    (cookie expirado/inválido), `EsajRateLimitError` se for 429 (rate
    limiting — cookie continua bom) e `EsajPortalIndisponivelError` para
    qualquer outra falha de rede/parse. Nunca loga o corpo da resposta.
    """
    try:
        response = await client.get(path, params=params, headers=_headers_base(referer))
    except httpx.TimeoutException as exc:
        raise EsajPortalIndisponivelError("timeout") from exc
    except httpx.HTTPError as exc:
        raise EsajPortalIndisponivelError(type(exc).__name__) from exc

    content_type = response.headers.get("content-type", "")
    final_url = str(response.url)

    if resposta_indica_login(content_type, response.text, final_url):
        raise EsajSessaoInvalidaError("redirecionado_para_login")

    if response.status_code == 429:
        raise EsajRateLimitError("status_429")

    if response.status_code != 200:
        raise EsajPortalIndisponivelError(f"status_{response.status_code}")

    try:
        dados = response.json()
    except ValueError as exc:
        raise EsajPortalIndisponivelError("resposta_nao_json") from exc

    if not isinstance(dados, list):
        raise EsajPortalIndisponivelError("payload_formato_inesperado")
    return dados


async def buscar_html(
    client: httpx.AsyncClient, url: str, *, referer: str, ajax: bool = False
) -> str:
    """GET de uma página HTML de `cpopg` (não JSON) — usado pelo pipe de
    movimentações e pelo script de captura de fixture (`scripts/capturar_cpo.py`).

    `url` é normalmente `processos.url_cpo`, já absoluta. Mesmas checagens de
    `buscar_json` (sessão inválida / rate limit / falha de portal); nunca loga
    o corpo da resposta.
    """
    headers = _headers_html(referer)
    if ajax:
        # Mesmo header do XHR do botão "Exibir movimentações".
        headers["X-Requested-With"] = "XMLHttpRequest"
    try:
        response = await client.get(url, headers=headers)
    except httpx.TimeoutException as exc:
        raise EsajPortalIndisponivelError("timeout") from exc
    except httpx.HTTPError as exc:
        raise EsajPortalIndisponivelError(type(exc).__name__) from exc

    content_type = response.headers.get("content-type", "")
    final_url = str(response.url)

    if resposta_indica_login(content_type, response.text, final_url):
        raise EsajSessaoInvalidaError("redirecionado_para_login")

    if response.status_code == 429:
        raise EsajRateLimitError("status_429")

    if response.status_code != 200:
        raise EsajPortalIndisponivelError(f"status_{response.status_code}")

    if "text/html" not in content_type.lower():
        raise EsajPortalIndisponivelError("resposta_nao_html")

    return response.text
