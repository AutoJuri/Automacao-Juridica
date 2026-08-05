"""Model de intimação vinda do e-SAJ."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.processo import Processo
    from app.models.user import User


class Intimacao(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "intimacoes"
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
    # Id composto devolvido pela API do e-SAJ.
    id_esaj: Mapped[str] = mapped_column(String(255), nullable=False)
    titulo: Mapped[str | None] = mapped_column(String(255))
    descricao: Mapped[str | None] = mapped_column(Text)
    instancia: Mapped[str | None] = mapped_column(String(10))
    data_movimentacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    # Se o advogado já deu ciência no próprio e-SAJ.
    ciencia: Mapped[bool] = mapped_column(nullable=False, server_default="false", default=False)
    is_new: Mapped[bool] = mapped_column(nullable=False, server_default="true", default=True)

    user: Mapped["User"] = relationship(back_populates="intimacoes")
    processo: Mapped["Processo | None"] = relationship(back_populates="intimacoes")

    def __repr__(self) -> str:
        return f"<Intimacao {self.id_esaj}>"
