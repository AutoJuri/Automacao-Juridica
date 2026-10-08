"""Schemas de organização, membro e convite.

Nenhum schema de resposta inclui `token`, `token_hash`, senha ou credencial.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PapelConvidavel = Literal["admin", "advogado", "assistente", "estagiario"]


class OrganizationCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def _nome_util(cls, valor: str) -> str:
        nome = valor.strip()
        if len(nome) < 2:
            raise ValueError("Informe o nome da organização")
        return nome


class OrganizationUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def _nome_util(cls, valor: str) -> str:
        nome = valor.strip()
        if len(nome) < 2:
            raise ValueError("Informe o nome da organização")
        return nome


class OrganizationMineSchema(BaseModel):
    id: UUID
    name: str
    slug: str
    role: str


class OrganizationDetailSchema(BaseModel):
    id: UUID
    name: str
    slug: str
    role: str
    created_at: datetime


class MemberPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    role: str
    joined_at: datetime


class MemberRoleUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: PapelConvidavel


class InviteCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(max_length=255)
    role: PapelConvidavel


class InvitePendingSchema(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    expires_at: datetime
    created_at: datetime


class InviteReceivedSchema(BaseModel):
    id: UUID
    organization_name: str
    role: str
    expires_at: datetime
    created_at: datetime


class InvitePreviewSchema(BaseModel):
    organization_name: str
    role: str
    email: EmailStr
    expires_at: datetime


class InviteAcceptedSchema(BaseModel):
    organization_id: UUID
    name: str
    slug: str
    role: str
