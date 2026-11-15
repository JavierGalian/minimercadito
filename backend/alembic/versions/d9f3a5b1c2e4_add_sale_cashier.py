"""Associate sales with the user who recorded them.

Revision ID: d9f3a5b1c2e4
Revises: 8d21ac49b735
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d9f3a5b1c2e4"
down_revision: Union[str, None] = "8d21ac49b735"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("ventas") as batch_op:
        batch_op.add_column(sa.Column("usuario_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_ventas_usuario_id_usuarios",
            "usuarios",
            ["usuario_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_ventas_usuario_id", ["usuario_id"])


def downgrade() -> None:
    with op.batch_alter_table("ventas") as batch_op:
        batch_op.drop_index("ix_ventas_usuario_id")
        batch_op.drop_constraint("fk_ventas_usuario_id_usuarios", type_="foreignkey")
        batch_op.drop_column("usuario_id")
