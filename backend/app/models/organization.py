"""Organizações, membros e convites.

Papéis são VARCHAR + constantes (ADR-002). O token do convite nunca é
persistido em claro: só `token_hash` (SHA-256), no mesmo espírito do refresh
e da recuperação de senha.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User

ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_ADVOGADO = "advogado"
ROLE_ASSISTENTE = "assistente"
ROLE_ESTAGIARIO = "estagiario"

ROLES = (ROLE_OWNER, ROLE_ADMIN, ROLE_ADVOGADO, ROLE_ASSISTENTE, ROLE_ESTAGIARIO)
# Owner nasce na criação da organização ou na transferência. Convite não promove.
ROLES_CONVIDAVEIS = (ROLE_ADMIN, ROLE_ADVOGADO, ROLE_ASSISTENTE, ROLE_ESTAGIARIO)

ROTULO_PAPEL = {
    ROLE_OWNER: "Owner",
    ROLE_ADMIN: "Admin",
    ROLE_ADVOGADO: "Advogado",
    ROLE_ASSISTENTE: "Assistente",
    ROLE_ESTAGIARIO: "Estagiário",
}


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    members: Mapped[list["OrganizationMember"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    invites: Mapped[list["OrganizationInvite"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Organization {self.slug}>"


class OrganizationMember(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "organization_members"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id"),
        Index("ix_organization_members_user_id", "user_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    invited_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    organization: Mapped[Organization] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<OrganizationMember org={self.organization_id} role={self.role}>"


class OrganizationInvite(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "organization_invites"
    __table_args__ = (
        Index(
            "uq_organization_invites_pending_email",
            "organization_id",
            "email",
            unique=True,
            postgresql_where=text("accepted_at IS NULL AND revoked_at IS NULL"),
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    invited_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    organization: Mapped[Organization] = relationship(back_populates="invites")

    def __repr__(self) -> str:
        return f"<OrganizationInvite org={self.organization_id} aceito={self.accepted_at is not None}>"
