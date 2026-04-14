"""
SQLAlchemy Implementation of IPurchaseOrderRepository
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.inventory.domain.entities import PurchaseOrderEntity
from src.modules.inventory.domain.ports import IPurchaseOrderRepository
from src.modules.inventory.models import PurchaseOrder

class SQLAlchemyPurchaseOrderRepository(IPurchaseOrderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: PurchaseOrder) -> PurchaseOrderEntity:
        return PurchaseOrderEntity(
            id=model.id,
            store_id=model.store_id,
            product_id=model.product_id,
            supplier_id=model.supplier_id,
            quantity=model.quantity,
            order_date=model.order_date,
            expected_arrival_date=model.expected_arrival_date,
            actual_arrival_date=model.actual_arrival_date,
            status=model.status
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
            model.status = entity.status
            model.actual_arrival_date = entity.actual_arrival_date
            model.quantity = entity.quantity
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
