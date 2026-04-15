import asyncio
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

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
        # Ne pas envelopper les attributs internes (protection SQLA)
        if name.startswith("_"):
            return getattr(self._session, name)

        # Récupère l'attribut de la session originale
        attr = getattr(self._session, name)
        
        # Si c'est une coroutine ou une méthode asynchrone, on l'enveloppe dans le lock
        if asyncio.iscoroutinefunction(attr) or name in ['execute', 'commit', 'rollback', 'flush', 'refresh', 'get', 'scalar', 'scalars', 'begin']:
            async def wrapped(*args, **kwargs):
                async with self._lock:
                    return await attr(*args, **kwargs)
            return wrapped
            
        return attr

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
