from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    descripcion: str | None = None
    codigo_barras: str | None = Field(default=None, min_length=1, max_length=64)
    precio: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock_actual: int = Field(default=0, ge=0)

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class ProductoUpdate(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    descripcion: str | None
    codigo_barras: str | None = Field(min_length=1, max_length=64)
    precio: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock_actual: int = Field(ge=0)

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class ProductoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    codigo_barras: str | None
    precio: Decimal
    stock_actual: int
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class DetalleVentaCreate(BaseModel):
    producto_id: int = Field(gt=0)
    cantidad: int = Field(gt=0)

    model_config = ConfigDict(extra="forbid")


class VentaCreate(BaseModel):
    detalles: list[DetalleVentaCreate] = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


class DetalleVentaResponse(BaseModel):
    id: int
    venta_id: int
    producto_id: int
    cantidad: int
    precio_unitario: Decimal

    model_config = ConfigDict(from_attributes=True)


class VentaResponse(BaseModel):
    id: int
    fecha: datetime
    total: Decimal
    detalles: list[DetalleVentaResponse]

    model_config = ConfigDict(from_attributes=True)


class DetalleVentaHistorialResponse(BaseModel):
    nombre_producto: str
    cantidad: int
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class VentaHistorialResponse(BaseModel):
    id: int
    fecha: datetime
    total: Decimal
    cajero: str | None
    detalles: list[DetalleVentaHistorialResponse]

    model_config = ConfigDict(from_attributes=True)


class ReporteVentasMensual(BaseModel):
    anio: int
    mes: int
    total: Decimal
    cantidad_ventas: int


class ReporteVentasPorMes(BaseModel):
    mes: int
    total: Decimal
    cantidad_ventas: int


class ReporteVentasAnual(BaseModel):
    anio: int
    meses: list[ReporteVentasPorMes]


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=12, max_length=72)
    rol: Literal["ADMIN", "CAJERO", "REPOSITOR"]

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, password: str) -> str:
        if len(password.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar 72 bytes en UTF-8.")
        return password


class UserResponse(BaseModel):
    id: int
    username: str
    rol: Literal["ADMIN", "CAJERO", "REPOSITOR"]
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=72)

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    rol: Literal["ADMIN", "CAJERO", "REPOSITOR"]


class InventoryMovementResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    change_type: Literal["CREACION", "ACTUALIZACION", "REPOSICION", "VENTA"]
    quantity_changed: int
    created_at: datetime
    product_name: str
    username: str

    model_config = ConfigDict(from_attributes=True)
