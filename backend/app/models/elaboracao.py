"""Capa de uma elaboração de peça.

Uma linha por (usuário, processo, peça) quando há processo. Sem processo,
os dados da capa foram digitados à mão e não há limite de quantidade.
O texto da minuta no editor continua no navegador. Quando a IA gera ou
edita, cada versão fica cifrada em `elaboracao_versoes` (ADR-016).
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, LargeBinary, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

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
    fatos_extras_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    estilo_perfil_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)

    user: Mapped["User"] = relationship()
    processo: Mapped["Processo | None"] = relationship()
    versoes: Mapped[list["ElaboracaoVersao"]] = relationship(
        back_populates="elaboracao",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ElaboracaoVersao.created_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<Elaboracao {self.peca} processo={self.processo_id}>"


ORIGEM_GERACAO = "geracao"
ORIGEM_CHAT = "chat"
ORIGEM_GRIFO = "grifo"
ORIGENS_VERSAO = (ORIGEM_GERACAO, ORIGEM_CHAT, ORIGEM_GRIFO)


class ElaboracaoVersao(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "elaboracao_versoes"
    __table_args__ = (
        Index("ix_elaboracao_versoes_elaboracao_id_created_at", "elaboracao_id", "created_at"),
    )

    elaboracao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("elaboracoes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    origem: Mapped[str] = mapped_column(String(20), nullable=False)
    instrucao_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    trecho_alvo_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    conteudo_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    llm_provider: Mapped[str] = mapped_column(String(30), nullable=False)
    llm_model: Mapped[str | None] = mapped_column(Text)

    elaboracao: Mapped["Elaboracao"] = relationship(back_populates="versoes")

    def __repr__(self) -> str:
        return f"<ElaboracaoVersao {self.origem} elaboracao={self.elaboracao_id}>"
