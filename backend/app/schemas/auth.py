"""Schemas de entrada e saída das rotas de autenticação.

Nenhum schema de resposta expõe `password_hash` ou qualquer campo `*_encrypted`.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.validators import SENHA_MAX, SENHA_MIN, valida_bytes_da_senha


class UserCreateSchema(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=SENHA_MIN, max_length=SENHA_MAX)

    @field_validator("password")
    @classmethod
    def _valida_password_bytes(cls, v: str) -> str:
        return valida_bytes_da_senha(v)


class UserLoginSchema(BaseModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=1, max_length=SENHA_MAX)


class UserPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    created_at: datetime


class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublicSchema


class ForgotPasswordSchema(BaseModel):
    email: EmailStr = Field(max_length=255)


class ResetPasswordSchema(BaseModel):
    token: str = Field(min_length=1, max_length=512)
    new_password: str = Field(min_length=SENHA_MIN, max_length=SENHA_MAX)

    @field_validator("new_password")
    @classmethod
    def _valida_new_password_bytes(cls, v: str) -> str:
        return valida_bytes_da_senha(v)


class MessageSchema(BaseModel):
    message: str
