"""Pasta do Drive do usuário.

Só a pasta mora aqui. O arquivo, quando existir, fica no Google Drive da
pessoa (ADR-022). O vínculo com um processo é opcional e some junto com o
processo sem apagar a pasta.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.drive_arquivo import DriveArquivo
    from app.models.processo import Processo
    from app.models.user import User


class DrivePasta(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "drive_pastas"
    __table_args__ = (Index("ix_drive_pastas_user_id_updated_at", "user_id", "updated_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    processo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processos.id", ondelete="SET NULL"),
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    # Nula até o primeiro envio; a pasta no Google nasce sob demanda.
    google_folder_id: Mapped[str | None] = mapped_column(String(100))

    user: Mapped["User"] = relationship()
    processo: Mapped["Processo | None"] = relationship()
    arquivos: Mapped[list["DriveArquivo"]] = relationship(
        back_populates="pasta", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<DrivePasta {self.nome}>"
