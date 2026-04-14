import asyncio
import asyncpg

async def create_test_db():
    # Connexion à la base 'postgres' par défaut
    conn = await asyncpg.connect(
        user="michi",
        password="michi123",
        database="postgres",
        host="localhost",
        port=5433
    )
    
    try:
        # On ne peut pas créer de DB dans une transaction, 
        # mais conn.execute() ici devrait suffire si c'est géré par asyncpg.
        # En fait, il vaut mieux utiliser conn.execute() sur une connexion brute.
        await conn.execute("CREATE DATABASE michi_test")
        print("Base de données 'michi_test' créée avec succès.")
    except asyncpg.exceptions.DuplicateDatabaseError:
        print("La base de données 'michi_test' existe déjà.")
    except Exception as e:
        print(f"Erreur lors de la création de la base : {str(e)}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_test_db())
