"""Model de log de execução dos jobs (login, pipes, reauth)."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User

JOB_TIPO_LOGIN = "login"
JOB_TIPO_PIPE_INTIMACOES = "pipe_intimacoes"
JOB_TIPO_PIPE_AUDIENCIAS = "pipe_audiencias"
JOB_TIPO_PIPE_PETICOES = "pipe_peticoes"
JOB_TIPO_PIPE_PROCESSOS = "pipe_processos"
JOB_TIPO_REAUTH = "reauth"

JOB_TIPOS = (
    JOB_TIPO_LOGIN,
    JOB_TIPO_PIPE_INTIMACOES,
    JOB_TIPO_PIPE_AUDIENCIAS,
    JOB_TIPO_PIPE_PETICOES,
    JOB_TIPO_PIPE_PROCESSOS,
    JOB_TIPO_REAUTH,
)

JOB_STATUS_SUCESSO = "sucesso"
JOB_STATUS_FALHA = "falha"
JOB_STATUS_SKIP = "skip"

JOB_STATUSES = (JOB_STATUS_SUCESSO, JOB_STATUS_FALHA, JOB_STATUS_SKIP)


class JobLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "job_logs"

    # Nullable: jobs de sistema não pertencem a um usuário.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    erro: Mapped[str | None] = mapped_column(Text)
    duracao_ms: Mapped[int | None] = mapped_column(Integer)

    user: Mapped["User | None"] = relationship(back_populates="job_logs")

    def __repr__(self) -> str:
        return f"<JobLog {self.tipo} {self.status}>"


__all__ = [
    "JOB_STATUSES",
    "JOB_STATUS_FALHA",
    "JOB_STATUS_SKIP",
    "JOB_STATUS_SUCESSO",
    "JOB_TIPOS",
    "JOB_TIPO_LOGIN",
    "JOB_TIPO_PIPE_AUDIENCIAS",
    "JOB_TIPO_PIPE_INTIMACOES",
    "JOB_TIPO_PIPE_PETICOES",
    "JOB_TIPO_PIPE_PROCESSOS",
    "JOB_TIPO_REAUTH",
    "JobLog",
]
