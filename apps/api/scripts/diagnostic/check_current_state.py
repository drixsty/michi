import asyncio
from core.database import AsyncSessionLocal
from modules.auth.models import User, Organization
from modules.inventory.models import Store, Product
from sqlalchemy import select
import modules.auth.models
import modules.inventory.models
import modules.forecasting.models

async def run():
    async with AsyncSessionLocal() as db:
        # 1. User
        res = await db.execute(select(User).where(User.email == 'dev@michi.com'))
        u = res.scalars().first()
        print(f"USER: {u.id}, ORG: {u.current_organization_id}")
        
        # 2. Stores in this org
        org_id = u.current_organization_id
        res = await db.execute(select(Store).where(Store.organization_id == org_id))
        stores = res.scalars().all()
        for s in stores:
            print(f"STORE: {s.name}, PLATFORM: {s.platform}, CONNECTED: {s.connected}")
            
        # 3. Products per platform
        for s in stores:
            p_res = await db.execute(select(Product).where(Product.store_id == s.id))
            p_count = len(p_res.scalars().all())
            print(f"STORE {s.name}: {p_count} products")
            
        # 4. Global Query Simulation
        from modules.decisions.service import DecisionCenterService
        service = DecisionCenterService(db)
        overview = await service.get_overview(str(u.id), store_id=None, channel=None)
        print(f"\nGLOBAL OVERVIEW:")
        print(f"Total Stock: {overview.total_stock}")
        print(f"Total Risks: {len(overview.top_risks)}")
        print(f"Inventory Value (Cost): {overview.kpis.inventory_value_cost}")
        print(f"Active Platforms in Overview: {overview.active_platforms}")

if __name__ == "__main__":
    asyncio.run(run())
