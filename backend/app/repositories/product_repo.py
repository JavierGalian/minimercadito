from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.exceptions import ConflictError, NotFoundError
from ..models.models import Producto


class ProductRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> list[Producto]:
        statement = (
            select(Producto)
            .where(Producto.activo.is_(True))
            .order_by(Producto.id)
        )
        return list(self.db.scalars(statement).all())

    def get_by_barcode(self, codigo_barras: str) -> Producto:
        producto = self.find_by_barcode(codigo_barras)
        if producto is None or not producto.activo:
            raise NotFoundError("No se encontró el producto.")
        return producto

    def find_by_barcode(self, codigo_barras: str) -> Producto | None:
        statement = select(Producto).where(
            Producto.codigo_barras == codigo_barras,
        )
        return self.db.scalar(statement)

    def get_by_id_for_update(self, producto_id: int) -> Producto:
        statement = (
            select(Producto)
            .where(Producto.id == producto_id, Producto.activo.is_(True))
            .with_for_update()
        )
        producto = self.db.scalar(statement)
        if producto is None:
            raise NotFoundError(f"No existe el producto con id {producto_id}.")
        return producto

    def create(self, producto: Producto) -> Producto:
        if (
            producto.codigo_barras
            and self.find_by_barcode(producto.codigo_barras) is not None
        ):
            raise ConflictError("Ya existe un producto con ese código de barras.")

        self.db.add(producto)
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError(
                "No se pudo crear el producto por un conflicto de datos."
            ) from exc
        return producto

    def update_stock(self, producto: Producto, nuevo_stock: int) -> Producto:
        producto.stock_actual = nuevo_stock
        self.db.flush()
        return producto
