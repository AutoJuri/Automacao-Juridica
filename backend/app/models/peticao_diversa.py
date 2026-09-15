"""Petição diversa extraída do HTML do CPO — não é o rascunho de `tarefas-adv`."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.processo import Processo


class PeticaoDiversa(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "peticoes_diversas"
    # Identidade estável: protocolo quando o HTML traz; senão hash de
    # data|tipo|texto_extra (várias "Petição Intermediária" no mesmo dia).
    __table_args__ = (UniqueConstraint("processo_id", "identidade_hash"),)

    processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data_peticao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    tipo: Mapped[str] = mapped_column(String(255), nullable=False)
    protocolo: Mapped[str | None] = mapped_column(String(100))
    identidade_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    processo: Mapped["Processo"] = relationship(back_populates="peticoes_diversas")

    def __repr__(self) -> str:
        return f"<PeticaoDiversa {self.tipo} processo={self.processo_id}>"
