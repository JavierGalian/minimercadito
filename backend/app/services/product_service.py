from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..core.exceptions import ApplicationError, ConflictError
from ..models.models import InventoryMovementModel, Producto, UserModel
from ..repositories.product_repo import ProductRepository
from ..schemas.schemas import ProductoCreate, ProductoResponse, ProductoUpdate


class ProductService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.product_repo = ProductRepository(db)

    def list_products(self) -> list[ProductoResponse]:
        return self._with_audit(self.product_repo.get_all())

    def get_by_barcode(self, codigo_barras: str) -> ProductoResponse:
        producto = self.product_repo.get_by_barcode(codigo_barras)
        return self._with_audit([producto])[0]

    def create_product(
        self,
        datos: ProductoCreate,
        user_id: int,
    ) -> ProductoResponse:
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
        return self._with_audit([producto])[0]

    def update_product(
        self,
        product_id: int,
        datos: ProductoUpdate,
        user_id: int,
    ) -> ProductoResponse:
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
        return self._with_audit([producto])[0]

    def _with_audit(self, productos: list[Producto]) -> list[ProductoResponse]:
        if not productos:
            return []

        product_ids = [producto.id for producto in productos]
        creation_rows = self.db.execute(
            select(
                InventoryMovementModel.product_id,
                InventoryMovementModel.user_id,
                UserModel.username,
            )
            .join(UserModel, UserModel.id == InventoryMovementModel.user_id)
            .where(
                InventoryMovementModel.product_id.in_(product_ids),
                InventoryMovementModel.change_type == "CREACION",
            )
            .order_by(
                InventoryMovementModel.created_at,
                InventoryMovementModel.id,
            )
        ).all()
        creators: dict[int, tuple[int, str]] = {}
        for row in creation_rows:
            creators.setdefault(row.product_id, (row.user_id, row.username))

        ranked_updates = (
            select(
                InventoryMovementModel.product_id.label("product_id"),
                InventoryMovementModel.user_id.label("user_id"),
                InventoryMovementModel.created_at.label("created_at"),
                UserModel.username.label("username"),
                func.row_number()
                .over(
                    partition_by=InventoryMovementModel.product_id,
                    order_by=(
                        InventoryMovementModel.created_at.desc(),
                        InventoryMovementModel.id.desc(),
                    ),
                )
                .label("position"),
            )
            .join(UserModel, UserModel.id == InventoryMovementModel.user_id)
            .where(
                InventoryMovementModel.product_id.in_(product_ids),
                InventoryMovementModel.change_type != "CREACION",
            )
            .subquery()
        )
        update_rows = self.db.execute(
            select(ranked_updates).where(ranked_updates.c.position == 1),
        ).all()
        latest_updates = {row.product_id: row for row in update_rows}

        responses: list[ProductoResponse] = []
        for producto in productos:
            creator = creators.get(producto.id)
            update = latest_updates.get(producto.id)
            response_data = ProductoResponse.model_validate(producto).model_dump()
            response_data.update(
                creado_por_id=creator[0] if creator else None,
                creado_por=creator[1] if creator else None,
                actualizado_en=update.created_at if update else None,
                actualizado_por_id=update.user_id if update else None,
                actualizado_por=update.username if update else None,
            )
            responses.append(ProductoResponse.model_validate(response_data))
        return responses
