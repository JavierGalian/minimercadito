"""Add REPOSITOR role and inventory movement audit records.

Revision ID: a721b3d4c5e6
Revises: d9f3a5b1c2e4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a721b3d4c5e6"
down_revision: Union[str, None] = "d9f3a5b1c2e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("usuarios") as batch_op:
        batch_op.drop_constraint("ck_usuarios_rol_valido", type_="check")
        batch_op.create_check_constraint(
            "ck_usuarios_rol_valido",
            "rol IN ('ADMIN', 'CAJERO', 'REPOSITOR')",
        )

    op.create_table(
        "movimientos_inventario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("change_type", sa.String(length=16), nullable=False),
        sa.Column("quantity_changed", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "change_type IN ('CREACION', 'ACTUALIZACION', 'REPOSICION', 'VENTA')",
            name="ck_movimientos_inventario_tipo_valido",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["productos.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["usuarios.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_movimientos_inventario_product_id",
        "movimientos_inventario",
        ["product_id"],
    )
    op.create_index(
        "ix_movimientos_inventario_user_id",
        "movimientos_inventario",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_movimientos_inventario_user_id",
        table_name="movimientos_inventario",
    )
    op.drop_index(
        "ix_movimientos_inventario_product_id",
        table_name="movimientos_inventario",
    )
    op.drop_table("movimientos_inventario")

    with op.batch_alter_table("usuarios") as batch_op:
        batch_op.drop_constraint("ck_usuarios_rol_valido", type_="check")
        batch_op.create_check_constraint(
            "ck_usuarios_rol_valido",
            "rol IN ('ADMIN', 'CAJERO')",
        )
