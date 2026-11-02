"""fichas cifradas dos autos e o dossie consolidado

Revision ID: a7d3c1e9b5f2
Revises: f1c8a4e2b7d0
Create Date: 2026-10-21 12:40:00.000000

ADR-024. O PDF não entra no banco. `ficha_encrypted` e `resumo_encrypted`
são BYTEA (AES-256-GCM). Apagar o processo ou o usuário apaga a leitura.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a7d3c1e9b5f2"
down_revision: Union[str, None] = "f1c8a4e2b7d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "processo_documentos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("processo_id", sa.UUID(), nullable=False),
        sa.Column("movimentacao_id", sa.UUID(), nullable=False),
        sa.Column("url_hash", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("paginas", sa.Integer(), nullable=True),
        sa.Column("paginas_ocr", sa.Integer(), nullable=True),
        sa.Column("ficha_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("lido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_processo_documentos_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["processos.id"],
            name=op.f("fk_processo_documentos_processo_id_processos"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["movimentacao_id"],
            ["movimentacoes.id"],
            name=op.f("fk_processo_documentos_movimentacao_id_movimentacoes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_processo_documentos")),
        sa.UniqueConstraint(
            "processo_id",
            "movimentacao_id",
            name=op.f("uq_processo_documentos_processo_id_movimentacao_id"),
        ),
    )
    op.create_index(
        op.f("ix_processo_documentos_user_id"),
        "processo_documentos",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_processo_documentos_processo_id"),
        "processo_documentos",
        ["processo_id"],
        unique=False,
    )

    op.create_table(
        "processo_dossies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("processo_id", sa.UUID(), nullable=False),
        sa.Column("resumo_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("fingerprint", sa.String(length=64), nullable=True),
        sa.Column("gerado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("lidos", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("retomar_apos", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_processo_dossies_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["processos.id"],
            name=op.f("fk_processo_dossies_processo_id_processos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_processo_dossies")),
        sa.UniqueConstraint(
            "processo_id",
            name=op.f("uq_processo_dossies_processo_id"),
        ),
    )
    op.create_index(
        op.f("ix_processo_dossies_user_id"),
        "processo_dossies",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_processo_dossies_user_id"), table_name="processo_dossies")
    op.drop_table("processo_dossies")
    op.drop_index(op.f("ix_processo_documentos_processo_id"), table_name="processo_documentos")
    op.drop_index(op.f("ix_processo_documentos_user_id"), table_name="processo_documentos")
    op.drop_table("processo_documentos")
