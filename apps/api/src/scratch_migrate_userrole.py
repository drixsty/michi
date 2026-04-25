import asyncio
from sqlalchemy import text
from core.database import AsyncSessionLocal

async def migrate_enum():
    async with AsyncSessionLocal() as session:
        try:
            print("[MIGRATE] Adding 'owner' and 'OWNER' to userrole enum...")
            await session.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'owner'"))
            await session.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'OWNER'"))
            await session.commit()
            print("[MIGRATE] Success! ✅")
        except Exception as e:
            print(f"[ERROR] Migration failed: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(migrate_enum())
