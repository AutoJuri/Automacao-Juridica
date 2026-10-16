"""cria a integração do drive com o google

Revision ID: c7e2a9d4b1f8
Revises: b4d8f1a6c3e2
Create Date: 2026-10-13 19:00:00.000000

`drive_conexoes` guarda o token do Google em BYTEA (AES-256-GCM). `drive_arquivos`
é só a ficha: o byte fica no Drive da pessoa (ADR-022). `drive_pastas` ganha o id
da pasta no Google, nulo até o primeiro envio.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7e2a9d4b1f8"
down_revision: Union[str, None] = "b4d8f1a6c3e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "drive_pastas",
        sa.Column("google_folder_id", sa.String(length=100), nullable=True),
    )

    op.create_table(
        "drive_conexoes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("root_folder_id", sa.String(length=100), nullable=True),
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
            name="fk_drive_conexoes_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_drive_conexoes"),
        sa.UniqueConstraint("user_id", name="uq_drive_conexoes_user_id"),
    )

    op.create_table(
        "drive_arquivos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("pasta_id", sa.UUID(), nullable=False),
        sa.Column("google_file_id", sa.String(length=100), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=150), nullable=False),
        sa.Column("tamanho", sa.BigInteger(), nullable=True),
        sa.Column("origem", sa.String(length=20), nullable=False),
        sa.Column(
            "ausente_no_google",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_drive_arquivos_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["pasta_id"],
            ["drive_pastas.id"],
            name="fk_drive_arquivos_pasta_id_drive_pastas",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_drive_arquivos"),
        sa.UniqueConstraint(
            "pasta_id", "google_file_id", name="uq_drive_arquivos_pasta_id_google_file_id"
        ),
        sa.CheckConstraint(
            "origem IN ('upload', 'drive', 'elaboracao')",
            name="ck_drive_arquivos_origem",
        ),
    )
    op.create_index(
        "ix_drive_arquivos_pasta_id_created_at",
        "drive_arquivos",
        ["pasta_id", "created_at"],
    )
    op.create_index("ix_drive_arquivos_user_id", "drive_arquivos", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_drive_arquivos_user_id", table_name="drive_arquivos")
    op.drop_index("ix_drive_arquivos_pasta_id_created_at", table_name="drive_arquivos")
    op.drop_table("drive_arquivos")
    op.drop_table("drive_conexoes")
    op.drop_column("drive_pastas", "google_folder_id")
