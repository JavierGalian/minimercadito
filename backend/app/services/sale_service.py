from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session, selectinload

from ..core.exceptions import InsufficientStockError
from ..models.models import DetalleVenta, Producto, Venta
from ..repositories.product_repo import ProductRepository
from ..schemas.schemas import (
    ReporteVentasAnual,
    ReporteVentasMensual,
    ReporteVentasPorMes,
    VentaCreate,
)


class SaleService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.product_repo = ProductRepository(db)

    def register_sale(
        self,
        venta_data: VentaCreate,
        usuario_id: int | None = None,
    ) -> Venta:
        cantidades: dict[int, int] = defaultdict(int)
        for detalle in venta_data.detalles:
            cantidades[detalle.producto_id] += detalle.cantidad

        try:
            if not self.db.in_transaction():
                self.db.begin()

            productos: dict[int, Producto] = {}
            for producto_id in sorted(cantidades):
                producto = self.product_repo.get_by_id_for_update(producto_id)
                cantidad = cantidades[producto_id]
                if producto.stock_actual < cantidad:
                    raise InsufficientStockError(
                        producto_id,
                        producto.stock_actual,
                        cantidad,
                    )
                productos[producto_id] = producto

            subtotales = [
                productos[detalle.producto_id].precio * detalle.cantidad
                for detalle in venta_data.detalles
            ]
            total = sum(subtotales, start=Decimal("0.00"))
            venta = Venta(total=total, usuario_id=usuario_id)
            for detalle in venta_data.detalles:
                producto = productos[detalle.producto_id]
                venta.detalles.append(
                    DetalleVenta(
                        producto=producto,
                        cantidad=detalle.cantidad,
                        precio_unitario=producto.precio,
                    )
                )

            self.db.add(venta)
            for producto_id, cantidad in cantidades.items():
                producto = productos[producto_id]
                self.product_repo.update_stock(
                    producto,
                    producto.stock_actual - cantidad,
                )
            self.db.flush()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(venta)
        return venta

    def list_history(
        self,
        limit: int,
        offset: int,
        cashier_id: int | None = None,
    ) -> list[Venta]:
        statement = (
            select(Venta)
            .options(
                selectinload(Venta.usuario),
                selectinload(Venta.detalles).selectinload(DetalleVenta.producto),
            )
            .order_by(Venta.fecha.desc(), Venta.id.desc())
            .limit(limit)
            .offset(offset)
        )
        if cashier_id is not None:
            statement = statement.where(Venta.usuario_id == cashier_id)
        return list(self.db.scalars(statement).all())

    def monthly_report(self, year: int, month: int) -> ReporteVentasMensual:
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = (
            datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            if month == 12
            else datetime(year, month + 1, 1, tzinfo=timezone.utc)
        )
        total, count = self.db.execute(
            select(
                func.coalesce(func.sum(Venta.total), Decimal("0.00")),
                func.count(Venta.id),
            ).where(Venta.fecha >= start, Venta.fecha < end),
        ).one()
        return ReporteVentasMensual(
            anio=year,
            mes=month,
            total=total,
            cantidad_ventas=count,
        )

    def annual_report(self, year: int) -> ReporteVentasAnual:
        start = datetime(year, 1, 1, tzinfo=timezone.utc)
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        month_expression = extract("month", Venta.fecha)
        rows = self.db.execute(
            select(
                month_expression,
                func.sum(Venta.total),
                func.count(Venta.id),
            )
            .where(Venta.fecha >= start, Venta.fecha < end)
            .group_by(month_expression)
            .order_by(month_expression),
        ).all()
        totals_by_month = {
            int(month): (total, count)
            for month, total, count in rows
        }
        return ReporteVentasAnual(
            anio=year,
            meses=[
                ReporteVentasPorMes(
                    mes=month,
                    total=totals_by_month.get(month, (Decimal("0.00"), 0))[0],
                    cantidad_ventas=totals_by_month.get(month, (Decimal("0.00"), 0))[1],
                )
                for month in range(1, 13)
            ],
        )
