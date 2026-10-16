"""cria a capa das elaborações

Revision ID: a9c4e2b7d1f6
Revises: e3b7a1c9d4f8
Create Date: 2026-10-08 23:58:00.000000

Bancos novos recebem a tabela. O banco local de desenvolvimento já tinha
`elaboracoes` no formato da branch feat/create-IA (processo_id obrigatório,
sem os dados manuais). Nesse caso a migration só completa a capa.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a9c4e2b7d1f6"
down_revision: Union[str, None] = "e3b7a1c9d4f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLUNAS_MANUAIS = (
    ("titulo", sa.String(length=120)),
    ("nu_processo", sa.String(length=50)),
    ("parte_ativa", sa.String(length=255)),
    ("parte_passiva", sa.String(length=255)),
    ("classe", sa.String(length=255)),
    ("assunto", sa.String(length=255)),
    ("foro_vara", sa.String(length=255)),
    ("valor_causa", sa.String(length=100)),
    ("juiz", sa.String(length=255)),
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "elaboracoes" not in inspector.get_table_names():
        _criar()
        return
    _completar(inspector)


def _criar() -> None:
    op.create_table(
        "elaboracoes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("processo_id", sa.UUID(), nullable=True),
        sa.Column("peca", sa.String(length=100), nullable=False),
        *[
            sa.Column(nome, tipo, nullable=True)
            for nome, tipo in _COLUNAS_MANUAIS
        ],
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "processo_id IS NOT NULL OR titulo IS NOT NULL",
            name="ck_elaboracoes_origem",
        ),
        sa.CheckConstraint(
            "processo_id IS NULL OR ("
            "titulo IS NULL AND nu_processo IS NULL AND parte_ativa IS NULL "
            "AND parte_passiva IS NULL AND classe IS NULL AND assunto IS NULL "
            "AND foro_vara IS NULL AND valor_causa IS NULL AND juiz IS NULL)",
            name="ck_elaboracoes_manual_so_sem_processo",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_elaboracoes_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["processos.id"],
            name="fk_elaboracoes_processo_id_processos",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_elaboracoes"),
    )
    op.create_index(
        "uq_elaboracoes_user_processo_peca",
        "elaboracoes",
        ["user_id", "processo_id", "peca"],
        unique=True,
        postgresql_where=sa.text("processo_id IS NOT NULL"),
    )
    op.create_index(
        "ix_elaboracoes_user_id_updated_at",
        "elaboracoes",
        ["user_id", "updated_at"],
    )


def _completar(inspector) -> None:
    existentes = {coluna["name"] for coluna in inspector.get_columns("elaboracoes")}
    for nome, tipo in _COLUNAS_MANUAIS:
        if nome not in existentes:
            op.add_column("elaboracoes", sa.Column(nome, tipo, nullable=True))
    op.alter_column("elaboracoes", "processo_id", existing_type=sa.UUID(), nullable=True)
    checks = {item["name"] for item in inspector.get_check_constraints("elaboracoes")}
    if "ck_elaboracoes_origem" not in checks:
        op.create_check_constraint(
            "ck_elaboracoes_origem",
            "elaboracoes",
            "processo_id IS NOT NULL OR titulo IS NOT NULL",
        )
    if "ck_elaboracoes_manual_so_sem_processo" not in checks:
        op.create_check_constraint(
            "ck_elaboracoes_manual_so_sem_processo",
            "elaboracoes",
            "processo_id IS NULL OR ("
            "titulo IS NULL AND nu_processo IS NULL AND parte_ativa IS NULL "
            "AND parte_passiva IS NULL AND classe IS NULL AND assunto IS NULL "
            "AND foro_vara IS NULL AND valor_causa IS NULL AND juiz IS NULL)",
        )
    indices = {item["name"] for item in inspector.get_indexes("elaboracoes")}
    if "uq_elaboracoes_user_id_processo_id_peca" in indices:
        op.drop_constraint(
            "uq_elaboracoes_user_id_processo_id_peca",
            "elaboracoes",
            type_="unique",
        )
    if "uq_elaboracoes_user_processo_peca" not in indices:
        op.create_index(
            "uq_elaboracoes_user_processo_peca",
            "elaboracoes",
            ["user_id", "processo_id", "peca"],
            unique=True,
            postgresql_where=sa.text("processo_id IS NOT NULL"),
        )
    if "ix_elaboracoes_user_id_updated_at" not in indices:
        op.create_index(
            "ix_elaboracoes_user_id_updated_at",
            "elaboracoes",
            ["user_id", "updated_at"],
        )


def downgrade() -> None:
    op.drop_index("ix_elaboracoes_user_id_updated_at", table_name="elaboracoes")
    op.drop_index("uq_elaboracoes_user_processo_peca", table_name="elaboracoes")
    op.drop_table("elaboracoes")
