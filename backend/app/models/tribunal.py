"""Credenciais e sessões dos portais de tribunal (e-SAJ)."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User

TRIBUNAL_ESAJ_TJSP = "esaj_tjsp"

EMAIL_PROVIDERS = ("gmail", "outlook")

# Estados possíveis de uma sessão no portal — ver PRD seção 9.
SESSION_STATUS_ATIVO = "ativo"
SESSION_STATUS_REAUTH_PENDENTE = "reauth_pendente"
SESSION_STATUS_BLOQUEADO = "bloqueado"
SESSION_STATUS_CREDENCIAL_INVALIDA = "credencial_invalida"
SESSION_STATUS_EMAIL_DESCONECTADO = "email_desconectado"
SESSION_STATUS_PORTAL_INDISPONIVEL = "portal_indisponivel"

SESSION_STATUSES = (
    SESSION_STATUS_ATIVO,
    SESSION_STATUS_REAUTH_PENDENTE,
    SESSION_STATUS_BLOQUEADO,
    SESSION_STATUS_CREDENCIAL_INVALIDA,
    SESSION_STATUS_EMAIL_DESCONECTADO,
    SESSION_STATUS_PORTAL_INDISPONIVEL,
)


class TribunalCredential(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "tribunal_credentials"
    # Um advogado só tem uma credencial ativa por tribunal.
    __table_args__ = (UniqueConstraint("user_id", "tribunal"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tribunal: Mapped[str] = mapped_column(String(50), nullable=False)
    cpf_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    senha_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    email_provider: Mapped[str | None] = mapped_column(String(20))
    email_oauth_token_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default="true", default=True)

    user: Mapped["User"] = relationship(back_populates="credentials")

    def __repr__(self) -> str:
        return f"<TribunalCredential {self.tribunal} user={self.user_id}>"


class TribunalSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tribunal_sessions"
    __table_args__ = (
        # Um advogado só tem uma sessão ativa por tribunal.
        UniqueConstraint("user_id", "tribunal"),
        # O scheduler filtra sessões pendentes de retry por status.
        Index("ix_tribunal_sessions_status_proximo_retry", "status", "proximo_retry"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tribunal: Mapped[str] = mapped_column(String(50), nullable=False)
    # JSESSIONID + CASTGC criptografados (AES-256).
    cookie_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=SESSION_STATUS_ATIVO
    )
    ultimo_erro: Mapped[str | None] = mapped_column(Text)
    tentativas_falha: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0", default=0
    )
    proximo_retry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultimo_sucesso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="sessions")

    def __repr__(self) -> str:
        return f"<TribunalSession {self.tribunal} status={self.status}>"


__all__ = [
    "EMAIL_PROVIDERS",
    "SESSION_STATUSES",
    "SESSION_STATUS_ATIVO",
    "SESSION_STATUS_BLOQUEADO",
    "SESSION_STATUS_CREDENCIAL_INVALIDA",
    "SESSION_STATUS_EMAIL_DESCONECTADO",
    "SESSION_STATUS_PORTAL_INDISPONIVEL",
    "SESSION_STATUS_REAUTH_PENDENTE",
    "TRIBUNAL_ESAJ_TJSP",
    "TribunalCredential",
    "TribunalSession",
]
