from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..api.deps import require_role
from ..core.database import get_db
from ..models.models import UserModel, Venta
from ..schemas.schemas import (
    ReporteVentasAnual,
    ReporteVentasMensual,
    VentaCreate,
    VentaHistorialResponse,
    VentaResponse,
)
from ..services.sale_service import SaleService

router = APIRouter()


@router.get("/historial", response_model=list[VentaHistorialResponse])
def listar_historial_ventas(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role(["ADMIN", "CAJERO"])),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Venta]:
    cashier_id = None if current_user.rol == "ADMIN" else current_user.id
    return SaleService(db).list_history(limit, offset, cashier_id=cashier_id)


@router.get("/reportes/mensual", response_model=ReporteVentasMensual)
def reporte_mensual_ventas(
    anio: int = Query(ge=1, le=9998),
    mes: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
    _: UserModel = Depends(require_role(["ADMIN"])),
) -> ReporteVentasMensual:
    return SaleService(db).monthly_report(anio, mes)


@router.get("/reportes/anual", response_model=ReporteVentasAnual)
def reporte_anual_ventas(
    anio: int = Query(ge=1, le=9998),
    db: Session = Depends(get_db),
    _: UserModel = Depends(require_role(["ADMIN"])),
) -> ReporteVentasAnual:
    return SaleService(db).annual_report(anio)


@router.post(
    "",
    response_model=VentaResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_venta(
    datos: VentaCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role(["ADMIN", "CAJERO"])),
) -> Venta:
    return SaleService(db).register_sale(datos, usuario_id=current_user.id)
