"""
SQLAlchemy Implementation of ICleanedDemandRepository
"""
from typing import List
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.forecasting.domain.entities import CleanedDemandEntity
from src.modules.forecasting.domain.ports import ICleanedDemandRepository
from src.modules.forecasting.models import CleanedDemand

class SQLAlchemyCleanedDemandRepository(ICleanedDemandRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: CleanedDemand) -> CleanedDemandEntity:
        return CleanedDemandEntity(
            id=model.id,
            product_id=model.product_id,
            date=model.date,
            raw_units_sold=model.raw_units_sold,
            corrected_units_sold=model.corrected_units_sold,
            inventory_level=model.inventory_level,
            is_stockout=model.is_stockout,
            is_outlier=model.is_outlier,
            correction_type=model.correction_type,
            computed_at=model.computed_at
        )

    async def list_by_product(self, product_id: UUID, limit: int = 365) -> List[CleanedDemandEntity]:
        stmt = (
            select(CleanedDemand)
            .where(CleanedDemand.product_id == product_id)
            .order_by(CleanedDemand.date.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def delete_by_products(self, product_ids: List[UUID]) -> None:
        stmt = delete(CleanedDemand).where(CleanedDemand.product_id.in_(product_ids))
        await self.session.execute(stmt)
        await self.session.flush()

    async def save_batch(self, entities: List[CleanedDemandEntity]) -> None:
        models = [
            CleanedDemand(
                id=e.id,
                product_id=e.product_id,
                date=e.date,
                raw_units_sold=e.raw_units_sold,
                corrected_units_sold=e.corrected_units_sold,
                inventory_level=e.inventory_level,
                is_stockout=e.is_stockout,
                is_outlier=e.is_outlier,
                correction_type=e.correction_type,
                computed_at=e.computed_at
            ) for e in entities
        ]
        self.session.add_all(models)
        await self.session.flush()
