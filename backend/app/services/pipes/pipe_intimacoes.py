"""PIPE A — coleta de intimações via `GET /tarefas-adv/api/intimacoes`."""

import httpx

from app.schemas.esaj_raw import IntimacaoRaw
from app.services.esaj_http import ESAJ_BASE_URL, buscar_json, validar_itens

REFERER = f"{ESAJ_BASE_URL}/tarefas-adv/intimacoes"


async def coletar(client: httpx.AsyncClient) -> list[IntimacaoRaw]:
    dados = await buscar_json(client, "/tarefas-adv/api/intimacoes", referer=REFERER)
    return validar_itens(IntimacaoRaw, dados, contexto="intimacoes")
