import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import sys
import os

# Add parent dir to path to import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.config import settings

async def migrate():
    print(f"Migrating {settings.DATABASE_URL}...")
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        # Add organization_id to users
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id UUID;"))
        # Add financial columns to products
        await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS cost_price FLOAT;"))
        await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS sale_price FLOAT;"))
        print("Columns added successfully.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
