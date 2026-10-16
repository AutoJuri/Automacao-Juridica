"""Capa de uma elaboração de peça.

Uma linha por (usuário, processo, peça) quando há processo. Sem processo,
os dados da capa foram digitados à mão e não há limite de quantidade.
O texto da minuta não fica aqui — continua no navegador até a etapa da IA.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.processo import Processo
    from app.models.user import User

PECAS: dict[str, str] = {
    "contestacao": "Contestação",
    "replica": "Réplica",
    "recurso_inominado": "Recurso Inominado",
    "apelacao": "Apelação",
    "agravo_interno": "Agravo Interno",
    "memoriais": "Memoriais",
    "peticao_inicial": "Petição Inicial",
    "tutela_urgencia": "Tutela de Urgência",
    "impugnacao_contestacao": "Impugnação à Contestação",
    "embargos_declaracao": "Embargos de Declaração",
}

_MANUAIS_NULOS = " AND ".join(
    f"{coluna} IS NULL"
    for coluna in (
        "titulo",
        "nu_processo",
        "parte_ativa",
        "parte_passiva",
        "classe",
        "assunto",
        "foro_vara",
        "valor_causa",
        "juiz",
    )
)


class Elaboracao(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "elaboracoes"
    __table_args__ = (
        CheckConstraint(
            "processo_id IS NOT NULL OR titulo IS NOT NULL",
            name="origem",
        ),
        CheckConstraint(
            f"processo_id IS NULL OR ({_MANUAIS_NULOS})",
            name="manual_so_sem_processo",
        ),
        Index(
            "uq_elaboracoes_user_processo_peca",
            "user_id",
            "processo_id",
            "peca",
            unique=True,
            postgresql_where=text("processo_id IS NOT NULL"),
        ),
        Index("ix_elaboracoes_user_id_updated_at", "user_id", "updated_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    processo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processos.id", ondelete="CASCADE"),
    )
    peca: Mapped[str] = mapped_column(String(100), nullable=False)
    titulo: Mapped[str | None] = mapped_column(String(120))
    nu_processo: Mapped[str | None] = mapped_column(String(50))
    parte_ativa: Mapped[str | None] = mapped_column(String(255))
    parte_passiva: Mapped[str | None] = mapped_column(String(255))
    classe: Mapped[str | None] = mapped_column(String(255))
    assunto: Mapped[str | None] = mapped_column(String(255))
    foro_vara: Mapped[str | None] = mapped_column(String(255))
    valor_causa: Mapped[str | None] = mapped_column(String(100))
    juiz: Mapped[str | None] = mapped_column(String(255))

    user: Mapped["User"] = relationship()
    processo: Mapped["Processo | None"] = relationship()

    def __repr__(self) -> str:
        return f"<Elaboracao {self.peca} processo={self.processo_id}>"
