"""Cliente da API pública do DataJud (CNJ).

Duas leituras, a mesma API:

- o job diário complementa um processo que a plataforma já rastreia;
- a consulta da tela busca um número CNJ que não está na carteira e
  devolve a ficha pública, sem gravar nada.

Nunca descobre processo por nome ou OAB: a API pública não expõe partes
nem advogados (Portaria CNJ 160/2020). Só aceita um número CNJ já
conhecido e consulta o índice do tribunal correspondente
(`app.core.cnj.resolver_alias_datajud`).

O job diário espera no máximo 10s. A consulta da tela espera até 30s
para ler a resposta, porque a busca pública do CNJ costuma passar de 10s.
Falha sempre isolada: qualquer erro de rede, HTTP ou parsing devolve
`None` — nunca propaga, porque o job diário não pode cair por causa de
um processo só.
Log nunca inclui o payload da resposta, só o tipo do problema.
"""

import logging
from dataclasses import dataclass
from typing import Literal

import httpx
from pydantic import ValidationError

from app.core.cnj import extrair_segmento_tribunal, resolver_alias_datajud
from app.core.config import get_settings
from app.schemas.datajud_raw import DatajudProcessoRaw

logger = logging.getLogger(__name__)

DATAJUD_BASE_URL = "https://api-publica.datajud.cnj.jus.br"
TIMEOUT_REQUISICAO_SEGUNDOS = 10.0
# A busca avulsa da tela. O job diário continua nos 10s acima.
TIMEOUT_CONSULTA_PUBLICA_SEGUNDOS = 30.0


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


SituacaoExibicao = Literal[
    "encontrado",
    "ausente",
    "indisponivel",
    "tribunal_nao_suportado",
    "sem_chave",
    "numero_invalido",
]


@dataclass(frozen=True)
class ExibicaoDatajud:
    """Resultado de uma consulta avulsa. Não grava no banco."""

    situacao: SituacaoExibicao
    tribunal: str | None
    processo: DatajudProcessoRaw | None


async def consultar_exibicao(client: httpx.AsyncClient, numero_cnj: str) -> ExibicaoDatajud:
    """Consulta um CNJ para mostrar na tela, sem persistir.

    Separa "não está na base" de "a API não respondeu", o que
    `consultar_processo` junta em `None` de propósito para o job diário.
    """
    settings = get_settings()
    if not settings.datajud_api_key:
        return ExibicaoDatajud("sem_chave", None, None)
    if extrair_segmento_tribunal(numero_cnj) is None:
        return ExibicaoDatajud("numero_invalido", None, None)
    alias = resolver_alias_datajud(numero_cnj)
    if alias is None:
        return ExibicaoDatajud("tribunal_nao_suportado", None, None)

    url = f"{DATAJUD_BASE_URL}/api_publica_{alias}/_search"
    payload = {"query": {"match": {"numeroProcesso": _apenas_digitos(numero_cnj)}}}
    headers = {"Authorization": f"APIKey {settings.datajud_api_key}"}
    try:
        resposta = await client.post(
            url,
            json=payload,
            headers=headers,
            timeout=httpx.Timeout(
                TIMEOUT_REQUISICAO_SEGUNDOS,
                read=TIMEOUT_CONSULTA_PUBLICA_SEGUNDOS,
            ),
        )
        resposta.raise_for_status()
        corpo = resposta.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.info(
            "Consulta pública do DataJud indisponível (tribunal=%s, erro=%s)",
            alias,
            type(exc).__name__,
        )
        return ExibicaoDatajud("indisponivel", alias, None)

    hits = (corpo.get("hits") or {}).get("hits") or []
    if not hits:
        return ExibicaoDatajud("ausente", alias, None)
    try:
        processo = DatajudProcessoRaw.model_validate(hits[0].get("_source") or {})
    except ValidationError:
        logger.info("Consulta pública do DataJud com item inválido (tribunal=%s)", alias)
        return ExibicaoDatajud("indisponivel", alias, None)
    return ExibicaoDatajud("encontrado", alias, processo)
