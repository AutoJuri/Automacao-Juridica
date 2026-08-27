"""Rotas do painel de processos.

`user_id` vem só do JWT. Processo de outro advogado responde 404 (não 403)
para não vazar existência. `id_esaj` nunca sai no JSON.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.processo import ProcessoDetalheSchema, ProcessoListSchema
from app.services import painel

router = APIRouter(prefix="/processos", tags=["processos"])

_NAO_ENCONTRADO = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado")


@router.get("", response_model=list[ProcessoListSchema])
async def listar_processos(
    current_user: CurrentUser,
    db: DbSession,
    q: str | None = Query(default=None, max_length=120),
) -> list[ProcessoListSchema]:
    return await painel.listar_processos(db, current_user.id, q=q)


@router.get("/{processo_id}", response_model=ProcessoDetalheSchema)
async def obter_processo(
    processo_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ProcessoDetalheSchema:
    detalhe = await painel.buscar_processo_detalhe(db, current_user.id, processo_id)
    if detalhe is None:
        raise _NAO_ENCONTRADO
    return detalhe
