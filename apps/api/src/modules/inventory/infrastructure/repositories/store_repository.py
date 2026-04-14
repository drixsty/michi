"""
SQLAlchemy Implementation of IStoreRepository
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.inventory.domain.entities import StoreEntity, PlatformSource
from src.modules.inventory.domain.ports import IStoreRepository
from src.modules.inventory.infrastructure.persistence.models import Store

class SQLAlchemyStoreRepository(IStoreRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: Store) -> StoreEntity:
        return StoreEntity(
            id=model.id,
            organization_id=model.organization_id,
            name=model.name,
            platform=PlatformSource(model.platform.value),
            connected=model.connected,
            last_sync_at=model.last_sync_at,
            health_status=model.health_status,
            config=model.config or {},
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def get_by_id(self, store_id: UUID) -> Optional[StoreEntity]:
        stmt = select(Store).where(Store.id == store_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_organization(self, org_id: UUID, connected_only: bool = False) -> List[StoreEntity]:
        stmt = select(Store).where(Store.organization_id == org_id)
        if connected_only:
            stmt = stmt.where(Store.connected == True)
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_platform(self, org_id: UUID, platform: str) -> Optional[StoreEntity]:
        from src.modules.inventory.models import PlatformSource as ModelPlatformSource
        stmt = select(Store).where(
            Store.organization_id == org_id,
            Store.platform == ModelPlatformSource(platform.upper())
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, entity: StoreEntity) -> StoreEntity:
        stmt = select(Store).where(Store.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.name = entity.name
            model.connected = entity.connected
            model.last_sync_at = entity.last_sync_at
            model.health_status = entity.health_status
            model.config = entity.config
        else:
            from src.modules.inventory.models import PlatformSource as ModelPlatformSource
            model = Store(
                id=entity.id,
                organization_id=entity.organization_id,
                name=entity.name,
                platform=ModelPlatformSource(entity.platform.value),
                connected=entity.connected,
                last_sync_at=entity.last_sync_at,
                health_status=entity.health_status,
                config=entity.config
            )
            self.session.add(model)
        
        await self.session.flush()
        return self._to_entity(model)
