"""Detecção de provedor de e-mail (Gmail/Outlook) por domínio — Etapa 9.

Usada só pra **sugerir** um botão no card de conexão (`EmailConnectionCard`),
nunca pra decidir nada sozinha: a escolha final continua sendo do
advogado. Qualquer erro de DNS/timeout devolve `None` — nunca lança, nunca
bloqueia o fluxo de conexão que já existe.
"""

import logging
from typing import Literal

import dns.resolver

logger = logging.getLogger(__name__)

EmailProvider = Literal["gmail", "outlook"]

TIMEOUT_DNS_SEGUNDOS = 3.0

# Domínios de e-mail gratuito conhecidos — atalho sem precisar de MX.
_DOMINIOS_GMAIL = {"gmail.com", "googlemail.com"}
_DOMINIOS_OUTLOOK = {"outlook.com", "hotmail.com", "live.com", "msn.com"}

# Trechos característicos do *exchange* do MX de cada provedor (Google
# Workspace / Microsoft 365, domínios próprios do advogado).
_MX_GMAIL = ("google.com", "googlemail.com")
_MX_OUTLOOK = ("outlook.com", "protection.outlook.com")


def _dominio(email: str) -> str | None:
    partes = email.strip().rsplit("@", 1)
    if len(partes) != 2 or not partes[1]:
        return None
    return partes[1].lower()


def _provedor_por_mx(dominio: str) -> EmailProvider | None:
    try:
        resposta = dns.resolver.resolve(dominio, "MX", lifetime=TIMEOUT_DNS_SEGUNDOS)
    except Exception:
        # NXDOMAIN, sem MX, timeout, servidor DNS indisponível... qualquer
        # falha aqui só significa "sem sugestão", nunca deve travar o card.
        logger.info("Resolução de MX falhou ou não encontrou registro — sem sugestão de provedor")
        return None

    exchanges = [str(registro.exchange).rstrip(".").lower() for registro in resposta]
    if any(alvo in exchange for exchange in exchanges for alvo in _MX_GMAIL):
        return "gmail"
    if any(alvo in exchange for exchange in exchanges for alvo in _MX_OUTLOOK):
        return "outlook"
    return None


def detectar_provedor_por_dominio(email: str) -> EmailProvider | None:
    """Sugestão de provedor a partir do domínio do e-mail. `None` quando
    não há como sugerir com confiança (domínio desconhecido, sem MX,
    provedor que não é Gmail nem Outlook, ou falha de DNS) — nesse caso a
    UI mantém a escolha manual que já existia.
    """
    dominio = _dominio(email)
    if dominio is None:
        return None
    if dominio in _DOMINIOS_GMAIL:
        return "gmail"
    if dominio in _DOMINIOS_OUTLOOK:
        return "outlook"
    return _provedor_por_mx(dominio)
