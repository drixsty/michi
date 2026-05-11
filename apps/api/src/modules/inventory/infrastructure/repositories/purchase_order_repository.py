"""
SQLAlchemy Implementation of IPurchaseOrderRepository
"""
from typing import List, Optional
from datetime import date
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.inventory.domain.entities import PurchaseOrderEntity
from modules.inventory.domain.ports import IPurchaseOrderRepository
from modules.inventory.infrastructure.persistence.models import PurchaseOrder

class SQLAlchemyPurchaseOrderRepository(IPurchaseOrderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: PurchaseOrder) -> PurchaseOrderEntity:
        from typing import cast
        return PurchaseOrderEntity(
            id=cast(UUID, model.id),
            store_id=cast(UUID, model.store_id),
            product_id=cast(UUID, model.product_id),
            supplier_id=cast(UUID, model.supplier_id),
            quantity=cast(int, model.quantity),
            order_date=cast(date, model.order_date),
            expected_arrival_date=cast(date, model.expected_arrival_date),
            actual_arrival_date=cast(Optional[date], model.actual_arrival_date),
            status=cast(str, model.status)
        )

    async def get_by_id(self, po_id: UUID) -> Optional[PurchaseOrderEntity]:
        stmt = select(PurchaseOrder).where(PurchaseOrder.id == po_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, entity: PurchaseOrderEntity) -> PurchaseOrderEntity:
        stmt = select(PurchaseOrder).where(PurchaseOrder.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.status = entity.status # type: ignore
            model.actual_arrival_date = entity.actual_arrival_date # type: ignore
            model.quantity = entity.quantity # type: ignore
        else:
            model = PurchaseOrder(
                id=entity.id,
                store_id=entity.store_id,
                product_id=entity.product_id,
                supplier_id=entity.supplier_id,
                quantity=entity.quantity,
                order_date=entity.order_date,
                expected_arrival_date=entity.expected_arrival_date,
                actual_arrival_date=entity.actual_arrival_date,
                status=entity.status
            )
            self.session.add(model)
        
        await self.session.flush()
        return self._to_entity(model)

    async def list_by_store(self, store_id: UUID) -> List[PurchaseOrderEntity]:
        stmt = select(PurchaseOrder).where(PurchaseOrder.store_id == store_id)
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_supplier(self, supplier_id: UUID, status: Optional[str] = None) -> List[PurchaseOrderEntity]:
        stmt = select(PurchaseOrder).where(PurchaseOrder.supplier_id == supplier_id)
        if status:
            stmt = stmt.where(PurchaseOrder.status == status)
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]
