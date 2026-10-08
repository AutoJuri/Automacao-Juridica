"""adiciona cargo do perfil e trava os papéis da organização

Revision ID: e3b7a1c9d4f8
Revises: d1f6a9c3e8b4
Create Date: 2026-10-07 23:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3b7a1c9d4f8"
down_revision: Union[str, None] = "d1f6a9c3e8b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CARGOS = "('advogado', 'assistente', 'estagiario')"
_PAPEIS = "('owner', 'admin', 'advogado', 'assistente', 'estagiario')"


def upgrade() -> None:
    op.add_column("users", sa.Column("cargo", sa.String(length=20), nullable=True))
    op.create_check_constraint(
        "ck_users_cargo",
        "users",
        f"cargo IS NULL OR cargo IN {_CARGOS}",
    )
    op.create_check_constraint(
        "ck_organization_members_role",
        "organization_members",
        f"role IN {_PAPEIS}",
    )
    op.create_check_constraint(
        "ck_organization_invites_role",
        "organization_invites",
        f"role IN {_PAPEIS}",
    )


def downgrade() -> None:
    op.drop_constraint("ck_organization_invites_role", "organization_invites", type_="check")
    op.drop_constraint("ck_organization_members_role", "organization_members", type_="check")
    op.drop_constraint("ck_users_cargo", "users", type_="check")
    op.drop_column("users", "cargo")
