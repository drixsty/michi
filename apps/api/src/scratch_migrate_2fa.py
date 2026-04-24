import asyncio
import sys
import os

# Ajouter src au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import engine
from sqlalchemy import text

async def migrate():
    print("Tentative d'ajout de la colonne recovery_codes...")
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS recovery_codes JSONB;"))
    print("✅ Colonne recovery_codes ajoutée avec succès !")

if __name__ == "__main__":
    asyncio.run(migrate())
