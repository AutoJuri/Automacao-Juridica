"""Rotas da capa de elaboração.

`user_id` vem do JWT. Elaboração ou processo de outra pessoa responde 404.
"""

from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.elaboracao import (
    ElaboracaoCardSchema,
    ElaboracaoCreateSchema,
    ElaboracaoDetalheSchema,
    ElaboracaoUpdateSchema,
    PaginaProcessosParaIniciarSchema,
)
from app.services import elaboracoes as servico

router = APIRouter(prefix="/elaboracoes", tags=["elaboracoes"])


@router.get("", response_model=list[ElaboracaoCardSchema])
async def listar_em_andamento(
    current_user: CurrentUser,
    db: DbSession,
    q: str | None = Query(default=None, max_length=120),
) -> list[ElaboracaoCardSchema]:
    return await servico.listar_em_andamento(db, current_user.id, q=q)


@router.get("/a-iniciar", response_model=PaginaProcessosParaIniciarSchema)
async def listar_a_iniciar(
    current_user: CurrentUser,
    db: DbSession,
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, max_length=120),
) -> PaginaProcessosParaIniciarSchema:
    return await servico.listar_a_iniciar(db, current_user.id, offset=offset, q=q)


@router.post("", response_model=ElaboracaoDetalheSchema)
async def criar_ou_reabrir(
    dados: ElaboracaoCreateSchema,
    current_user: CurrentUser,
    db: DbSession,
    response: Response,
) -> ElaboracaoDetalheSchema:
    detalhe, criado = await servico.criar_ou_reabrir(db, current_user.id, dados)
    response.status_code = status.HTTP_201_CREATED if criado else status.HTTP_200_OK
    return detalhe


@router.get("/{elaboracao_id}", response_model=ElaboracaoDetalheSchema)
async def obter(
    elaboracao_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ElaboracaoDetalheSchema:
    return await servico.obter(db, current_user.id, elaboracao_id)


@router.patch("/{elaboracao_id}", response_model=ElaboracaoDetalheSchema)
async def atualizar(
    elaboracao_id: UUID,
    dados: ElaboracaoUpdateSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> ElaboracaoDetalheSchema:
    return await servico.atualizar(db, current_user.id, elaboracao_id, dados)


@router.delete("/{elaboracao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir(
    elaboracao_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    await servico.excluir(db, current_user.id, elaboracao_id)
