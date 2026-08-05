"""Model de movimentação processual."""

import hashlib
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.processo import Processo


class Movimentacao(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "movimentacoes"
    # Chave natural do diff do ETL: evita reinserir a mesma movimentação.
    # Usa o hash de descricao (não a coluna Text em si) porque um índice
    # UNIQUE do Postgres não aceita entradas maiores que ~2.7 KB.
    __table_args__ = (
        UniqueConstraint("processo_id", "data_movimentacao", "descricao_hash"),
    )

    processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data_movimentacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    # SHA-256 de `descricao`, preenchido automaticamente via @validates.
    descricao_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    titulo: Mapped[str | None] = mapped_column(String(255))
    instancia: Mapped[str | None] = mapped_column(String(10))
    is_new: Mapped[bool] = mapped_column(nullable=False, server_default="true", default=True)

    processo: Mapped["Processo"] = relationship(back_populates="movimentacoes")

    @validates("descricao")
    def _set_descricao_hash(self, key: str, value: str) -> str:
        self.descricao_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return value

    def __repr__(self) -> str:
        return f"<Movimentacao {self.data_movimentacao} processo={self.processo_id}>"
