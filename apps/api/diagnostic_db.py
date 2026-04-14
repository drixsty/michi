
import asyncio
import uuid
from sqlalchemy import select, func
from src.core.database import AsyncSessionLocal
from src.modules.inventory.models import Product, SourceConnection, PlatformSource
from src.modules.auth.models import User

async def diag():
    async with SessionLocal() as db:
        # 1. On prend le premier shop existant
        user_res = await db.execute(select(User).limit(1))
        user = user_res.scalars().first()
        if not user:
            print("No user found")
            return
            
        shop_id = user.shop_id
        print(f"Checking shop: {shop_id}")
        
        # 2. Vérifier les connexions
        conn_res = await db.execute(select(SourceConnection).where(SourceConnection.shop_id == shop_id))
        conns = conn_res.scalars().all()
        print("\nConnections:")
        for c in conns:
            print(f"- {c.platform.value}: connected={c.connected}")
            
        # 3. Compter les produits par plateforme
        prod_res = await db.execute(
            select(Product.source_platform, func.count(Product.id))
            .where(Product.shop_id == shop_id)
            .group_by(Product.source_platform)
        )
        counts = prod_res.all()
        print("\nProducts in DB:")
        for platform, count in counts:
            print(f"- {platform.value}: {count} products")

if __name__ == "__main__":
    asyncio.run(diag())
