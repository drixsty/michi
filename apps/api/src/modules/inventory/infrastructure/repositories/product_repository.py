"""
SQLAlchemy Implementation of IProductRepository
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.inventory.domain.entities import ProductEntity, PlatformSource
from src.modules.inventory.domain.ports import IProductRepository
from src.modules.inventory.infrastructure.persistence.models import Product

class SQLAlchemyProductRepository(IProductRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: Product) -> ProductEntity:
        return ProductEntity(
            id=model.id,
            store_id=model.store_id,
            sku=model.sku,
            title=model.title,
            current_stock=model.current_stock,
            lead_time=model.lead_time,
            moq=model.moq,
            boost_factor=model.boost_factor,
            stock_weight=model.stock_weight,
            cost_price=model.cost_price,
            sale_price=model.sale_price,
            source_platform=PlatformSource(model.source_platform.value) if model.source_platform else PlatformSource.CUSTOM,
            external_id=model.external_id,
            supplier_id=model.supplier_id,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def get_by_id(self, product_id: UUID) -> Optional[ProductEntity]:
        stmt = select(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_sku(self, sku: str, store_ids: List[UUID]) -> List[ProductEntity]:
        stmt = (
            select(Product)
            .where(Product.sku == sku, Product.store_id.in_(store_ids))
            .options(
                selectinload(Product.prediction),
                selectinload(Product.supplier)
            )
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_store(self, store_ids: List[UUID]) -> List[ProductEntity]:
        stmt = (
            select(Product)
            .where(Product.store_id.in_(store_ids))
            .options(
                selectinload(Product.prediction),
                selectinload(Product.supplier)
            )
            .order_by(Product.sku)
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def save(self, entity: ProductEntity) -> ProductEntity:
        stmt = select(Product).where(Product.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.title = entity.title
            model.current_stock = entity.current_stock
            model.lead_time = entity.lead_time
            model.moq = entity.moq
            model.boost_factor = entity.boost_factor
            model.stock_weight = entity.stock_weight
            model.cost_price = entity.cost_price
            model.sale_price = entity.sale_price
            model.supplier_id = entity.supplier_id
        else:
            from src.modules.inventory.infrastructure.persistence.models import PlatformSource as ModelPlatformSource
            model = Product(
                id=entity.id,
                store_id=entity.store_id,
                sku=entity.sku,
                title=entity.title,
                current_stock=entity.current_stock,
                lead_time=entity.lead_time,
                moq=entity.moq,
                boost_factor=entity.boost_factor,
                stock_weight=entity.stock_weight,
                cost_price=entity.cost_price,
                sale_price=entity.sale_price,
                source_platform=ModelPlatformSource(entity.source_platform.value),
                external_id=entity.external_id,
                supplier_id=entity.supplier_id
            )
            self.session.add(model)
        
        await self.session.flush()
        return self._to_entity(model)

    async def update_settings(self, product_id: UUID, **kwargs) -> Optional[ProductEntity]:
        stmt = (
            update(Product)
            .where(Product.id == product_id)
            .values(**kwargs)
            .returning(Product)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.flush()
            return self._to_entity(model)
        return None

    async def delete_by_store(self, store_id: UUID) -> None:
        stmt = delete(Product).where(Product.store_id == store_id)
        await self.session.execute(stmt)
        await self.session.flush()
