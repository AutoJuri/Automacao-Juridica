"""Login automatizado no e-SAJ via Playwright.

Preenche CPF + senha, aguarda o duplo fator (código obtido por um callback
injetado — nunca importa `email_capture` diretamente, o que mantém este
módulo testável sem rede nem dependência do provedor de e-mail), "aquece" a
sessão navegando pelos módulos `tarefas-adv` (obrigatório: sem isso os
cookies não autenticam as APIs internas) e extrai os cookies de sessão.

Roda sempre headless e com um contexto de browser novo e isolado por
chamada — nunca reaproveitado entre advogados (ver `security.mdc` §8).

No Windows, o event loop padrão do uvicorn (`SelectorEventLoop`) não
suporta subprocessos — o Playwright async falha com `NotImplementedError`.
Por isso o browser roda na API **síncrona** dentro de `asyncio.to_thread`,
e o callback async de MFA é ponteado de volta ao loop principal via
`run_coroutine_threadsafe`.
"""

import asyncio
import logging
import os
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _corrigir_browsers_path_efemero() -> None:
    """Evita o cache temporário do Cursor (`cursor-sandbox-cache`), que some
    entre sessões e faz o Chromium 'sumir' com `Executable doesn't exist`.
    """
    atual = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
    if "cursor-sandbox-cache" not in atual.replace("\\", "/").lower():
        return
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return
    destino = str(Path(local_app_data) / "ms-playwright")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = destino
    logger.info("PLAYWRIGHT_BROWSERS_PATH redirecionado para %s", destino)

LOGIN_URL = (
    "https://esaj.tjsp.jus.br/sajcas/login?"
    "service=https%3A%2F%2Fesaj.tjsp.jus.br%2Fesaj%2Fapi%2Fauth%2Fcheck#aba-cpf"
)

SELETOR_CPF = "#usernameForm"
SELETOR_SENHA = "#passwordForm"
SELETOR_SUBMIT = "#aba-cpf input[type='submit']"
SELETOR_MODAL_MFA = "#modalTokenDuploFator"
SELETOR_INPUT_MFA = f"{SELETOR_MODAL_MFA} input[type='text']"
SELETOR_SUBMIT_MFA = f"{SELETOR_MODAL_MFA} button:has-text('Enviar')"
SELETOR_ERRO_LOGIN = "#mensagemErro, .alert-danger"

# As 4 páginas de módulo que precisam ser abertas depois do MFA para a
# sessão ficar autenticada nas APIs internas do e-SAJ.
TAREFAS_ADV_MODULES = (
    "https://esaj.tjsp.jus.br/tarefas-adv/",
    "https://esaj.tjsp.jus.br/tarefas-adv/intimacoes",
    "https://esaj.tjsp.jus.br/tarefas-adv/audiencias",
    "https://esaj.tjsp.jus.br/tarefas-adv/peticoes",
)

TIMEOUT_NAVEGACAO_MS = 30_000
TIMEOUT_MODAL_MFA_MS = 15_000
# Margem dentro do orçamento de 60s do orquestrador (login + warm-up também
# consomem tempo).
TIMEOUT_OBTER_CODIGO_SEGUNDOS = 45.0

COOKIE_JSESSIONID = "JSESSIONID"
COOKIE_CASTGC = "CASTGC"
COOKIE_PREFIXO_K_JSESSIONID = "K-JSESSIONID-"
COOKIE_SAJCAS_URL = "sajcasUrl"
PATH_TAREFAS_ADV = "/tarefas-adv"


class LoginEsajError(Exception):
    """Falha de login já mapeada para um dos `SESSION_STATUSES`.

    `tipo` nunca carrega detalhe de Playwright, HTML ou mensagem do e-SAJ —
    só o status que o resto do sistema já conhece (`credencial_invalida`,
    `bloqueado`, `portal_indisponivel`, `email_desconectado`,
    `codigo_nao_encontrado`).
    """

    def __init__(self, tipo: str):
        super().__init__(tipo)
        self.tipo = tipo


def selecionar_cookies_sessao(cookies: list[dict]) -> dict[str, str]:
    """Escolhe, da lista completa de cookies do contexto, só os que a sessão
    autenticada do e-SAJ precisa para as próximas chamadas.

    Existe mais de um cookie `JSESSIONID` no contexto (um por path); só o do
    path `/tarefas-adv` importa — o de `/sajcas` pertence à tela de login e
    não autentica nada depois dela.
    """
    selecionados: dict[str, str] = {}
    for cookie in cookies:
        nome = cookie.get("name", "")
        valor = cookie.get("value", "")
        path = cookie.get("path", "")
        if nome == COOKIE_JSESSIONID and path.startswith(PATH_TAREFAS_ADV):
            selecionados[COOKIE_JSESSIONID] = valor
        elif nome == COOKIE_CASTGC:
            selecionados[COOKIE_CASTGC] = valor
        elif nome.startswith(COOKIE_PREFIXO_K_JSESSIONID):
            selecionados[nome] = valor
        elif nome == COOKIE_SAJCAS_URL:
            selecionados[COOKIE_SAJCAS_URL] = valor

    faltantes = [nome for nome in (COOKIE_JSESSIONID, COOKIE_CASTGC) if nome not in selecionados]
    if faltantes:
        # Sessão "completou" o fluxo mas sem os cookies essenciais — trata
        # como instabilidade do portal, não como credencial inválida (o
        # login em si foi aceito).
        raise LoginEsajError("portal_indisponivel")

    return selecionados


def _detectar_resultado_pos_submit(page) -> str:
    """Espera aparecer o modal de MFA OU uma mensagem de erro de credencial.

    Retorna `"mfa"` ou `"erro"` — nunca deixa o caller sem diagnóstico.
    """
    try:
        page.wait_for_selector(
            f"{SELETOR_MODAL_MFA}, {SELETOR_ERRO_LOGIN}",
            timeout=TIMEOUT_MODAL_MFA_MS,
            state="visible",
        )
    except PlaywrightTimeoutError as exc:
        raise LoginEsajError("portal_indisponivel") from exc

    if page.is_visible(SELETOR_MODAL_MFA):
        return "mfa"
    return "erro"


def _salvar_screenshot_debug(page, nome: str) -> None:
    """Screenshot só em desenvolvimento — nunca reter dado sensível em disco
    de servidor de produção (a tela pode conter CPF preenchido)."""
    settings = get_settings()
    if not settings.is_development:
        return
    try:
        destino = Path("debug_screenshots")
        destino.mkdir(exist_ok=True)
        page.screenshot(path=str(destino / f"{nome}.png"))
    except PlaywrightError:
        logger.debug("Falha ao salvar screenshot de depuração (%s)", nome)


def _mapear_erro_playwright(exc: BaseException) -> LoginEsajError:
    """Converte qualquer falha do Playwright/browser em LoginEsajError.

    Em development loga só o tipo e a mensagem técnica curta — nunca CPF,
    senha, cookie ou HTML da página.
    """
    if isinstance(exc, LoginEsajError):
        return exc

    mensagem = str(exc)
    mensagem_lower = mensagem.lower()
    settings = get_settings()
    if settings.is_development:
        logger.warning(
            "Falha no login e-SAJ (%s): %s",
            type(exc).__name__,
            mensagem[:300].replace("\n", " "),
        )

    if "executable doesn't exist" in mensagem_lower or "browserType.launch" in mensagem:
        logger.error(
            "Chromium do Playwright não encontrado. Rode: "
            "python -m uv run playwright install chromium"
        )
        return LoginEsajError("portal_indisponivel")
    if "429" in mensagem_lower or "too many" in mensagem_lower or "rate limit" in mensagem_lower:
        return LoginEsajError("bloqueado")
    return LoginEsajError("portal_indisponivel")


def _realizar_login_sync(
    cpf: str,
    senha: str,
    obter_codigo: Callable[[datetime], str],
) -> dict[str, str]:
    """Fluxo Playwright síncrono — deve rodar fora do event loop do uvicorn."""
    _corrigir_browsers_path_efemero()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        # Contexto novo e isolado a cada chamada — nunca compartilhado entre
        # advogados nem reaproveitado entre tentativas.
        context = browser.new_context()
        try:
            page = context.new_page()
            page.set_default_timeout(TIMEOUT_NAVEGACAO_MS)

            page.goto(LOGIN_URL, wait_until="domcontentloaded")
            page.fill(SELETOR_CPF, cpf)
            page.fill(SELETOR_SENHA, senha)
            page.click(SELETOR_SUBMIT)

            resultado = _detectar_resultado_pos_submit(page)
            if resultado == "erro":
                _salvar_screenshot_debug(page, "credencial_invalida")
                raise LoginEsajError("credencial_invalida")

            mfa_solicitado_em = datetime.now(UTC)
            codigo = obter_codigo(mfa_solicitado_em)

            page.fill(SELETOR_INPUT_MFA, codigo)
            page.click(SELETOR_SUBMIT_MFA)
            page.wait_for_selector(SELETOR_MODAL_MFA, state="hidden", timeout=TIMEOUT_MODAL_MFA_MS)

            for url in TAREFAS_ADV_MODULES:
                page.goto(url, wait_until="domcontentloaded")

            cookies = context.cookies()
            return selecionar_cookies_sessao(cookies)
        except LoginEsajError:
            raise
        except Exception as exc:
            raise _mapear_erro_playwright(exc) from exc
        finally:
            context.close()
            browser.close()


async def realizar_login(
    cpf: str,
    senha: str,
    obter_codigo: Callable[[datetime], Awaitable[str]],
) -> dict[str, str]:
    """Executa o fluxo completo de login no e-SAJ e devolve os cookies de
    sessão autenticada, prontos para serem criptografados e persistidos.

    `obter_codigo` recebe o instante exato em que o MFA foi solicitado (para
    quem for buscar o código por e-mail nunca reaproveitar uma mensagem
    antiga) e deve devolver o código de 6 dígitos ou levantar uma exceção —
    qualquer exceção do callback é tratada como falha de login aqui.

    Sempre levanta `LoginEsajError` em caso de falha — nunca deixa escapar
    uma exceção "crua" do Playwright ou de rede.
    """
    loop = asyncio.get_running_loop()

    def obter_codigo_sync(since: datetime) -> str:
        # Ponte thread → event loop: o callback de e-mail é async (httpx +
        # sessão SQLAlchemy), mas o Playwright sync roda numa thread.
        future = asyncio.run_coroutine_threadsafe(obter_codigo(since), loop)
        try:
            return future.result(timeout=TIMEOUT_OBTER_CODIGO_SEGUNDOS)
        except LoginEsajError:
            raise
        except Exception as exc:
            raise _mapear_erro_playwright(exc) from exc

    try:
        return await asyncio.to_thread(_realizar_login_sync, cpf, senha, obter_codigo_sync)
    except LoginEsajError:
        raise
    except Exception as exc:
        # Qualquer falha ao lançar o browser/thread (ex.: Chromium ausente)
        # vira status conhecido — nunca deixa a BackgroundTask explodir.
        raise _mapear_erro_playwright(exc) from exc
