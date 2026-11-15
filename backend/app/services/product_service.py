from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..core.exceptions import ApplicationError, ConflictError
from ..models.models import InventoryMovementModel, Producto
from ..repositories.product_repo import ProductRepository
from ..schemas.schemas import ProductoCreate, ProductoUpdate


class ProductService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.product_repo = ProductRepository(db)

    def create_product(
        self,
        datos: ProductoCreate,
        user_id: int,
    ) -> Producto:
        producto = Producto(**datos.model_dump())
        try:
            self.product_repo.create(producto)
            self.db.add(
                InventoryMovementModel(
                    product_id=producto.id,
                    user_id=user_id,
                    change_type="CREACION",
                    quantity_changed=producto.stock_actual,
                )
            )
            self.db.commit()
            self.db.refresh(producto)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError(
                "No se pudo crear el producto por un conflicto de datos."
            ) from exc
        except (ApplicationError, SQLAlchemyError):
            self.db.rollback()
            raise
        return producto

    def update_product(
        self,
        product_id: int,
        datos: ProductoUpdate,
        user_id: int,
    ) -> Producto:
        try:
            producto = self.product_repo.get_by_id_for_update(product_id)
            if (
                datos.codigo_barras
                and datos.codigo_barras != producto.codigo_barras
                and self.product_repo.find_by_barcode(datos.codigo_barras) is not None
            ):
                raise ConflictError(
                    "Ya existe un producto con ese código de barras."
                )

            stock_anterior = producto.stock_actual
            for campo, valor in datos.model_dump().items():
                setattr(producto, campo, valor)
            self.db.flush()

            diferencia_stock = producto.stock_actual - stock_anterior
            if diferencia_stock:
                self.db.add(
                    InventoryMovementModel(
                        product_id=producto.id,
                        user_id=user_id,
                        change_type=(
                            "REPOSICION"
                            if diferencia_stock > 0
                            else "ACTUALIZACION"
                        ),
                        quantity_changed=diferencia_stock,
                    )
                )
            self.db.commit()
            self.db.refresh(producto)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError(
                "No se pudo actualizar el producto por un conflicto de datos."
            ) from exc
        except (ApplicationError, SQLAlchemyError):
            self.db.rollback()
            raise
        return producto
