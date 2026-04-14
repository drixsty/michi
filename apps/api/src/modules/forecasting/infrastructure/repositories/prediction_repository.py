"""
SQLAlchemy Implementation of IPredictionRepository
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.forecasting.domain.entities import PredictionEntity
from src.modules.forecasting.domain.ports import IPredictionRepository
from src.modules.forecasting.infrastructure.persistence.models import Prediction
from src.modules.inventory.models import Product, Store

class SQLAlchemyPredictionRepository(IPredictionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: Prediction) -> PredictionEntity:
        return PredictionEntity(
            id=model.id,
            product_id=model.product_id,
            run_rate=model.run_rate,
            days_of_stock=model.days_of_stock,
            predicted_stockout_date=model.predicted_stockout_date,
            reorder_quantity=model.reorder_quantity,
            current_stock_snapshot=model.current_stock_snapshot,
            lead_time_snapshot=model.lead_time_snapshot,
            moq_snapshot=model.moq_snapshot,
            mape_score=model.mape_score,
            abc_rank=model.abc_rank,
            annual_gross_profit=model.annual_gross_profit,
            computed_at=model.computed_at
        )

    async def get_by_product(self, product_id: UUID) -> Optional[PredictionEntity]:
        stmt = select(Prediction).where(Prediction.product_id == product_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, entity: PredictionEntity) -> PredictionEntity:
        stmt = select(Prediction).where(Prediction.product_id == entity.product_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.run_rate = entity.run_rate
            model.days_of_stock = entity.days_of_stock
            model.predicted_stockout_date = entity.predicted_stockout_date
            model.reorder_quantity = entity.reorder_quantity
            model.current_stock_snapshot = entity.current_stock_snapshot
            model.lead_time_snapshot = entity.lead_time_snapshot
            model.moq_snapshot = entity.moq_snapshot
            model.mape_score = entity.mape_score
            model.abc_rank = entity.abc_rank
            model.annual_gross_profit = entity.annual_gross_profit
        else:
            model = Prediction(
                id=entity.id,
                product_id=entity.product_id,
                run_rate=entity.run_rate,
                days_of_stock=entity.days_of_stock,
                predicted_stockout_date=entity.predicted_stockout_date,
                reorder_quantity=entity.reorder_quantity,
                current_stock_snapshot=entity.current_stock_snapshot,
                lead_time_snapshot=entity.lead_time_snapshot,
                moq_snapshot=entity.moq_snapshot,
                mape_score=entity.mape_score,
                abc_rank=entity.abc_rank,
                annual_gross_profit=entity.annual_gross_profit
            )
            self.session.add(model)
        
        await self.session.flush()
        return self._to_entity(model)

    async def delete_by_products(self, product_ids: List[UUID]) -> None:
        stmt = delete(Prediction).where(Prediction.product_id.in_(product_ids))
        await self.session.execute(stmt)
        await self.session.flush()

    async def list_by_store(self, store_id: UUID) -> List[PredictionEntity]:
        stmt = (
            select(Prediction)
            .join(Product)
            .where(Product.store_id == store_id)
            .order_by(Prediction.predicted_stockout_date.asc().nullslast())
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_organization(self, org_id: UUID) -> List[PredictionEntity]:
        stmt = (
            select(Prediction)
            .join(Product)
            .join(Store, Product.store_id == Store.id)
            .where(Store.organization_id == org_id, Store.connected == True)
            .order_by(Prediction.predicted_stockout_date.asc().nullslast())
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]
