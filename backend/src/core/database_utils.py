import asyncio
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

class SerializedAsyncSession:
    """
    Wrapper pour SQLAlchemy AsyncSession qui sérialise toutes les opérations asynchrones.
    
    Utile pour GraphQL (Strawberry) où les résolveurs s'exécutent en parallèle
    alors que l'AsyncSession ne supporte pas les opérations concurrentes.
    """
    def __init__(self, session: AsyncSession, lock: asyncio.Lock):
        self._session = session
        self._lock = lock

    def __getattr__(self, name: str) -> Any:
        # Récupère l'attribut de la session originale
        attr = getattr(self._session, name)
        
        # Si c'est une coroutine, on l'enveloppe dans le lock
        if asyncio.iscoroutinefunction(attr):
            async def wrapped(*args, **kwargs):
                async with self._lock:
                    # logger.trace(f"[SerializedAsyncSession] Locking for {name}")
                    return await attr(*args, **kwargs)
            return wrapped
            
        return attr

    # Support explicite pour le context manager asynchrone (pour await session.begin())
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # On ne ferme pas la session ici car elle est gérée par get_db (lifespan de la requête)
        pass
