from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..api.deps import require_inventory_manager
from ..core.database import get_db
from ..models.models import Producto, UserModel
from ..schemas.schemas import ProductoCreate, ProductoResponse, ProductoUpdate
from ..services.product_service import ProductService

router = APIRouter()


@router.get("", response_model=list[ProductoResponse])
def listar_productos(db: Session = Depends(get_db)) -> list[ProductoResponse]:
    return ProductService(db).list_products()


@router.get("/codigo-barras/{codigo_barras}", response_model=ProductoResponse)
def obtener_producto_por_codigo(
    codigo_barras: str,
    db: Session = Depends(get_db),
) -> ProductoResponse:
    return ProductService(db).get_by_barcode(codigo_barras)


@router.post(
    "",
    response_model=ProductoResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_producto(
    datos: ProductoCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_inventory_manager),
) -> ProductoResponse:
    return ProductService(db).create_product(datos, current_user.id)


@router.put(
    "/{product_id}",
    response_model=ProductoResponse,
)
def actualizar_producto(
    product_id: int,
    datos: ProductoUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_inventory_manager),
) -> ProductoResponse:
    return ProductService(db).update_product(
        product_id,
        datos,
        current_user.id,
    )
