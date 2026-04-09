import strawberry
from strawberry.extensions import SchemaExtension
from src.core.database import AsyncSessionLocal

class SQLAlchemySessionExtension(SchemaExtension):
    """
    Extension Strawberry pour gérer le cycle de vie de la session SQLAlchemy.
    Garantit que la session est fermée à la fin de chaque exécution GraphQL.
    """
    
    async def on_operation(self):
        # Créer la session pour cette opération
        print(f"DEBUG: Opening DB session for GraphQL operation...")
        session = AsyncSessionLocal()
        self.execution_context.context.db = session
        
        try:
            yield
        except Exception as e:
            print(f"DEBUG: Error during GraphQL operation: {e}")
            raise
        finally:
            print(f"DEBUG: Closing DB session...")
            await session.close()
