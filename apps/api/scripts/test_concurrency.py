import asyncio
import os
import sys

# Ajouter le répertoire courant (backend) au PYTHONPATH pour trouver 'src'
sys.path.append(os.getcwd())

from sqlalchemy import select
from michi_core.database import AsyncSessionLocal
from michi_core.database_utils import SerializedAsyncSession

async def test_concurrency():
    print("Démarrage du test de concurrence...")
    
    async with AsyncSessionLocal() as session:
        lock = asyncio.Lock()
        serialized_db = SerializedAsyncSession(session, lock)
        
        # Simuler 10 opérations concurrentes
        async def run_query(i):
            print(f"  [Tâche {i}] Début requête...")
            result = await serialized_db.execute(select(1))
            val = result.scalar()
            print(f"  [Tâche {i}] Fin requête : {val}")
            return val

        print("Lancement de 10 requêtes en // via asyncio.gather...")
        try:
            results = await asyncio.gather(*(run_query(i) for i in range(10)))
            print(f"Succès ! {len(results)} requêtes traitées sans erreur de confluence.")
        except Exception as e:
            print(f"ÉCHEC : Une erreur est survenue : {e}")
            sys.exit(1)

if __name__ == "__main__":
    # S'assurer qu'on est au bon endroit
    if not os.path.exists("src"):
        print("Erreur : Ce script doit être lancé depuis le dossier 'backend'.")
        sys.exit(1)
        
    asyncio.run(test_concurrency())
