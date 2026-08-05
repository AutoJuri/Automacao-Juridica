"""Model de processo monitorado."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.audiencia import Audiencia
    from app.models.intimacao import Intimacao
    from app.models.movimentacao import Movimentacao
    from app.models.notification import Notification
    from app.models.user import User


class Processo(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "processos"
    __table_args__ = (UniqueConstraint("user_id", "cd_processo"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tribunal: Mapped[str] = mapped_column(String(50), nullable=False)
    # Código interno do e-SAJ (cdProcesso).
    cd_processo: Mapped[str] = mapped_column(String(100), nullable=False)
    # Número CNJ formatado.
    nu_processo: Mapped[str | None] = mapped_column(String(50), index=True)
    de_classe: Mapped[str | None] = mapped_column(String(255))
    de_assunto: Mapped[str | None] = mapped_column(String(255))
    instancia: Mapped[str | None] = mapped_column(String(10))
    # {nome, nomeSocial, representada}
    parte_ativa: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # {nome, representada}
    parte_passiva: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    url_cpo: Mapped[str | None] = mapped_column(String(500))
    url_pasta: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str | None] = mapped_column(String(50))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="processos")
    movimentacoes: Mapped[list["Movimentacao"]] = relationship(
        back_populates="processo", cascade="all, delete-orphan", passive_deletes=True
    )
    intimacoes: Mapped[list["Intimacao"]] = relationship(
        back_populates="processo", passive_deletes=True
    )
    audiencias: Mapped[list["Audiencia"]] = relationship(
        back_populates="processo", passive_deletes=True
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="processo", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<Processo {self.nu_processo or self.cd_processo}>"
