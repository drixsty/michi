import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
import src.modules.auth.models
import src.modules.inventory.models
import src.modules.forecasting.models

from src.modules.inventory.models import Product, PlatformSource, Store
from src.modules.forecasting.models import Prediction
from src.modules.auth.models import User

async def audit_amazon_predictions():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # Check User
        res = await session.execute(select(User).where(User.email == "dev@michi.com"))
        user = res.scalars().first()
        org_id = user.current_organization_id
        
        # Check Amazon Products & Predictions
        stmt = (
            select(Product, Prediction)
            .outerjoin(Prediction, Product.id == Prediction.product_id)
            .join(Store, Product.store_id == Store.id)
            .where(Store.organization_id == org_id, Product.source_platform == PlatformSource.AMAZON)
        )
        res = await session.execute(stmt)
        data = res.all()
        
        print(f"Amazon Products examined: {len(data)}")
        with_pred = sum(1 for p, pred in data if pred is not None)
        with_risk = sum(1 for p, pred in data if pred and (pred.reorder_quantity or 0) > 0)
        
        print(f"Products with Predictions: {with_pred}")
        print(f"Products with Reorder Quantity > 0: {with_risk}")
        
        if with_risk > 0:
            for p, pred in data:
                if pred and (pred.reorder_quantity or 0) > 0:
                    print(f"- {p.sku}: Risk Value = {pred.reorder_quantity * (p.sale_price or 0)}")
                    break

if __name__ == "__main__":
    asyncio.run(audit_amazon_predictions())
