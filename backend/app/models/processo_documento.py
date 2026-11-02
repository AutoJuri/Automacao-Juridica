"""Ficha cifrada de cada documento lido e o dossiê consolidado (ADR-024).

O PDF não tem coluna. `ficha_encrypted` e `resumo_encrypted` são AES-256-GCM
(`encrypt_secret`). Texto de página não é persistido.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

STATUS_DOC_PENDENTE = "pendente"
STATUS_DOC_LIDO = "lido"
STATUS_DOC_PARCIAL = "parcial"
STATUS_DOC_SEM_ACESSO = "sem_acesso"
STATUS_DOC_ILEGIVEL = "ilegivel"
STATUS_DOC_ERRO = "erro"

STATUS_DOC_TERMINAIS = frozenset(
    {
        STATUS_DOC_LIDO,
        STATUS_DOC_PARCIAL,
        STATUS_DOC_SEM_ACESSO,
        STATUS_DOC_ILEGIVEL,
    }
)
STATUS_DOC_REAPROVEITAVEIS = STATUS_DOC_TERMINAIS

STATUS_DOSSIE_OCIOSO = "ocioso"
STATUS_DOSSIE_LENDO = "lendo"
STATUS_DOSSIE_PRONTO = "pronto"
STATUS_DOSSIE_BLOQUEADO = "bloqueado"
STATUS_DOSSIE_SESSAO = "sessao_expirada"
STATUS_DOSSIE_LIMITE = "limite_ia"
STATUS_DOSSIE_ERRO = "erro"
STATUS_DOSSIE_SEM = "sem_documentos"


class ProcessoDocumento(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "processo_documentos"
    __table_args__ = (
        UniqueConstraint("processo_id", "movimentacao_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    movimentacao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("movimentacoes.id", ondelete="CASCADE"),
        nullable=False,
    )
    # SHA-256 da URL lida. Muda a URL, a ficha deixa de valer.
    url_hash: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=STATUS_DOC_PENDENTE)
    paginas: Mapped[int | None] = mapped_column(Integer)
    paginas_ocr: Mapped[int | None] = mapped_column(Integer)
    ficha_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    lido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProcessoDossie(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "processo_dossies"
    __table_args__ = (UniqueConstraint("processo_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processos.id", ondelete="CASCADE"),
        nullable=False,
    )
    resumo_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    fingerprint: Mapped[str | None] = mapped_column(String(64))
    gerado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=STATUS_DOSSIE_OCIOSO
    )
    lidos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retomar_apos: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Lista cifrada das peças da pasta: título, status e ficha. Sem URL e sem PDF.
    pecas_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    # Roteiro confirmado pelo advogado (resumo ajustado, tese, pedidos,
    # jurisprudência colada). AES-256-GCM. Sem URL e sem PDF.
    roteiro_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
