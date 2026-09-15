"""Model de audiência vinda do e-SAJ."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.processo import Processo
    from app.models.user import User


class Audiencia(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "audiencias"
    # Unicidade por advogado: evita colisão caso o e-SAJ reaproveite o
    # mesmo id_esaj entre contas diferentes.
    __table_args__ = (UniqueConstraint("user_id", "id_esaj"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    processo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processos.id", ondelete="SET NULL"),
        index=True,
    )
    # A API de audiências não manda id. O ETL grava um composto estável
    # `cdProcesso|{iso}|{titulo}` — ver ADR-010. Nunca UUID por captura.
    id_esaj: Mapped[str] = mapped_column(String(255), nullable=False)
    titulo: Mapped[str | None] = mapped_column(String(255))
    data_audiencia: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    local: Mapped[str | None] = mapped_column(String(255))
    is_new: Mapped[bool] = mapped_column(nullable=False, server_default="true", default=True)

    user: Mapped["User"] = relationship(back_populates="audiencias")
    processo: Mapped["Processo | None"] = relationship(back_populates="audiencias")

    def __repr__(self) -> str:
        return f"<Audiencia {self.id_esaj} {self.data_audiencia}>"
