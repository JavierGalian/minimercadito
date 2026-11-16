from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class UserModel(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('ADMIN', 'CAJERO', 'REPOSITOR')",
            name="ck_usuarios_rol_valido",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(10), nullable=False)
    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    ventas: Mapped[list["Venta"]] = relationship(back_populates="usuario")
    movimientos_inventario: Mapped[list["InventoryMovementModel"]] = relationship(
        back_populates="usuario",
    )


class Producto(Base):
    __tablename__ = "productos"
    __table_args__ = (
        CheckConstraint("stock_actual >= 0", name="ck_productos_stock_no_negativo"),
        CheckConstraint("precio > 0", name="ck_productos_precio_positivo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    codigo_barras: Mapped[str | None] = mapped_column(String(64), unique=True)
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    detalles_venta: Mapped[list["DetalleVenta"]] = relationship(
        back_populates="producto",
    )
    movimientos_inventario: Mapped[list["InventoryMovementModel"]] = relationship(
        back_populates="producto",
    )


class Venta(Base):
    __tablename__ = "ventas"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_ventas_total_no_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    detalles: Mapped[list["DetalleVenta"]] = relationship(
        back_populates="venta",
        cascade="all, delete-orphan",
        order_by="DetalleVenta.id",
    )
    usuario: Mapped[UserModel | None] = relationship(back_populates="ventas")

    @property
    def cajero(self) -> str | None:
        return self.usuario.username if self.usuario is not None else None


class DetalleVenta(Base):
    __tablename__ = "detalle_venta"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_detalle_venta_cantidad_positiva"),
        CheckConstraint(
            "precio_unitario > 0",
            name="ck_detalle_venta_precio_positivo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(
        ForeignKey("ventas.id", ondelete="CASCADE"),
        nullable=False,
    )
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    venta: Mapped[Venta] = relationship(back_populates="detalles")
    producto: Mapped[Producto] = relationship(back_populates="detalles_venta")

    @property
    def nombre_producto(self) -> str:
        return self.producto.nombre

    @property
    def subtotal(self) -> Decimal:
        return self.precio_unitario * self.cantidad


class InventoryMovementModel(Base):
    __tablename__ = "movimientos_inventario"
    __table_args__ = (
        CheckConstraint(
            "change_type IN ('CREACION', 'ACTUALIZACION', 'REPOSICION', 'VENTA', 'BAJA')",
            name="ck_movimientos_inventario_tipo_valido",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    change_type: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity_changed: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    producto: Mapped[Producto] = relationship(
        back_populates="movimientos_inventario",
    )
    usuario: Mapped[UserModel] = relationship(
        back_populates="movimientos_inventario",
    )

    @property
    def product_name(self) -> str:
        return self.producto.nombre

    @property
    def username(self) -> str:
        return self.usuario.username
