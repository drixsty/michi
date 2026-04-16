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

async def check_user():
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == "dev@michi.com"))
        user = result.scalar_one_or_none()
        if user:
            print(f"User found: {user.email}")
            print(f"ID: {user.id}")
            print(f"Hashed Password: {user.hashed_password[:10]}...")
            print(f"Is Active: {user.is_active}")
            print(f"Current Org: {user.current_organization_id}")
        else:
            print("User NOT FOUND")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_user())
