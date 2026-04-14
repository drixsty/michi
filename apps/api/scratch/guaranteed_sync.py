import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.modules.auth.models import User, Organization
from src.modules.inventory.models import Store

async def force_sync():
    engine = create_async_engine(settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+asyncpg"))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Ensure User exists
        res = await session.execute(select(User).where(User.email == "dev@michi.com"))
        user = res.scalars().first()
        if not user:
            print("Creating dev user...")
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = User(email="dev@michi.com", hashed_password=pwd_context.hash("michi123"))
            session.add(user)
            await session.flush()

        # 2. Get/Create Org
        res = await session.execute(select(Organization))
        org = res.scalars().first()
        if not org:
            print("Creating organization...")
            org = Organization(name="Michi Corp")
            session.add(org)
            await session.flush()
        
        # 3. Force User fields
        user.current_organization_id = org.id
        print(f"User {user.email} -> Org {org.id}")
        
        # 4. Check Stores
        res = await session.execute(select(Store))
        stores = res.scalars().all()
        for s in stores:
            s.organization_id = org.id
            s.connected = True
            print(f"Store {s.name} -> Connected & Linked to Org")

        await session.commit()
        print("Final sync completed.")

if __name__ == "__main__":
    asyncio.run(force_sync())
