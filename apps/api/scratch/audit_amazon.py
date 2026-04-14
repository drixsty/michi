import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.modules.inventory.models import Product, PlatformSource, Store
from src.modules.auth.models import User

async def audit_amazon():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # Check User
        res = await session.execute(select(User).where(User.email == "dev@michi.com"))
        user = res.scalars().first()
        org_id = user.current_organization_id
        print(f"User Org ID: {org_id}")
        
        # Check Stores
        res = await session.execute(select(Store).where(Store.organization_id == org_id))
        stores = res.scalars().all()
        print(f"Stores found for Org: {len(stores)}")
        for s in stores:
            print(f"- {s.name} (Platform: {s.platform.value}, Connected: {s.connected})")
            
        # Check Products
        res = await session.execute(
            select(Product.source_platform, select.func.count(Product.id))
            .join(Store, Product.store_id == Store.id)
            .where(Store.organization_id == org_id)
            .group_by(Product.source_platform)
        )
        stats = res.all()
        print("\nProduct Platform Stats for this Org:")
        for platform, count in stats:
            print(f"- {platform.value if hasattr(platform, 'value') else platform}: {count}")

        # Deep dive Amazon
        res = await session.execute(
            select(Product)
            .join(Store, Product.store_id == Store.id)
            .where(Store.organization_id == org_id, Product.source_platform == PlatformSource.AMAZON)
        )
        amazon_prods = res.scalars().all()
        print(f"\nAmazon Products found: {len(amazon_prods)}")

if __name__ == "__main__":
    asyncio.run(audit_amazon())
