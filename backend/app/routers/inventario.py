from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..api.deps import require_inventory_manager
from ..core.database import get_db
from ..models.models import InventoryMovementModel, UserModel
from ..schemas.schemas import InventoryMovementResponse
from ..services.inventory_service import InventoryService

router = APIRouter()


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
