"""Audiência listada no HTML do CPO (futuras daquele processo).

Não misturar com `audiencias` (agenda JSON da carteira, ADR-010 / ADR-013).
"""

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


class AudienciaCpo(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "audiencias_cpo"
    __table_args__ = (UniqueConstraint("processo_id", "identidade_hash"),)

    processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data_audiencia: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    situacao: Mapped[str | None] = mapped_column(String(100))
    qt_pessoas: Mapped[str | None] = mapped_column(String(20))
    identidade_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    processo: Mapped["Processo"] = relationship(back_populates="audiencias_cpo")

    def __repr__(self) -> str:
        return f"<AudienciaCpo {self.titulo} processo={self.processo_id}>"
