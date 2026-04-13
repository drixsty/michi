import asyncio
import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import settings

async def backfill_user_names():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        print("Mise a jour des noms utilisateurs existants via SQL direct...")
        
        # 1. Récupérer les utilisateurs sans noms
        result = await conn.execute(text("SELECT id, email FROM users WHERE first_name IS NULL OR last_name IS NULL"))
        users = result.fetchall()
        
        updated_count = 0
        for user_id, email in users:
            first_name = email.split('@')[0].capitalize()
            last_name = "Michi" if email != "dev@michi.com" else "Admin"
            
            await conn.execute(
                text("UPDATE users SET first_name = :f, last_name = :l WHERE id = :id"),
                {"f": first_name, "l": last_name, "id": user_id}
            )
            updated_count += 1
        
        print(f"SUCCESS: {updated_count} utilisateurs mis a jour.")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(backfill_user_names())
