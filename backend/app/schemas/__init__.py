"""Esquemas de entrada y salida de la API."""

from .schemas import (
    DetalleVentaCreate,
    DetalleVentaHistorialResponse,
    DetalleVentaResponse,
    ProductoCreate,
    ProductoResponse,
    ReporteVentasAnual,
    ReporteVentasMensual,
    ReporteVentasPorMes,
    VentaCreate,
    VentaHistorialResponse,
    VentaResponse,
)

__all__ = [
    "ProductoCreate",
    "ProductoResponse",
    "DetalleVentaCreate",
    "DetalleVentaResponse",
    "DetalleVentaHistorialResponse",
    "VentaCreate",
    "VentaResponse",
    "VentaHistorialResponse",
    "ReporteVentasMensual",
    "ReporteVentasPorMes",
    "ReporteVentasAnual",
]
