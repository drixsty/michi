"""
SQLAlchemy Implementation of IAlertRepository
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.inventory.domain.entities import AlertEntity
from src.modules.inventory.domain.ports import IAlertRepository
from src.modules.inventory.infrastructure.persistence.models import Alert, Product, Store

class SQLAlchemyAlertRepository(IAlertRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: Alert) -> AlertEntity:
        return AlertEntity(
            id=model.id,
            product_id=model.product_id,
            type=model.type,
            message=model.message,
            is_read=model.is_read,
            severity=model.severity,
            created_at=model.created_at
        )

    async def get_by_id(self, alert_id: UUID) -> Optional[AlertEntity]:
        stmt = select(Alert).where(Alert.id == alert_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_unread(self, store_id: Optional[UUID] = None, org_id: Optional[UUID] = None) -> List[AlertEntity]:
        stmt = select(Alert).where(Alert.is_read == False)
        
        if store_id:
            stmt = stmt.join(Product).where(Product.store_id == store_id)
        elif org_id:
            stmt = stmt.join(Product).join(Store).where(Store.organization_id == org_id)
            
        stmt = stmt.order_by(Alert.severity.desc(), Alert.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def save(self, entity: AlertEntity) -> AlertEntity:
        stmt = select(Alert).where(Alert.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.is_read = entity.is_read
            model.message = entity.message
            model.severity = entity.severity
        else:
            model = Alert(
                id=entity.id,
                product_id=entity.product_id,
                type=entity.type,
                message=entity.message,
                is_read=entity.is_read,
                severity=entity.severity,
                created_at=entity.created_at
            )
            self.session.add(model)
        
        await self.session.flush()
        return self._to_entity(model)

    async def save_batch(self, entities: List[AlertEntity]) -> None:
        models = [
            Alert(
                id=e.id,
                product_id=e.product_id,
                type=e.type,
                message=e.message,
                is_read=e.is_read,
                severity=e.severity,
                created_at=e.created_at
            ) for e in entities
        ]
        self.session.add_all(models)
        await self.session.flush()

    async def mark_as_read(self, alert_id: UUID) -> bool:
        stmt = update(Alert).where(Alert.id == alert_id).values(is_read=True)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def delete(self, alert_id: UUID) -> bool:
        stmt = delete(Alert).where(Alert.id == alert_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def exists_unread(self, product_id: UUID, alert_type: str) -> bool:
        stmt = select(func.count(Alert.id)).where(
            Alert.product_id == product_id,
            Alert.type == alert_type,
            Alert.is_read == False
        )
        result = await self.session.execute(stmt)
        return result.scalar() > 0
