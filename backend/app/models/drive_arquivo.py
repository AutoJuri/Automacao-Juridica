"""Ficha de um arquivo do Drive. O byte mora no Google Drive da pessoa (ADR-022)."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.drive_pasta import DrivePasta
    from app.models.user import User

ORIGEM_UPLOAD = "upload"
ORIGEM_DRIVE = "drive"
ORIGEM_ELABORACAO = "elaboracao"
ORIGENS_ARQUIVO = (ORIGEM_UPLOAD, ORIGEM_DRIVE, ORIGEM_ELABORACAO)


class DriveArquivo(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "drive_arquivos"
    __table_args__ = (
        UniqueConstraint("pasta_id", "google_file_id", name="uq_drive_arquivos_pasta_id_google_file_id"),
        CheckConstraint(
            "origem IN ('upload', 'drive', 'elaboracao')",
            name="ck_drive_arquivos_origem",
        ),
        Index("ix_drive_arquivos_pasta_id_created_at", "pasta_id", "created_at"),
        Index("ix_drive_arquivos_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    pasta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("drive_pastas.id", ondelete="CASCADE"),
        nullable=False,
    )
    google_file_id: Mapped[str] = mapped_column(String(100), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(150), nullable=False)
    tamanho: Mapped[int | None] = mapped_column(BigInteger)
    origem: Mapped[str] = mapped_column(String(20), nullable=False)
    ausente_no_google: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    user: Mapped["User"] = relationship()
    pasta: Mapped["DrivePasta"] = relationship(back_populates="arquivos")

    def __repr__(self) -> str:
        return f"<DriveArquivo {self.id}>"
