"""
SQLAlchemy Implementation of ISalesLogRepository
"""
from typing import List
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.inventory.domain.entities import SalesLogEntity
from src.modules.inventory.domain.ports import ISalesLogRepository
from src.modules.inventory.infrastructure.persistence.models import SalesLog

class SQLAlchemySalesLogRepository(ISalesLogRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: SalesLog) -> SalesLogEntity:
        return SalesLogEntity(
            id=model.id,
            product_id=model.product_id,
            date=model.date,
            units_sold=model.units_sold,
            end_of_day_stock=model.end_of_day_stock
        )

    async def list_by_product(self, product_id: UUID, limit: int = 90) -> List[SalesLogEntity]:
        stmt = (
            select(SalesLog)
            .where(SalesLog.product_id == product_id)
            .order_by(SalesLog.date.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def delete_by_products(self, product_ids: List[UUID]) -> None:
        stmt = delete(SalesLog).where(SalesLog.product_id.in_(product_ids))
        await self.session.execute(stmt)
        await self.session.flush()

    async def save_batch(self, entities: List[SalesLogEntity]) -> None:
        models = [
            SalesLog(
                id=e.id,
                product_id=e.product_id,
                date=e.date,
                units_sold=e.units_sold,
                end_of_day_stock=e.end_of_day_stock
            ) for e in entities
        ]
        self.session.add_all(models)
        await self.session.flush()
