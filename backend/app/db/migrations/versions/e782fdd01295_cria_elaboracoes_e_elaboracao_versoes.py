"""cria elaboracoes e elaboracao_versoes

Revision ID: e782fdd01295
Revises: e5b3f7a2c916
Create Date: 2026-09-21 23:41:05.978608

IA da elaboração (ADR-016) — sessão por `(user_id, processo_id, peca)` com
os fatos extras do advogado, e o histórico de versões da minuta (geração,
chat, grifo). Campos com texto do advogado/da minuta em BYTEA (cifrados com
AES-256-GCM, mesma função de `tribunal_credentials`) — nunca `VARCHAR`/`TEXT`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e782fdd01295"
down_revision: Union[str, None] = "e5b3f7a2c916"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "elaboracoes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("processo_id", sa.UUID(), nullable=False),
        sa.Column("peca", sa.String(length=100), nullable=False),
        sa.Column("fatos_extras_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["processos.id"],
            name=op.f("fk_elaboracoes_processo_id_processos"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_elaboracoes_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_elaboracoes")),
        sa.UniqueConstraint(
            "user_id", "processo_id", "peca", name=op.f("uq_elaboracoes_user_id_processo_id_peca")
        ),
    )
    op.create_index(
        op.f("ix_elaboracoes_processo_id"), "elaboracoes", ["processo_id"], unique=False
    )
    op.create_index(op.f("ix_elaboracoes_user_id"), "elaboracoes", ["user_id"], unique=False)

    op.create_table(
        "elaboracao_versoes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("elaboracao_id", sa.UUID(), nullable=False),
        sa.Column("origem", sa.String(length=20), nullable=False),
        sa.Column("instrucao_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("trecho_alvo_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("conteudo_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("llm_provider", sa.String(length=30), nullable=False),
        sa.Column("llm_model", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["elaboracao_id"],
            ["elaboracoes.id"],
            name=op.f("fk_elaboracao_versoes_elaboracao_id_elaboracoes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_elaboracao_versoes")),
    )
    op.create_index(
        op.f("ix_elaboracao_versoes_elaboracao_id"),
        "elaboracao_versoes",
        ["elaboracao_id"],
        unique=False,
    )
    op.create_index(
        "ix_elaboracao_versoes_elaboracao_id_created_at",
        "elaboracao_versoes",
        ["elaboracao_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_elaboracao_versoes_elaboracao_id_created_at", table_name="elaboracao_versoes"
    )
    op.drop_index(op.f("ix_elaboracao_versoes_elaboracao_id"), table_name="elaboracao_versoes")
    op.drop_table("elaboracao_versoes")
    op.drop_index(op.f("ix_elaboracoes_user_id"), table_name="elaboracoes")
    op.drop_index(op.f("ix_elaboracoes_processo_id"), table_name="elaboracoes")
    op.drop_table("elaboracoes")
