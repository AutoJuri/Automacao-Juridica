"""Sessão de elaboração de peça e histórico de versões (IA — ADR-016).

`Elaboracao` é uma sessão por `(user_id, processo_id, peca)`: guarda os
fatos extras que o advogado digitou (input humano, não vem do e-SAJ).
`ElaboracaoVersao` é cada rascunho gerado ou editado — a "fonte de verdade"
do documento passa a ser o servidor quando a IA está ligada (mesmo em modo
`stub`), em vez do `localStorage` do browser.

Campos com texto do advogado ou da minuta são cifrados com AES-256-GCM
(`app.core.security.encrypt_secret` / `decrypt_secret`) no mesmo espírito do
`security.mdc` para dado processual sigiloso — mesmo não sendo credencial de
terceiro como CPF/senha do e-SAJ.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.processo import Processo
    from app.models.user import User

ORIGEM_GERACAO = "geracao"
ORIGEM_CHAT = "chat"
ORIGEM_GRIFO = "grifo"

ORIGENS_VERSAO = (ORIGEM_GERACAO, ORIGEM_CHAT, ORIGEM_GRIFO)


class Elaboracao(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "elaboracoes"
    __table_args__ = (
        # Uma sessão por peça, por processo, por advogado — reabrir a tela
        # continua a mesma elaboração em vez de duplicar.
        UniqueConstraint("user_id", "processo_id", "peca"),
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
    # Id da peça do seletor do frontend (ex.: "contestacao") — ver
    # `frontend/src/features/elaboracao/elaboracao.mock.ts`.
    peca: Mapped[str] = mapped_column(String(100), nullable=False)
    # Fatos/tese que o advogado digitou — o e-SAJ não tem isso.
    fatos_extras_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    # Perfil de estilo (JSON) extraído do último modelo de peça enviado
    # (ADR-016 Fase 3) — cifrado como todo texto do advogado nesta tabela.
    estilo_perfil_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)

    user: Mapped["User"] = relationship()
    processo: Mapped["Processo"] = relationship()
    versoes: Mapped[list["ElaboracaoVersao"]] = relationship(
        back_populates="elaboracao",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ElaboracaoVersao.created_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<Elaboracao {self.peca} processo={self.processo_id}>"


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
    # Instrução do chat/grifo que gerou esta versão — None na primeira geração.
    instrucao_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    # Trecho selecionado no grifo — None fora do grifo.
    trecho_alvo_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    conteudo_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    # Auditoria/debug — não é segredo, ajuda a saber se saiu do stub ou de
    # um provedor real depois.
    llm_provider: Mapped[str] = mapped_column(String(30), nullable=False)
    llm_model: Mapped[str | None] = mapped_column(Text)

    elaboracao: Mapped["Elaboracao"] = relationship(back_populates="versoes")

    def __repr__(self) -> str:
        return f"<ElaboracaoVersao {self.origem} elaboracao={self.elaboracao_id}>"


__all__ = [
    "ORIGEM_CHAT",
    "ORIGEM_GERACAO",
    "ORIGEM_GRIFO",
    "ORIGENS_VERSAO",
    "Elaboracao",
    "ElaboracaoVersao",
]
