"""Model de processo monitorado."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.audiencia import Audiencia
    from app.models.audiencia_cpo import AudienciaCpo
    from app.models.intimacao import Intimacao
    from app.models.movimentacao import Movimentacao
    from app.models.notification import Notification
    from app.models.peticao_diversa import PeticaoDiversa
    from app.models.user import User


class Processo(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "processos"
    __table_args__ = (
        UniqueConstraint("user_id", "cd_processo"),
        Index(
            "ix_processos_user_id_movimentacoes_synced_at",
            "user_id",
            "movimentacoes_synced_at",
            postgresql_where=text("url_cpo IS NOT NULL"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tribunal: Mapped[str] = mapped_column(String(50), nullable=False)
    # Código interno do e-SAJ (cdProcesso).
    cd_processo: Mapped[str] = mapped_column(String(100), nullable=False)
    # Número CNJ formatado.
    nu_processo: Mapped[str | None] = mapped_column(String(50), index=True)
    de_classe: Mapped[str | None] = mapped_column(String(255))
    de_assunto: Mapped[str | None] = mapped_column(String(255))
    instancia: Mapped[str | None] = mapped_column(String(10))
    # {nome, nomeSocial, representada}
    parte_ativa: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # {nome, representada}
    parte_passiva: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    url_cpo: Mapped[str | None] = mapped_column(String(500))
    url_pasta: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str | None] = mapped_column(String(50))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Último fetch do HTML do CPO (independente de ter achado movimentação
    # nova) — usado pelo throttle do pipe de movimentações para dar
    # round-robin entre ciclos em vez de buscar todos os processos a cada
    # 10 min (ADR-012). Nulo = nunca buscado, prioridade máxima no lote.
    movimentacoes_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Capa complementar do HTML do CPO — o JSON de processos não traz esses
    # campos (ADR-013). Texto do portal, sem parse de moeda.
    foro: Mapped[str | None] = mapped_column(String(255))
    vara: Mapped[str | None] = mapped_column(String(255))
    juiz: Mapped[str | None] = mapped_column(String(255))
    distribuicao: Mapped[str | None] = mapped_column(String(255))
    controle: Mapped[str | None] = mapped_column(String(50))
    area: Mapped[str | None] = mapped_column(String(50))
    valor_acao: Mapped[str | None] = mapped_column(String(100))
    # Lista [{papel, nome, advogados}] de `tableTodasPartes`. Polo JSON
    # (`parte_ativa` / `parte_passiva`) continua sendo a fonte do card.
    partes_cpo: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    # None = CPO ainda não passou por este processo; True = empty state do portal.
    sem_incidentes: Mapped[bool | None] = mapped_column()
    sem_apensos: Mapped[bool | None] = mapped_column()
    # Preferência do advogado na lista da home — não vem do e-SAJ.
    fixado: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=text("false")
    )

    user: Mapped["User"] = relationship(back_populates="processos")
    movimentacoes: Mapped[list["Movimentacao"]] = relationship(
        back_populates="processo", cascade="all, delete-orphan", passive_deletes=True
    )
    peticoes_diversas: Mapped[list["PeticaoDiversa"]] = relationship(
        back_populates="processo", cascade="all, delete-orphan", passive_deletes=True
    )
    audiencias_cpo: Mapped[list["AudienciaCpo"]] = relationship(
        back_populates="processo", cascade="all, delete-orphan", passive_deletes=True
    )
    intimacoes: Mapped[list["Intimacao"]] = relationship(
        back_populates="processo", passive_deletes=True
    )
    audiencias: Mapped[list["Audiencia"]] = relationship(
        back_populates="processo", passive_deletes=True
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="processo", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<Processo {self.nu_processo or self.cd_processo}>"
