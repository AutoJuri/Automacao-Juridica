"""Model de notificação exibida no painel."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.processo import Processo
    from app.models.user import User

NOTIFICATION_TIPO_MOVIMENTACAO = "movimentacao"
NOTIFICATION_TIPO_INTIMACAO = "intimacao"
NOTIFICATION_TIPO_AUDIENCIA = "audiencia"
NOTIFICATION_TIPO_SISTEMA = "sistema"

NOTIFICATION_TIPOS = (
    NOTIFICATION_TIPO_MOVIMENTACAO,
    NOTIFICATION_TIPO_INTIMACAO,
    NOTIFICATION_TIPO_AUDIENCIA,
    NOTIFICATION_TIPO_SISTEMA,
)


class Notification(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "notifications"
    # O painel lista sempre "não lidas do usuário".
    __table_args__ = (Index("ix_notifications_user_id_is_read", "user_id", "is_read"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    processo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processos.id", ondelete="SET NULL"),
        index=True,
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(nullable=False, server_default="false", default=False)

    user: Mapped["User"] = relationship(back_populates="notifications")
    processo: Mapped["Processo | None"] = relationship(back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification {self.tipo} read={self.is_read}>"


__all__ = [
    "NOTIFICATION_TIPOS",
    "NOTIFICATION_TIPO_AUDIENCIA",
    "NOTIFICATION_TIPO_INTIMACAO",
    "NOTIFICATION_TIPO_MOVIMENTACAO",
    "NOTIFICATION_TIPO_SISTEMA",
    "Notification",
]
