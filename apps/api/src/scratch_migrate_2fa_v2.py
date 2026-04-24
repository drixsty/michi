import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://michi:michi123@localhost:5433/michi_db"

async def migrate():
    print(f"Connexion à {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as conn:
            print("Vérification et ajout de la colonne recovery_codes...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS recovery_codes JSONB;"))
            print("✅ Migration réussie : colonne recovery_codes opérationnelle.")
    except Exception as e:
        print(f"❌ Erreur lors de la migration : {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
