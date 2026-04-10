
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, func, Column, String, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()

class PlatformSource(enum.Enum):
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    AMAZON = "amazon"
    CSV = "csv"
    CUSTOM = "custom"

class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True)
    shop_id = Column(UUID(as_uuid=True))
    source_platform = Column(Enum(PlatformSource))

class SourceConnection(Base):
    __tablename__ = "source_connections"
    id = Column(UUID(as_uuid=True), primary_key=True)
    shop_id = Column(UUID(as_uuid=True))
    platform = Column(Enum(PlatformSource))
    connected = Column(Boolean)

async def diag():
    db_url = "postgresql+asyncpg://michi:michi123@localhost:5433/michi_db"
    engine = create_async_engine(db_url)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)

    async with AsyncSessionLocal() as db:
        # Check Connections
        conn_res = await db.execute(select(SourceConnection))
        conns = conn_res.scalars().all()
        print("\n--- Connections in DB ---")
        for c in conns:
            print(f"Shop: {c.shop_id} | Platform: {c.platform.value} | Connected: {c.connected}")

        # Check Products
        prod_res = await db.execute(
            select(Product.shop_id, Product.source_platform, func.count(Product.id))
            .group_by(Product.shop_id, Product.source_platform)
        )
        counts = prod_res.all()
        print("\n--- Products in DB ---")
        for sid, platform, count in counts:
            print(f"Shop: {sid} | Platform: {platform.value} | Count: {count}")

if __name__ == "__main__":
    asyncio.run(diag())
