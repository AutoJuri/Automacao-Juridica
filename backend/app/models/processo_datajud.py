"""Complemento somente-leitura do DataJud (CNJ) para um processo já
rastreado. Etapa 9 / ver `docs/modulos/datajud.md` e ADR-015.

Uma linha por `Processo` (1:1) — nunca sobrescreve campos de `Processo`
(que continuam vindo só do e-SAJ). `encontrado=False` significa que o
DataJud foi consultado mas não tem (ainda) o processo indexado — não é
erro, é um estado normal (defasagem de replicação do CNJ).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.processo import Processo


class ProcessoDatajud(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "processos_datajud"

    processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processos.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    # Alias do índice consultado (ex.: "tjsp", "trf3") — não é o `tribunal`
    # do e-SAJ, é o alias resolvido por `app.core.cnj.resolver_alias_datajud`.
    tribunal_alias: Mapped[str] = mapped_column(String(30), nullable=False)
    classe_codigo: Mapped[str | None] = mapped_column(String(20))
    classe_nome: Mapped[str | None] = mapped_column(String(255))
    # [{codigo, nome}, ...] — padrão TPU, pode ter mais de um assunto.
    assuntos: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    orgao_julgador: Mapped[str | None] = mapped_column(String(255))
    data_ajuizamento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    grau: Mapped[str | None] = mapped_column(String(10))
    formato: Mapped[str | None] = mapped_column(String(50))
    # [{codigo, nome, data_hora}, ...] — movimentos públicos do DataJud,
    # nunca confundir com `Movimentacao` (essa vem do CPO do e-SAJ).
    movimentos: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    # False = DataJud consultado, processo ainda não indexado por lá.
    encontrado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ultima_consulta_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    processo: Mapped["Processo"] = relationship(back_populates="datajud")

    def __repr__(self) -> str:
        return f"<ProcessoDatajud processo={self.processo_id} encontrado={self.encontrado}>"
