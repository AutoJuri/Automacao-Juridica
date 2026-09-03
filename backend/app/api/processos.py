"""Rotas do painel de processos.

`user_id` vem só do JWT. Processo de outro advogado responde 404 (não 403)
para não vazar existência. `id_esaj` nunca sai no JSON.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.processo import (
    AudienciaPainelSchema,
    IntimacaoPainelSchema,
    ProcessoDetalheSchema,
    ProcessoFixadoSchema,
    ProcessoFixarSchema,
    ProcessoListSchema,
)
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


@router.patch("/{processo_id}", response_model=ProcessoFixadoSchema)
async def fixar_processo(
    processo_id: UUID,
    body: ProcessoFixarSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> ProcessoFixadoSchema:
    atualizado = await painel.atualizar_fixado(
        db, current_user.id, processo_id, fixado=body.fixado
    )
    if atualizado is None:
        raise _NAO_ENCONTRADO
    return ProcessoFixadoSchema(id=atualizado.id, fixado=atualizado.fixado)


router_intimacoes = APIRouter(prefix="/intimacoes", tags=["processos"])
router_audiencias = APIRouter(prefix="/audiencias", tags=["processos"])


@router_intimacoes.get("", response_model=list[IntimacaoPainelSchema])
async def listar_intimacoes(
    current_user: CurrentUser,
    db: DbSession,
) -> list[IntimacaoPainelSchema]:
    return await painel.listar_intimacoes_painel(db, current_user.id)


@router_audiencias.get("", response_model=list[AudienciaPainelSchema])
async def listar_audiencias(
    current_user: CurrentUser,
    db: DbSession,
) -> list[AudienciaPainelSchema]:
    return await painel.listar_audiencias_painel(db, current_user.id)
