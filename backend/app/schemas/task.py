"""Contratos do quadro de tarefas.

A resposta nunca leva e-mail, papel ou dado de processo além de id e número.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ColumnCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=40)


class ColumnUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=40)
    is_done: bool | None = None


class ColumnPublicSchema(BaseModel):
    id: UUID
    title: str
    position: int
    is_done: bool
    # Na coluna de conclusão pode ser maior que a lista `tasks` desta resposta.
    task_count: int


class TaskCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    column_id: UUID
    due_date: date | None = None
    processo_id: UUID | None = None


class TaskCreateOrgSchema(TaskCreateSchema):
    assigned_to_member_id: UUID


class TaskUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    due_date: date | None = None
    processo_id: UUID | None = None


class TaskUpdateOrgSchema(TaskUpdateSchema):
    assigned_to_member_id: UUID | None = None


class TaskMoveSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    column_id: UUID
    position: int = Field(ge=0)


class AssigneePublicSchema(BaseModel):
    member_id: UUID | None = None
    name: str


class CreatorPublicSchema(BaseModel):
    name: str


class ProcessoRefSchema(BaseModel):
    id: UUID
    nu_processo: str | None = None


class TaskPublicSchema(BaseModel):
    id: UUID
    column_id: UUID
    position: int
    title: str
    description: str
    assignee: AssigneePublicSchema | None = None
    created_by: CreatorPublicSchema
    processo: ProcessoRefSchema | None = None
    due_date: date | None = None
    is_overdue: bool
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class BoardUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=280)


class BoardSchema(BaseModel):
    title: str
    description: str
    columns: list[ColumnPublicSchema]
    tasks: list[TaskPublicSchema]


class TaskPageSchema(BaseModel):
    tasks: list[TaskPublicSchema]
    total: int
