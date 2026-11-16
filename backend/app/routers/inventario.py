import re
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..api.deps import require_inventory_manager
from ..core.database import get_db
from ..models.models import InventoryMovementModel, UserModel
from ..schemas.schemas import InventoryMovementResponse
from ..services.inventory_service import InventoryService
from ..services.pdf_service import InventoryPdfService

router = APIRouter()
inventory_export_router = APIRouter()


@inventory_export_router.get("/export/pdf")
def exportar_inventario_pdf(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_inventory_manager),
) -> StreamingResponse:
    generated_at = datetime.now().astimezone()
    filename_username = re.sub(r"[^A-Za-z0-9._-]", "_", current_user.username)
    filename = (
        f"inventario_{generated_at:%Y-%m-%d}_{filename_username}.pdf"
    )
    pdf_buffer = InventoryPdfService(db).generate_inventory_pdf(
        current_user.username,
        generated_at,
    )
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/historial",
    response_model=list[InventoryMovementResponse],
)
def listar_historial_inventario(
    db: Session = Depends(get_db),
    _: UserModel = Depends(require_inventory_manager),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[InventoryMovementModel]:
    return InventoryService(db).list_history(limit, offset)
