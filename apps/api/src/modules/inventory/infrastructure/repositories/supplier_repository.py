"""
SQLAlchemy Implementation of ISupplierRepository
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.inventory.domain.entities import SupplierEntity
from src.modules.inventory.domain.ports import ISupplierRepository
from src.modules.inventory.models import Supplier

class SQLAlchemySupplierRepository(ISupplierRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: Supplier) -> SupplierEntity:
        return SupplierEntity(
            id=model.id,
            store_id=model.store_id,
            name=model.name,
            contact_email=model.contact_email,
            reliability_score=model.reliability_score,
            average_delay_days=model.average_delay_days
        )

    async def get_by_id(self, supplier_id: UUID) -> Optional[SupplierEntity]:
        stmt = select(Supplier).where(Supplier.id == supplier_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_store(self, store_id: UUID) -> List[SupplierEntity]:
        stmt = select(Supplier).where(Supplier.store_id == store_id)
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def save(self, entity: SupplierEntity) -> SupplierEntity:
        stmt = select(Supplier).where(Supplier.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.name = entity.name
            model.contact_email = entity.contact_email
            model.reliability_score = entity.reliability_score
            model.average_delay_days = entity.average_delay_days
        else:
            model = Supplier(
                id=entity.id,
                store_id=entity.store_id,
                name=entity.name,
                contact_email=entity.contact_email,
                reliability_score=entity.reliability_score,
                average_delay_days=entity.average_delay_days
            )
            self.session.add(model)
        
        await self.session.flush()
        return self._to_entity(model)
