"""Schemas públicos das notificações in-app.

`id_esaj` nunca entra aqui — o id público é o UUID da `notifications`.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    processo_id: UUID | None = None
    tipo: str
    titulo: str
    message: str
    is_read: bool
    created_at: datetime


class NotificationLidaSchema(BaseModel):
    is_read: bool = True


class NotificationsMarcadasSchema(BaseModel):
    marcadas: int = Field(ge=0)
