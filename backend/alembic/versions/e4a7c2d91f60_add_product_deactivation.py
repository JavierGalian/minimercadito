"""Add soft deactivation for products and audit its event.

Revision ID: e4a7c2d91f60
Revises: a721b3d4c5e6
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4a7c2d91f60"
down_revision: Union[str, None] = "a721b3d4c5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("productos") as batch_op:
        batch_op.add_column(
            sa.Column(
                "activo",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=False,
            )
        )

    with op.batch_alter_table("movimientos_inventario") as batch_op:
        batch_op.drop_constraint(
            "ck_movimientos_inventario_tipo_valido",
            type_="check",
        )
        batch_op.create_check_constraint(
            "ck_movimientos_inventario_tipo_valido",
            "change_type IN ('CREACION', 'ACTUALIZACION', 'REPOSICION', 'VENTA', 'BAJA')",
        )


def downgrade() -> None:
    op.execute(
        "UPDATE movimientos_inventario "
        "SET change_type = 'ACTUALIZACION' WHERE change_type = 'BAJA'"
    )
    with op.batch_alter_table("movimientos_inventario") as batch_op:
        batch_op.drop_constraint(
            "ck_movimientos_inventario_tipo_valido",
            type_="check",
        )
        batch_op.create_check_constraint(
            "ck_movimientos_inventario_tipo_valido",
            "change_type IN ('CREACION', 'ACTUALIZACION', 'REPOSICION', 'VENTA')",
        )

    with op.batch_alter_table("productos") as batch_op:
        batch_op.drop_column("activo")
