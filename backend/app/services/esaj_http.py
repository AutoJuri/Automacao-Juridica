"""Client httpx autenticado para as APIs internas do e-SAJ (`tarefas-adv`).

Os cookies (`JSESSIONID`, `CASTGC`, `K-JSESSIONID-*`, `sajcasUrl`) já vêm
decriptados pelo chamador — este módulo nunca decripta nem loga cookie. O
padrão de headers/detecção de redirect segue o que o lab em `scripts/esaj`
validou contra o portal real (ver `docs/modulos/esaj-apis.md`).
"""

import logging
from typing import TypeVar

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


def montar_client(cookies: dict[str, str]) -> httpx.AsyncClient:
    """Monta um `httpx.AsyncClient` autenticado com os cookies de sessão.

    O chamador é responsável por descartar `cookies` (variável local) e
    fechar o client (`async with`) logo depois do uso — nunca reaproveitar
    entre advogados diferentes (ver `security.mdc` §8).
    """
    jar = httpx.Cookies()
    for nome, valor in cookies.items():
        jar.set(nome, valor, domain="esaj.tjsp.jus.br", path="/")
    return httpx.AsyncClient(
        base_url=ESAJ_BASE_URL,
        cookies=jar,
        timeout=TIMEOUT_REQUISICAO_SEGUNDOS,
        follow_redirects=True,
    )


def _e_html_de_login(content_type: str, corpo: str) -> bool:
    if "text/html" not in content_type.lower():
        return False
    amostra = corpo[:1000].lower()
    if "usernameform" in amostra and "passwordform" in amostra:
        return True
    return "<!doctype html" in amostra and "sajcas" in amostra


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

    if "/sajcas/" in final_url.lower() or _e_html_de_login(content_type, response.text):
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
