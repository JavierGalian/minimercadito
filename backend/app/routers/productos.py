from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..api.deps import require_role
from ..core.database import get_db
from ..core.exceptions import ConflictError
from ..models.models import Producto, UserModel
from ..repositories.product_repo import ProductRepository
from ..schemas.schemas import ProductoCreate, ProductoResponse

router = APIRouter()


@router.get("", response_model=list[ProductoResponse])
def listar_productos(db: Session = Depends(get_db)) -> list[Producto]:
    return ProductRepository(db).get_all()


@router.get("/codigo-barras/{codigo_barras}", response_model=ProductoResponse)
def obtener_producto_por_codigo(
    codigo_barras: str,
    db: Session = Depends(get_db),
) -> Producto:
    return ProductRepository(db).get_by_barcode(codigo_barras)


@router.post(
    "",
    response_model=ProductoResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_producto(
    datos: ProductoCreate,
    db: Session = Depends(get_db),
    _: UserModel = Depends(require_role(["ADMIN"])),
) -> Producto:
    repo = ProductRepository(db)
    producto = Producto(**datos.model_dump())
    try:
        repo.create(producto)
        db.commit()
        db.refresh(producto)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "No se pudo crear el producto por un conflicto de datos."
        ) from exc
    return producto
