import asyncio
import uuid
from core.database import AsyncSessionLocal
from modules.inventory.models import Store, Product
from sqlalchemy import select
import modules.auth.models
import modules.inventory.models
import modules.forecasting.models

async def debug_org():
    async with AsyncSessionLocal() as db:
        org_id = uuid.UUID('b5295741-d3d5-4517-91ce-73279ce7aeca')
        
        print("--- Active Stores ---")
        res = await db.execute(select(Store).where(Store.organization_id == org_id))
        stores = res.scalars().all()
        for s in stores:
            print(f"Store: {s.name}, ID: {s.id}, Platform: {s.platform}, Connected: {s.connected}")
            
        print("\n--- Products count per store ---")
        for s in stores:
            p_res = await db.execute(select(Product).where(Product.store_id == s.id))
            p_count = len(p_res.scalars().all())
            print(f"Store {s.name}: {p_count} products")

if __name__ == "__main__":
    asyncio.run(debug_org())
