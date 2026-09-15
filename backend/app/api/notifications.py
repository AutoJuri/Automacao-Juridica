"""Rotas de notificações in-app.

`user_id` vem só do JWT. Notificação de outro advogado responde 404.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.notification import (
    NotificationLidaSchema,
    NotificationPublicSchema,
    NotificationsMarcadasSchema,
)
from app.services import painel

router = APIRouter(prefix="/notifications", tags=["notifications"])

_NAO_ENCONTRADO = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada"
)


@router.get("", response_model=list[NotificationPublicSchema])
async def listar_notificacoes(
    current_user: CurrentUser,
    db: DbSession,
    somente_nao_lidas: bool = Query(default=False),
) -> list[NotificationPublicSchema]:
    return await painel.listar_notificacoes(
        db, current_user.id, somente_nao_lidas=somente_nao_lidas
    )


@router.patch("/{notificacao_id}", response_model=NotificationPublicSchema)
async def marcar_lida(
    notificacao_id: UUID,
    body: NotificationLidaSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> NotificationPublicSchema:
    if not body.is_read:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Só é possível marcar a notificação como lida",
        )
    atualizada = await painel.marcar_notificacao_lida(db, current_user.id, notificacao_id)
    if atualizada is None:
        raise _NAO_ENCONTRADO
    return atualizada


@router.post("/marcar-lidas", response_model=NotificationsMarcadasSchema)
async def marcar_todas_lidas(
    current_user: CurrentUser,
    db: DbSession,
) -> NotificationsMarcadasSchema:
    marcadas = await painel.marcar_todas_lidas(db, current_user.id)
    return NotificationsMarcadasSchema(marcadas=marcadas)
