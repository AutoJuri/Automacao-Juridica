"""Quadro Kanban: colunas por contexto e tarefas.

Pessoal: `organization_id` nulo e `user_id` preenchido na coluna; a tarefa
fica com `created_by` do dono. Organização: o inverso. Os dois nunca vêm
preenchidos juntos (CHECK em `kanban_columns`).
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

MAX_COLUNAS = 4
LIMITE_TITULO_COLUNA = 40
LIMITE_TITULO_TAREFA = 120
LIMITE_DESCRICAO = 2000
LIMITE_TITULO_QUADRO = 80
LIMITE_DESCRICAO_QUADRO = 280
TITULO_QUADRO_PADRAO = "Tarefas"
DESCRICAO_QUADRO_PESSOAL = "Suas tarefas. O responsável é você."
DESCRICAO_QUADRO_ORG = (
    "Tarefas desta organização. Escolha um membro como responsável e, se quiser, um processo."
)

COLUNAS_PADRAO: tuple[tuple[str, bool], ...] = (
    ("A fazer", False),
    ("Em andamento", False),
    ("Concluído", True),
)


class KanbanBoard(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Nome e frase do quadro. Uma linha por contexto; sem linha, a API devolve o padrão."""

    __tablename__ = "kanban_boards"
    __table_args__ = (
        CheckConstraint(
            "(organization_id IS NOT NULL AND user_id IS NULL) OR "
            "(organization_id IS NULL AND user_id IS NOT NULL)",
            name="escopo",
        ),
        CheckConstraint(
            f"char_length(title) >= 1 AND char_length(title) <= {LIMITE_TITULO_QUADRO}",
            name="title_len",
        ),
        CheckConstraint(
            f"char_length(description) <= {LIMITE_DESCRICAO_QUADRO}",
            name="description_len",
        ),
        Index(
            "uq_kanban_boards_org",
            "organization_id",
            unique=True,
            postgresql_where=text("organization_id IS NOT NULL"),
        ),
        Index(
            "uq_kanban_boards_user",
            "user_id",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL"),
        ),
    )

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    title: Mapped[str] = mapped_column(String(LIMITE_TITULO_QUADRO), nullable=False)
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default=text("''"),
    )

    def __repr__(self) -> str:
        return f"<KanbanBoard {self.title}>"


class KanbanColumn(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "kanban_columns"
    __table_args__ = (
        CheckConstraint(
            "(organization_id IS NOT NULL AND user_id IS NULL) OR "
            "(organization_id IS NULL AND user_id IS NOT NULL)",
            name="escopo",
        ),
        CheckConstraint("position >= 0 AND position <= 3", name="position_range"),
        Index(
            "uq_kanban_columns_org_position",
            "organization_id",
            "position",
            unique=True,
            postgresql_where=text("organization_id IS NOT NULL"),
        ),
        Index(
            "uq_kanban_columns_user_position",
            "user_id",
            "position",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL"),
        ),
        Index(
            "uq_kanban_columns_org_done",
            "organization_id",
            unique=True,
            postgresql_where=text("is_done AND organization_id IS NOT NULL"),
        ),
        Index(
            "uq_kanban_columns_user_done",
            "user_id",
            unique=True,
            postgresql_where=text("is_done AND user_id IS NOT NULL"),
        ),
    )

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    title: Mapped[str] = mapped_column(String(LIMITE_TITULO_COLUNA), nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_done: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))

    def __repr__(self) -> str:
        return f"<KanbanColumn {self.title} pos={self.position}>"


class Task(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(f"char_length(description) <= {LIMITE_DESCRICAO}", name="description_len"),
        Index("ix_tasks_org_column_position", "organization_id", "column_id", "position"),
        Index("ix_tasks_assigned_to", "assigned_to"),
        Index("ix_tasks_created_by", "created_by"),
    )

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
    )
    column_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kanban_columns.id", ondelete="RESTRICT"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(LIMITE_TITULO_TAREFA), nullable=False)
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default=text("''"),
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    processo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processos.id", ondelete="SET NULL"),
    )
    due_date: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<Task {self.title}>"


__all__ = [
    "COLUNAS_PADRAO",
    "DESCRICAO_QUADRO_ORG",
    "DESCRICAO_QUADRO_PESSOAL",
    "KanbanBoard",
    "KanbanColumn",
    "LIMITE_DESCRICAO",
    "LIMITE_DESCRICAO_QUADRO",
    "LIMITE_TITULO_COLUNA",
    "LIMITE_TITULO_QUADRO",
    "LIMITE_TITULO_TAREFA",
    "MAX_COLUNAS",
    "TITULO_QUADRO_PADRAO",
    "Task",
]
