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
from src.modules.auth.models import User, Organization

async def fix_user():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # 1. Get User
        res = await session.execute(select(User).where(User.email == "dev@michi.com"))
        user = res.scalars().first()
        if not user:
            print("User not found")
            return
            
        # 2. Get any Organization
        res = await session.execute(select(Organization))
        org = res.scalars().first()
        if not org:
            # Create one if missing
            org = Organization(name="Michi Corp")
            session.add(org)
            await session.flush()
            print(f"Created Org: {org.id}")
            
        print(f"Assigning Org {org.id} to user {user.email}")
        user.current_organization_id = org.id
        
        # Ensure password is correct too
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user.hashed_password = pwd_context.hash("michi123")
        
        await session.commit()
        print("User fixed successfully.")

if __name__ == "__main__":
    asyncio.run(fix_user())
