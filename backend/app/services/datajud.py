"""Cliente da API pública do DataJud (CNJ) — complemento somente-leitura
dos processos já rastreados (hoje via e-SAJ). Etapa 9 / ver `docs/modulos/
datajud.md` e ADR-015.

Nunca é fonte de descoberta de processos: só aceita um número CNJ já
conhecido e consulta o índice do tribunal correspondente
(`app.core.cnj.resolver_alias_datajud`). A API pública do DataJud não
expõe partes nem advogados/OAB (Portaria CNJ 160/2020) — não tem como
"puxar a carteira" de um advogado por aqui.

Timeout de 10s por requisição (`security.mdc` §12) e falha sempre
isolada: qualquer erro de rede, HTTP ou parsing devolve `None` — nunca
propaga, porque o job diário não pode cair por causa de um processo só.
Log nunca inclui o payload da resposta, só o tipo do problema.
"""

import logging

import httpx
from pydantic import ValidationError

from app.core.cnj import resolver_alias_datajud
from app.core.config import get_settings
from app.schemas.datajud_raw import DatajudProcessoRaw

logger = logging.getLogger(__name__)

DATAJUD_BASE_URL = "https://api-publica.datajud.cnj.jus.br"
TIMEOUT_REQUISICAO_SEGUNDOS = 10.0


def _apenas_digitos(numero_cnj: str) -> str:
    return "".join(char for char in numero_cnj if char.isdigit())


async def consultar_processo(
    client: httpx.AsyncClient, numero_cnj: str
) -> DatajudProcessoRaw | None:
    """Consulta o DataJud pelo número CNJ já conhecido.

    Devolve `None` sem chamar a rede quando: a chave não está configurada
    (`DATAJUD_API_KEY` vazio), o número não é um CNJ válido, ou o tribunal
    ainda não está mapeado (`resolver_alias_datajud`). Também devolve
    `None` (nunca lança) em qualquer falha de rede, status HTTP de erro,
    JSON malformado ou payload que não valide contra `DatajudProcessoRaw`.
    """
    settings = get_settings()
    if not settings.datajud_api_key:
        logger.debug("DataJud não configurado (DATAJUD_API_KEY vazio) — consulta ignorada")
        return None

    alias = resolver_alias_datajud(numero_cnj)
    if alias is None:
        logger.info("Tribunal do número CNJ ainda não mapeado para o DataJud — consulta ignorada")
        return None

    url = f"{DATAJUD_BASE_URL}/api_publica_{alias}/_search"
    payload = {"query": {"match": {"numeroProcesso": _apenas_digitos(numero_cnj)}}}
    headers = {"Authorization": f"APIKey {settings.datajud_api_key}"}

    try:
        resposta = await client.post(
            url, json=payload, headers=headers, timeout=TIMEOUT_REQUISICAO_SEGUNDOS
        )
        resposta.raise_for_status()
        corpo = resposta.json()
    except httpx.HTTPStatusError as exc:
        logger.info("DataJud respondeu erro HTTP (status=%s, tribunal=%s)", exc.response.status_code, alias)
        return None
    except (httpx.HTTPError, ValueError):
        logger.info("DataJud indisponível ou resposta malformada (tribunal=%s)", alias)
        return None

    hits = (corpo.get("hits") or {}).get("hits") or []
    if not hits:
        return None

    fonte = hits[0].get("_source") or {}
    try:
        return DatajudProcessoRaw.model_validate(fonte)
    except ValidationError:
        logger.info("Item do DataJud omitido na validação (tribunal=%s)", alias)
        return None
