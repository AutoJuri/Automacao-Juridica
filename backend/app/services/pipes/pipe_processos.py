"""PIPE D — upsert de ficha via `GET /tarefas-adv/api/processos?cdsProcesso=`.

Não é uma listagem da carteira: exige um ou mais `cdsProcesso` explícitos e
pode devolver menos itens do que foi pedido (código omitido = skip, não
falha — ver ADR-010). Os `cdsProcesso` vêm de fora (união de intimações,
audiências e processos já persistidos), montada pelo orquestrador.
"""

import httpx

from app.schemas.esaj_raw import ProcessoRaw
from app.services.esaj_http import ESAJ_BASE_URL, buscar_json, validar_itens

REFERER = f"{ESAJ_BASE_URL}/tarefas-adv/processos"

# Evita URL gigante quando a carteira do advogado crescer — o e-SAJ não
# documenta um limite, esse valor é uma margem de segurança conservadora.
CDS_PROCESSO_CHUNK_SIZE = 50


def _dividir_em_lotes(itens: list[str], tamanho: int) -> list[list[str]]:
    return [itens[i : i + tamanho] for i in range(0, len(itens), tamanho)]


async def coletar(client: httpx.AsyncClient, cds_processo: list[str]) -> list[ProcessoRaw]:
    if not cds_processo:
        return []

    resultado: list[ProcessoRaw] = []
    for lote in _dividir_em_lotes(cds_processo, CDS_PROCESSO_CHUNK_SIZE):
        params = [("cdsProcesso", cd) for cd in lote]
        dados = await buscar_json(client, "/tarefas-adv/api/processos", params=params, referer=REFERER)
        resultado.extend(validar_itens(ProcessoRaw, dados, contexto="processos"))
    return resultado
