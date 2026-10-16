"""Conexão da pessoa com o Google Drive (ADR-022).

O token (access, refresh, expiração, escopo) fica em AES-256-GCM, no mesmo
padrão de `email_oauth_token_encrypted`. Nunca sai na API e nunca vai ao log.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class DriveConexao(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "drive_conexoes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    token_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    root_folder_id: Mapped[str | None] = mapped_column(String(100))

    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<DriveConexao user_id={self.user_id}>"
