from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models.models import InventoryMovementModel


class InventoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_history(
        self,
        limit: int,
        offset: int,
    ) -> list[InventoryMovementModel]:
        statement = (
            select(InventoryMovementModel)
            .options(
                selectinload(InventoryMovementModel.producto),
                selectinload(InventoryMovementModel.usuario),
            )
            .order_by(
                InventoryMovementModel.created_at.desc(),
                InventoryMovementModel.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(statement).all())
