"""Model de usuário do painel."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.audiencia import Audiencia
    from app.models.intimacao import Intimacao
    from app.models.job_log import JobLog
    from app.models.notification import Notification
    from app.models.processo import Processo
    from app.models.tribunal import TribunalCredential, TribunalSession


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    credentials: Mapped[list["TribunalCredential"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    sessions: Mapped[list["TribunalSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    processos: Mapped[list["Processo"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    intimacoes: Mapped[list["Intimacao"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    audiencias: Mapped[list["Audiencia"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    job_logs: Mapped[list["JobLog"]] = relationship(
        back_populates="user", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
