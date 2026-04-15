from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from core.config import settings
from core.database.models import User
from core.security.hashing import hash_password

DEMO_EMAIL = "dev@michi.com"
NEW_PASSWORD = "password123"

async def reset_password():
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == DEMO_EMAIL))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User {DEMO_EMAIL} not found.")
            return

        print(f"Resetting password for {DEMO_EMAIL}...")
        user.hashed_password = hash_password(NEW_PASSWORD)
        await session.commit()
        print("Password reset successful.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_password())
