import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

SRC_PATH = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))
load_dotenv(Path(__file__).parent.parent / ".env")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from core.config import settings
from core.database.models import User
from core.security.hashing import verify_password

async def verify_db_password():
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == "dev@michi.com"))
        user = result.scalar_one_or_none()
        if user:
            print(f"User: {user.email}")
            print(f"Stored Hash: {user.hashed_password}")
            is_valid = verify_password("password123", user.hashed_password)
            print(f"Verify 'password123': {is_valid}")
        else:
            print("User NOT FOUND")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_db_password())
