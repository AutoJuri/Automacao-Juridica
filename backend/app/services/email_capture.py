"""Captura do código de verificação (duplo fator) enviado por e-mail pelo
e-SAJ, via Gmail API ou Microsoft Graph API.

Faz polling (o e-mail pode levar até ~40s para chegar) e filtra na API
**e** em código — nunca confia só na query do provedor — por remetente e
por data (`since`, o instante exato em que o MFA foi solicitado no login:
nunca reaproveita um código de um e-mail antigo).

Usa uma `SessionLocal` própria (ADR-009): o Playwright sync roda em
thread e o timeout do orquestrador não pode compartilhar a mesma
`AsyncSession` com o refresh do token OAuth.
"""

import asyncio
import base64
import html
import json
import logging
import re
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_secret, encrypt_secret
from app.db.session import SessionLocal
from app.models.tribunal import EMAIL_PROVIDERS, TRIBUNAL_ESAJ_TJSP, TribunalCredential
from app.services import oauth_gmail, oauth_outlook
from app.services.auth_esaj import LoginEsajError
from app.services.oauth_common import OAuthTokenExchangeError

logger = logging.getLogger(__name__)

DOMINIO_REMETENTE_ESAJ = "tjsp.jus.br"

GMAIL_MESSAGES_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
OUTLOOK_MESSAGES_URL = "https://graph.microsoft.com/v1.0/me/messages"
EMAIL_HTTP_TIMEOUT_SECONDS = 10.0

# Orçamento de polling: deixa margem dentro do timeout total de 60s do
# orquestrador (login + preenchimento + warm-up também consomem tempo).
POLLING_ORCAMENTO_SEGUNDOS = 40.0
POLLING_INTERVALO_SEGUNDOS = 3.0

_REGEX_TAG_HTML = re.compile(r"<[^>]+>")
_REGEX_CODIGO_CONTEXTUAL = re.compile(r"(?i)(c[oó]digo|verifica[cç][aã]o|token)[^\d]{0,40}(\d{4,8})")
_REGEX_CODIGO_FALLBACK = re.compile(r"\b\d{6}\b")


class CodigoNaoEncontradoError(LoginEsajError):
    """Nenhum e-mail do e-SAJ com código de verificação chegou dentro do
    orçamento de polling. Subclasse de `LoginEsajError` para o motor de
    login mapear direto para `codigo_nao_encontrado` sem importar este
    módulo.
    """

    def __init__(self, motivo: str = "OrcamentoDePollingEsgotado"):
        super().__init__("codigo_nao_encontrado")
        self.motivo = motivo


def eh_email_do_esaj(remetente: str) -> bool:
    """Confere se o endereço do remetente pertence ao domínio do e-SAJ/TJSP.

    Aceita tanto um endereço puro (`esaj@tjsp.jus.br`) quanto o formato
    `"Nome <endereco@dominio>"` usado no cabeçalho `From` de e-mail.
    """
    remetente_normalizado = remetente.strip().lower()
    match = re.search(r"<([^>]+)>", remetente_normalizado)
    endereco = match.group(1) if match else remetente_normalizado
    if "@" not in endereco:
        return False
    dominio = endereco.rsplit("@", 1)[-1]
    return dominio == DOMINIO_REMETENTE_ESAJ or dominio.endswith(f".{DOMINIO_REMETENTE_ESAJ}")


def _gmail_list_params(since: datetime) -> dict[str, str]:
    """Query da listagem Gmail: só mensagens do TJSP posteriores a `since`."""
    epoch = int(since.timestamp())
    return {"q": f"from:{DOMINIO_REMETENTE_ESAJ} after:{epoch}"}


def _outlook_list_params(since: datetime) -> dict[str, str]:
    """Listagem Graph sem `body` — remetente e data só; corpo vem depois."""
    since_utc = since.astimezone(UTC)
    iso = since_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "$select": "id,from,receivedDateTime",
        "$filter": f"receivedDateTime ge {iso}",
        "$orderby": "receivedDateTime desc",
        "$top": "10",
    }


def _remover_tags_html(texto: str) -> str:
    return html.unescape(_REGEX_TAG_HTML.sub(" ", texto))


def extrair_codigo_verificacao(texto: str) -> str | None:
    """Extrai o código de 6 dígitos do corpo do e-mail (texto puro ou HTML).

    Prioriza um trecho com contexto explícito ("código", "verificação",
    "token" próximo de dígitos); cai para o primeiro número de 6 dígitos
    isolado no texto se não achar contexto.
    """
    texto_limpo = _remover_tags_html(texto)

    contextual = _REGEX_CODIGO_CONTEXTUAL.search(texto_limpo)
    if contextual:
        return contextual.group(2)

    fallback = _REGEX_CODIGO_FALLBACK.search(texto_limpo)
    return fallback.group(0) if fallback else None


def _decodificar_base64url(dados: str) -> str:
    padding = "=" * (-len(dados) % 4)
    try:
        return base64.urlsafe_b64decode(dados + padding).decode("utf-8", errors="ignore")
    except (ValueError, TypeError):
        return ""


def _parse_iso(valor: str | None) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        return None


async def _get_autenticado(
    db: AsyncSession,
    credencial: TribunalCredential,
    provider_module,
    url: str,
    params: dict | None = None,
) -> httpx.Response:
    """GET autenticado com o access_token salvo; se vier 401, renova o token
    uma vez (via `refresh_token`) e regrava `email_oauth_token_encrypted`
    já criptografado antes de tentar de novo.
    """
    if credencial.email_oauth_token_encrypted is None:
        raise LoginEsajError("email_desconectado")

    token_payload = json.loads(decrypt_secret(credencial.email_oauth_token_encrypted))
    access_token = token_payload.get("access_token")

    async with httpx.AsyncClient(timeout=EMAIL_HTTP_TIMEOUT_SECONDS) as client:
        response = await client.get(url, params=params, headers={"Authorization": f"Bearer {access_token}"})
        if response.status_code != httpx.codes.UNAUTHORIZED:
            return response

        refresh_token = token_payload.get("refresh_token")
        if not refresh_token:
            raise LoginEsajError("email_desconectado")

        try:
            renovado = await provider_module.refresh_access_token(refresh_token)
        except OAuthTokenExchangeError as exc:
            raise LoginEsajError("email_desconectado") from exc

        token_payload["access_token"] = renovado.get("access_token")
        if renovado.get("refresh_token"):
            token_payload["refresh_token"] = renovado["refresh_token"]
        if renovado.get("expires_in") is not None:
            token_payload["expires_in"] = renovado["expires_in"]
        credencial.email_oauth_token_encrypted = encrypt_secret(json.dumps(token_payload))
        await db.commit()

        return await client.get(
            url, params=params, headers={"Authorization": f"Bearer {token_payload['access_token']}"}
        )


def _gmail_header(mensagem: dict, nome: str) -> str | None:
    headers = mensagem.get("payload", {}).get("headers", [])
    for cabecalho in headers:
        if cabecalho.get("name", "").lower() == nome.lower():
            return cabecalho.get("value")
    return None


def _gmail_data_interna(mensagem: dict) -> datetime | None:
    bruto = mensagem.get("internalDate")
    if not bruto:
        return None
    try:
        return datetime.fromtimestamp(int(bruto) / 1000, tz=UTC)
    except (ValueError, TypeError, OverflowError):
        return None


def _gmail_corpo(mensagem: dict) -> str:
    partes_texto: list[str] = []

    def _percorrer(parte: dict) -> None:
        dados = parte.get("body", {}).get("data")
        if dados:
            partes_texto.append(_decodificar_base64url(dados))
        for sub_parte in parte.get("parts", []) or []:
            _percorrer(sub_parte)

    _percorrer(mensagem.get("payload", {}))
    return "\n".join(partes_texto)


async def _buscar_codigo_gmail(db: AsyncSession, credencial: TribunalCredential, since: datetime) -> str | None:
    resposta = await _get_autenticado(
        db, credencial, oauth_gmail, GMAIL_MESSAGES_URL, params=_gmail_list_params(since)
    )
    if resposta.status_code != httpx.codes.OK:
        return None

    for resumo in resposta.json().get("messages", []):
        detalhe = await _get_autenticado(
            db, credencial, oauth_gmail, f"{GMAIL_MESSAGES_URL}/{resumo['id']}", params={"format": "full"}
        )
        if detalhe.status_code != httpx.codes.OK:
            continue

        mensagem = detalhe.json()
        recebida_em = _gmail_data_interna(mensagem)
        if recebida_em is None or recebida_em <= since:
            continue

        remetente = _gmail_header(mensagem, "From")
        if not remetente or not eh_email_do_esaj(remetente):
            continue

        codigo = extrair_codigo_verificacao(_gmail_corpo(mensagem))
        if codigo:
            return codigo

    return None


async def _buscar_codigo_outlook(db: AsyncSession, credencial: TribunalCredential, since: datetime) -> str | None:
    resposta = await _get_autenticado(
        db,
        credencial,
        oauth_outlook,
        OUTLOOK_MESSAGES_URL,
        params=_outlook_list_params(since),
    )
    if resposta.status_code != httpx.codes.OK:
        return None

    for mensagem in resposta.json().get("value", []):
        recebida_em = _parse_iso(mensagem.get("receivedDateTime"))
        if recebida_em is None or recebida_em <= since:
            continue

        remetente = ((mensagem.get("from") or {}).get("emailAddress") or {}).get("address")
        if not remetente or not eh_email_do_esaj(remetente):
            continue

        detalhe = await _get_autenticado(
            db,
            credencial,
            oauth_outlook,
            f"{OUTLOOK_MESSAGES_URL}/{mensagem['id']}",
            params={"$select": "body"},
        )
        if detalhe.status_code != httpx.codes.OK:
            continue

        texto = (detalhe.json().get("body") or {}).get("content", "")
        codigo = extrair_codigo_verificacao(texto)
        if codigo:
            return codigo

    return None


async def _carregar_credencial(db: AsyncSession, user_id: UUID) -> TribunalCredential | None:
    return await db.scalar(
        select(TribunalCredential).where(
            TribunalCredential.user_id == user_id,
            TribunalCredential.tribunal == TRIBUNAL_ESAJ_TJSP,
        )
    )


async def buscar_codigo_esaj(
    user_id: UUID,
    since: datetime,
    cancelado: asyncio.Event | None = None,
) -> str:
    """Faz polling da caixa de entrada até achar o código de verificação do
    e-SAJ enviado depois de `since`, ou estourar o orçamento de tempo.

    Abre uma `SessionLocal` por iteração (ADR-009) — nunca recebe a sessão
    do orquestrador. `cancelado` interrompe o loop se o timeout de 60s
    disparar no orquestrador enquanto a thread do Playwright ainda roda.

    Levanta `LoginEsajError("email_desconectado")` se não há e-mail
    conectado ou o token não pôde ser renovado, e `CodigoNaoEncontradoError`
    se o orçamento de polling esgotar sem achar o código.
    """
    prazo_final = datetime.now(UTC) + timedelta(seconds=POLLING_ORCAMENTO_SEGUNDOS)

    while True:
        if cancelado is not None and cancelado.is_set():
            raise CodigoNaoEncontradoError("ValidacaoCancelada")

        async with SessionLocal() as db:
            credencial = await _carregar_credencial(db, user_id)
            if credencial is None or credencial.email_provider not in EMAIL_PROVIDERS:
                raise LoginEsajError("email_desconectado")

            buscar = _buscar_codigo_gmail if credencial.email_provider == "gmail" else _buscar_codigo_outlook
            codigo = await buscar(db, credencial, since)
            if codigo:
                return codigo

        if datetime.now(UTC) >= prazo_final:
            raise CodigoNaoEncontradoError("OrcamentoDePollingEsgotado")
        await asyncio.sleep(POLLING_INTERVALO_SEGUNDOS)
