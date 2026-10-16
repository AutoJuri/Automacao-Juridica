"""Autorização de organização.

O papel não vai no JWT: cada request lê `organization_members` no banco.
`organization_id` no path só identifica o recurso — sem a linha de membership
a rota responde 403.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.sql.elements import ColumnElement

from app.api.deps import CurrentUser, DbSession
from app.models.organization import (
    ROLE_ADMIN,
    ROLE_OWNER,
    OrganizationMember,
)
from app.models.task import Task

# Matriz usada pelas rotas. Teste unitário trava estes conjuntos.
ACOES_POR_PAPEL: dict[str, frozenset[str]] = {
    "convidar": frozenset({ROLE_OWNER, ROLE_ADMIN}),
    "remover_outro_membro": frozenset({ROLE_OWNER, ROLE_ADMIN}),
    "alterar_papel": frozenset({ROLE_OWNER, ROLE_ADMIN}),
    "configurar": frozenset({ROLE_OWNER, ROLE_ADMIN}),
    "excluir_organizacao": frozenset({ROLE_OWNER}),
    "transferir_ownership": frozenset({ROLE_OWNER}),
    "configurar_colunas": frozenset({ROLE_OWNER, ROLE_ADMIN}),
    "mover_qualquer_tarefa": frozenset({ROLE_OWNER, ROLE_ADMIN}),
    "excluir_qualquer_tarefa": frozenset({ROLE_OWNER, ROLE_ADMIN}),
}


def pode_editar_ou_mover_tarefa(
    papel: str,
    *,
    created_by: UUID,
    assigned_to: UUID | None,
    user_id: UUID,
) -> bool:
    """Owner e admin movem qualquer tarefa. Os demais, só as que criaram ou receberam."""
    if papel_autorizado(papel, "mover_qualquer_tarefa"):
        return True
    return user_id == created_by or (assigned_to is not None and user_id == assigned_to)


def pode_excluir_tarefa(papel: str, *, created_by: UUID, user_id: UUID) -> bool:
    """Owner e admin excluem qualquer tarefa. Os demais, só as que criaram."""
    if papel_autorizado(papel, "excluir_qualquer_tarefa"):
        return True
    return user_id == created_by


def ve_todas_as_tarefas(papel: str) -> bool:
    return papel_autorizado(papel, "mover_qualquer_tarefa")


def filtro_visibilidade_tarefas(member: OrganizationMember) -> ColumnElement[bool]:
    """Cláusula SQL do quadro da organização. Advogado, assistente e estagiário não veem tarefa alheia."""
    escopo = Task.organization_id == member.organization_id
    if ve_todas_as_tarefas(member.role):
        return escopo
    return and_(
        escopo,
        or_(Task.created_by == member.user_id, Task.assigned_to == member.user_id),
    )


def papel_autorizado(role: str, acao: str) -> bool:
    return role in ACOES_POR_PAPEL[acao]


async def get_current_org_member(
    org_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> OrganizationMember:
    """Membro da organização do path. Quem não é membro recebe 403."""
    member = await db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == current_user.id,
        )
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não é membro desta organização",
        )
    return member


def require_role(roles: frozenset[str]):
    """Dependency: o membro do path precisa ter um dos papéis."""

    async def _checker(
        member: Annotated[OrganizationMember, Depends(get_current_org_member)],
    ) -> OrganizationMember:
        if member.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para esta ação",
            )
        return member

    return _checker


CurrentOrgMember = Annotated[OrganizationMember, Depends(get_current_org_member)]
