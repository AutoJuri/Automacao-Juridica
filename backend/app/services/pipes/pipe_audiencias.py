"""PIPE B — coleta de audiências via `GET /tarefas-adv/api/audiencias`."""

import httpx

from app.schemas.esaj_raw import AudienciaRaw
from app.services.esaj_http import ESAJ_BASE_URL, buscar_json, validar_itens

REFERER = f"{ESAJ_BASE_URL}/tarefas-adv/audiencias"


async def coletar(client: httpx.AsyncClient) -> list[AudienciaRaw]:
    dados = await buscar_json(client, "/tarefas-adv/api/audiencias", referer=REFERER)
    return validar_itens(AudienciaRaw, dados, contexto="audiencias")
