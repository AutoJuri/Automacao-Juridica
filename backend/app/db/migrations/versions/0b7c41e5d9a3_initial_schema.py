"""initial schema

Revision ID: 0b7c41e5d9a3
Revises:
Create Date: 2026-07-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0b7c41e5d9a3"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "job_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.Column("duracao_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_job_logs_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_logs")),
    )
    op.create_index(op.f("ix_job_logs_user_id"), "job_logs", ["user_id"], unique=False)

    op.create_table(
        "processos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("tribunal", sa.String(length=50), nullable=False),
        sa.Column("cd_processo", sa.String(length=100), nullable=False),
        sa.Column("nu_processo", sa.String(length=50), nullable=True),
        sa.Column("de_classe", sa.String(length=255), nullable=True),
        sa.Column("de_assunto", sa.String(length=255), nullable=True),
        sa.Column("instancia", sa.String(length=10), nullable=True),
        sa.Column("parte_ativa", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("parte_passiva", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("url_cpo", sa.String(length=500), nullable=True),
        sa.Column("url_pasta", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_processos_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_processos")),
        sa.UniqueConstraint(
            "user_id", "cd_processo", name=op.f("uq_processos_user_id_cd_processo")
        ),
    )
    op.create_index(op.f("ix_processos_nu_processo"), "processos", ["nu_processo"], unique=False)
    op.create_index(op.f("ix_processos_user_id"), "processos", ["user_id"], unique=False)

    op.create_table(
        "tribunal_credentials",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("tribunal", sa.String(length=50), nullable=False),
        sa.Column("cpf_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("senha_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("email_provider", sa.String(length=20), nullable=True),
        sa.Column("email_oauth_token_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_tribunal_credentials_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tribunal_credentials")),
    )
    op.create_index(
        op.f("ix_tribunal_credentials_user_id"),
        "tribunal_credentials",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "tribunal_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("tribunal", sa.String(length=50), nullable=False),
        sa.Column("cookie_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="ativo", nullable=False),
        sa.Column("ultimo_erro", sa.Text(), nullable=True),
        sa.Column("tentativas_falha", sa.Integer(), server_default="0", nullable=False),
        sa.Column("proximo_retry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultimo_sucesso", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_tribunal_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tribunal_sessions")),
    )
    op.create_index(
        op.f("ix_tribunal_sessions_expires_at"),
        "tribunal_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tribunal_sessions_user_id"), "tribunal_sessions", ["user_id"], unique=False
    )

    op.create_table(
        "audiencias",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("processo_id", sa.UUID(), nullable=True),
        sa.Column("id_esaj", sa.String(length=255), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=True),
        sa.Column("data_audiencia", sa.DateTime(timezone=True), nullable=True),
        sa.Column("local", sa.String(length=255), nullable=True),
        sa.Column("is_new", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["processos.id"],
            name=op.f("fk_audiencias_processo_id_processos"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_audiencias_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audiencias")),
        sa.UniqueConstraint("id_esaj", name=op.f("uq_audiencias_id_esaj")),
    )
    op.create_index(
        op.f("ix_audiencias_data_audiencia"), "audiencias", ["data_audiencia"], unique=False
    )
    op.create_index(op.f("ix_audiencias_processo_id"), "audiencias", ["processo_id"], unique=False)
    op.create_index(op.f("ix_audiencias_user_id"), "audiencias", ["user_id"], unique=False)

    op.create_table(
        "intimacoes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("processo_id", sa.UUID(), nullable=True),
        sa.Column("id_esaj", sa.String(length=255), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("instancia", sa.String(length=10), nullable=True),
        sa.Column("data_movimentacao", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ciencia", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_new", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["processos.id"],
            name=op.f("fk_intimacoes_processo_id_processos"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_intimacoes_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_intimacoes")),
        sa.UniqueConstraint("id_esaj", name=op.f("uq_intimacoes_id_esaj")),
    )
    op.create_index(
        op.f("ix_intimacoes_data_movimentacao"),
        "intimacoes",
        ["data_movimentacao"],
        unique=False,
    )
    op.create_index(op.f("ix_intimacoes_processo_id"), "intimacoes", ["processo_id"], unique=False)
    op.create_index(op.f("ix_intimacoes_user_id"), "intimacoes", ["user_id"], unique=False)

    op.create_table(
        "movimentacoes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("processo_id", sa.UUID(), nullable=False),
        sa.Column("data_movimentacao", sa.DateTime(timezone=True), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=True),
        sa.Column("instancia", sa.String(length=10), nullable=True),
        sa.Column("is_new", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["processos.id"],
            name=op.f("fk_movimentacoes_processo_id_processos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_movimentacoes")),
        sa.UniqueConstraint(
            "processo_id",
            "data_movimentacao",
            "descricao",
            name=op.f("uq_movimentacoes_processo_id_data_movimentacao_descricao"),
        ),
    )
    op.create_index(
        op.f("ix_movimentacoes_data_movimentacao"),
        "movimentacoes",
        ["data_movimentacao"],
        unique=False,
    )
    op.create_index(
        op.f("ix_movimentacoes_processo_id"), "movimentacoes", ["processo_id"], unique=False
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("processo_id", sa.UUID(), nullable=True),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["processos.id"],
            name=op.f("fk_notifications_processo_id_processos"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_notifications_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )
    op.create_index(
        op.f("ix_notifications_processo_id"), "notifications", ["processo_id"], unique=False
    )
    op.create_index(
        "ix_notifications_user_id_is_read", "notifications", ["user_id", "is_read"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id_is_read", table_name="notifications")
    op.drop_index(op.f("ix_notifications_processo_id"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(op.f("ix_movimentacoes_processo_id"), table_name="movimentacoes")
    op.drop_index(op.f("ix_movimentacoes_data_movimentacao"), table_name="movimentacoes")
    op.drop_table("movimentacoes")
    op.drop_index(op.f("ix_intimacoes_user_id"), table_name="intimacoes")
    op.drop_index(op.f("ix_intimacoes_processo_id"), table_name="intimacoes")
    op.drop_index(op.f("ix_intimacoes_data_movimentacao"), table_name="intimacoes")
    op.drop_table("intimacoes")
    op.drop_index(op.f("ix_audiencias_user_id"), table_name="audiencias")
    op.drop_index(op.f("ix_audiencias_processo_id"), table_name="audiencias")
    op.drop_index(op.f("ix_audiencias_data_audiencia"), table_name="audiencias")
    op.drop_table("audiencias")
    op.drop_index(op.f("ix_tribunal_sessions_user_id"), table_name="tribunal_sessions")
    op.drop_index(op.f("ix_tribunal_sessions_expires_at"), table_name="tribunal_sessions")
    op.drop_table("tribunal_sessions")
    op.drop_index(op.f("ix_tribunal_credentials_user_id"), table_name="tribunal_credentials")
    op.drop_table("tribunal_credentials")
    op.drop_index(op.f("ix_processos_user_id"), table_name="processos")
    op.drop_index(op.f("ix_processos_nu_processo"), table_name="processos")
    op.drop_table("processos")
    op.drop_index(op.f("ix_job_logs_user_id"), table_name="job_logs")
    op.drop_table("job_logs")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
