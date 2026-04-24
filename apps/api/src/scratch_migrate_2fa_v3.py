import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://michi:michi123@localhost:5433/michi_db"

async def migrate():
    print("Connecting to database...")
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as conn:
            print("Running ALTER TABLE...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS recovery_codes JSONB;"))
            print("MIGRATION SUCCESSFUL: recovery_codes column added.")
    except Exception as e:
        print(f"MIGRATION ERROR: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
