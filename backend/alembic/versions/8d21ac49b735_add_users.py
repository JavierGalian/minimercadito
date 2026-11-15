"""Add user accounts for authentication and roles.

Revision ID: 8d21ac49b735
Revises: c58085ec1233
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8d21ac49b735"
down_revision: Union[str, None] = "c58085ec1233"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=10), nullable=False),
        sa.Column(
            "activo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rol IN ('ADMIN', 'CAJERO')",
            name="ck_usuarios_rol_valido",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )


def downgrade() -> None:
    op.drop_table("usuarios")
