import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.database.models import Product, Prediction, Organization
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.config import settings

async def check():
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        # Check Orgs
        orgs = (await session.execute(select(Organization))).scalars().all()
        print(f"Organizations: {len(orgs)}")
        
        # Check Products
        products = (await session.execute(select(Product))).scalars().all()
        print(f"Products: {len(products)}")
        
        # Check Predictions
        preds = (await session.execute(select(Prediction))).scalars().all()
        print(f"Predictions: {len(preds)}")
        
        if preds:
            print("First prediction check:")
            p = preds[0]
            print(f"  Product: {p.product_id}")
            print(f"  Stockout Date: {p.predicted_stockout_date}")
            print(f"  Demand Sigma: {p.demand_sigma}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
