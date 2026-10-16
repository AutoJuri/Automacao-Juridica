"""Rotas de tarefas pessoais e de organização.

O contexto pessoal nunca lê tarefa de organização, e o contrário também.
`user_id` vem do JWT. `organization_id` vem do path e só passa se houver membership.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import CurrentUser, DbSession
from app.core.permissions import ACOES_POR_PAPEL, CurrentOrgMember, require_role
from app.models.organization import OrganizationMember
from app.schemas.task import (
    AssigneePublicSchema,
    BoardSchema,
    BoardUpdateSchema,
    ColumnCreateSchema,
    ColumnPublicSchema,
    ColumnUpdateSchema,
    TaskCreateOrgSchema,
    TaskCreateSchema,
    TaskMoveSchema,
    TaskPageSchema,
    TaskPublicSchema,
    TaskUpdateOrgSchema,
    TaskUpdateSchema,
)
from app.services import tasks as quadros

router = APIRouter(prefix="/tasks", tags=["tasks"])
router_org = APIRouter(prefix="/organizations/{org_id}", tags=["tasks"])

MembroColunas = Annotated[
    OrganizationMember, Depends(require_role(ACOES_POR_PAPEL["configurar_colunas"]))
]


@router.get("/board", response_model=BoardSchema)
async def board_pessoal(current_user: CurrentUser, db: DbSession) -> BoardSchema:
    return await quadros.obter_board(db, quadros.escopo_pessoal(current_user.id), None)


@router.patch("/board", response_model=BoardSchema)
async def atualizar_board_pessoal(
    dados: BoardUpdateSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> BoardSchema:
    return await quadros.atualizar_apresentacao(
        db,
        quadros.escopo_pessoal(current_user.id),
        None,
        dados.title,
        dados.description,
    )


@router.post("/columns", response_model=ColumnPublicSchema, status_code=status.HTTP_201_CREATED)
async def criar_coluna_pessoal(
    dados: ColumnCreateSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> ColumnPublicSchema:
    return await quadros.criar_coluna(
        db, quadros.escopo_pessoal(current_user.id), None, dados.title
    )


@router.patch("/columns/{column_id}", response_model=ColumnPublicSchema)
async def atualizar_coluna_pessoal(
    column_id: UUID,
    dados: ColumnUpdateSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> ColumnPublicSchema:
    return await quadros.atualizar_coluna(
        db,
        quadros.escopo_pessoal(current_user.id),
        None,
        column_id,
        title=dados.title,
        is_done=dados.is_done,
        campos=dados.model_fields_set,
    )


@router.get("/columns/{column_id}/tasks", response_model=TaskPageSchema)
async def pagina_conclusao_pessoal(
    column_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    offset: int = Query(default=0, ge=0),
) -> TaskPageSchema:
    return await quadros.listar_pagina_conclusao(
        db,
        quadros.escopo_pessoal(current_user.id),
        None,
        column_id,
        offset,
    )


@router.delete("/columns/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_coluna_pessoal(
    column_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    await quadros.remover_coluna(db, quadros.escopo_pessoal(current_user.id), None, column_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("", response_model=TaskPublicSchema, status_code=status.HTTP_201_CREATED)
async def criar_tarefa_pessoal(
    dados: TaskCreateSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskPublicSchema:
    return await quadros.criar_tarefa(
        db,
        quadros.escopo_pessoal(current_user.id),
        None,
        title=dados.title,
        description=dados.description,
        column_id=dados.column_id,
        due_date=dados.due_date,
        processo_id=dados.processo_id,
        assigned_to_member_id=None,
        autor_id=current_user.id,
    )


@router.patch("/{task_id}", response_model=TaskPublicSchema)
async def atualizar_tarefa_pessoal(
    task_id: UUID,
    dados: TaskUpdateSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskPublicSchema:
    return await quadros.atualizar_tarefa(
        db,
        quadros.escopo_pessoal(current_user.id),
        None,
        task_id,
        dados,
        current_user.id,
    )


@router.post("/{task_id}/move", response_model=TaskPublicSchema)
async def mover_tarefa_pessoal(
    task_id: UUID,
    dados: TaskMoveSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskPublicSchema:
    return await quadros.mover_tarefa(
        db,
        quadros.escopo_pessoal(current_user.id),
        None,
        task_id,
        dados.column_id,
        dados.position,
        current_user.id,
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_tarefa_pessoal(
    task_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    await quadros.excluir_tarefa(
        db,
        quadros.escopo_pessoal(current_user.id),
        None,
        task_id,
        current_user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router_org.get("/tasks/board", response_model=BoardSchema)
async def board_org(member: CurrentOrgMember, db: DbSession) -> BoardSchema:
    return await quadros.obter_board(db, quadros.escopo_da_org(member), member)


@router_org.patch("/tasks/board", response_model=BoardSchema)
async def atualizar_board_org(
    dados: BoardUpdateSchema,
    member: MembroColunas,
    db: DbSession,
) -> BoardSchema:
    return await quadros.atualizar_apresentacao(
        db,
        quadros.escopo_da_org(member),
        member,
        dados.title,
        dados.description,
    )


@router_org.post(
    "/kanban/columns",
    response_model=ColumnPublicSchema,
    status_code=status.HTTP_201_CREATED,
)
async def criar_coluna_org(
    dados: ColumnCreateSchema,
    member: MembroColunas,
    db: DbSession,
) -> ColumnPublicSchema:
    return await quadros.criar_coluna(db, quadros.escopo_da_org(member), member, dados.title)


@router_org.patch("/kanban/columns/{column_id}", response_model=ColumnPublicSchema)
async def atualizar_coluna_org(
    column_id: UUID,
    dados: ColumnUpdateSchema,
    member: MembroColunas,
    db: DbSession,
) -> ColumnPublicSchema:
    return await quadros.atualizar_coluna(
        db,
        quadros.escopo_da_org(member),
        member,
        column_id,
        title=dados.title,
        is_done=dados.is_done,
        campos=dados.model_fields_set,
    )


@router_org.get("/kanban/columns/{column_id}/tasks", response_model=TaskPageSchema)
async def pagina_conclusao_org(
    column_id: UUID,
    member: CurrentOrgMember,
    db: DbSession,
    offset: int = Query(default=0, ge=0),
) -> TaskPageSchema:
    return await quadros.listar_pagina_conclusao(
        db,
        quadros.escopo_da_org(member),
        member,
        column_id,
        offset,
    )


@router_org.delete("/kanban/columns/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_coluna_org(
    column_id: UUID,
    member: MembroColunas,
    db: DbSession,
) -> Response:
    await quadros.remover_coluna(db, quadros.escopo_da_org(member), member, column_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router_org.post("/tasks", response_model=TaskPublicSchema, status_code=status.HTTP_201_CREATED)
async def criar_tarefa_org(
    dados: TaskCreateOrgSchema,
    member: CurrentOrgMember,
    db: DbSession,
) -> TaskPublicSchema:
    return await quadros.criar_tarefa(
        db,
        quadros.escopo_da_org(member),
        member,
        title=dados.title,
        description=dados.description,
        column_id=dados.column_id,
        due_date=dados.due_date,
        processo_id=dados.processo_id,
        assigned_to_member_id=dados.assigned_to_member_id,
        autor_id=member.user_id,
    )


@router_org.patch("/tasks/{task_id}", response_model=TaskPublicSchema)
async def atualizar_tarefa_org(
    task_id: UUID,
    dados: TaskUpdateOrgSchema,
    member: CurrentOrgMember,
    db: DbSession,
) -> TaskPublicSchema:
    return await quadros.atualizar_tarefa(
        db,
        quadros.escopo_da_org(member),
        member,
        task_id,
        dados,
        member.user_id,
    )


@router_org.post("/tasks/{task_id}/move", response_model=TaskPublicSchema)
async def mover_tarefa_org(
    task_id: UUID,
    dados: TaskMoveSchema,
    member: CurrentOrgMember,
    db: DbSession,
) -> TaskPublicSchema:
    return await quadros.mover_tarefa(
        db,
        quadros.escopo_da_org(member),
        member,
        task_id,
        dados.column_id,
        dados.position,
        member.user_id,
    )


@router_org.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_tarefa_org(
    task_id: UUID,
    member: CurrentOrgMember,
    db: DbSession,
) -> Response:
    await quadros.excluir_tarefa(
        db,
        quadros.escopo_da_org(member),
        member,
        task_id,
        member.user_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
