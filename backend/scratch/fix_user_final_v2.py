import asyncio
from sqlalchemy import select
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

from src.modules.auth.models import User, Organization
from src.modules.inventory.models import Store, Product

async def fix_user_final():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # 1. Get User
        res = await session.execute(select(User).where(User.email == "dev@michi.com"))
        user = res.scalars().first()
        if not user:
            print("User not found")
            return
            
        # 2. Get Organization
        res = await session.execute(select(Organization))
        org = res.scalars().first()
        if not org:
            org = Organization(name="Michi Corp")
            session.add(org)
            await session.flush()
        
        user.current_organization_id = org.id
        
        # 3. Check and reconnect stores
        res = await session.execute(select(Store).where(Store.organization_id == org.id))
        stores = res.scalars().all()
        for s in stores:
            if not s.connected:
                s.connected = True
                print(f"Reconnected store: {s.name}")
        
        await session.commit()
        print(f"User {user.email} successfully linked to Org {org.id} and stores reconnected.")

if __name__ == "__main__":
    asyncio.run(fix_user_final())
