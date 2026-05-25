import asyncio
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result, ScalarResult
from sqlalchemy.exc import InvalidRequestError


class EagerResult:
    """
    Objet résultat statique qui contient déjà toutes les données en mémoire.
    Compatible avec les méthodes courantes de Result de SQLAlchemy.
    """
    def __init__(self, data: list):
        self._data = data

    def all(self):
        return self._data

    def first(self):
        return self._data[0] if self._data else None

    def one(self):
        if len(self._data) == 1:
            return self._data[0]
        if len(self._data) == 0:
            raise Exception("No result found for one()")
        raise Exception(f"Expected one result, found {len(self._data)}")

    def one_or_none(self):
        if len(self._data) == 1:
            return self._data[0]
        if len(self._data) == 0:
            return None
        raise Exception(f"Expected at most one result, found {len(self._data)}")

    def scalar(self):
        row = self.first()
        return row[0] if row and isinstance(row, (list, tuple, object)) and hasattr(row, '__getitem__') else row

    def scalar_one(self):
        row = self.one()
        return row[0] if row and isinstance(row, (list, tuple, object)) and hasattr(row, '__getitem__') else row

    def scalar_one_or_none(self):
        row = self.one_or_none()
        if row is None: return None
        return row[0] if row and isinstance(row, (list, tuple, object)) and hasattr(row, '__getitem__') else row

    def scalars(self):
        def _get_scalar(row):
            # If it's a SQLAlchemy Row or a sequence, extract the first element.
            # We check if it's a sequence but NOT a model instance (which might have _sa_instance_state).
            if hasattr(row, '__getitem__') and not hasattr(row, '_sa_instance_state') and not isinstance(row, (str, bytes, dict)):
                try:
                    return row[0]
                except (IndexError, TypeError):
                    return row
            return row

        return EagerScalarResult([_get_scalar(row) for row in self._data])

    def __iter__(self):
        return iter(self._data)

    def unique(self):
        return self

class EagerScalarResult:
    def __init__(self, data: list):
        self._data = data

    def all(self):
        return self._data

    def first(self):
        return self._data[0] if self._data else None

    def one(self):
        if len(self._data) == 1:
            return self._data[0]
        if len(self._data) == 0:
             raise Exception("No result found for one()")
        raise Exception(f"Expected one result, found {len(self._data)}")

    def one_or_none(self):
        if len(self._data) == 1:
            return self._data[0]
        if len(self._data) == 0:
            return None
        raise Exception(f"Expected at most one result, found {len(self._data)}")

    def __iter__(self):
        return iter(self._data)

    def unique(self):
        return self

from typing import Optional
from contextvars import ContextVar
import uuid

# Identifiant unique du flux d'exécution actuel (Request/Worker)
# Permet au ReentrantAsyncLock de savoir s'il peut ré-entrer.
session_flow_id: ContextVar[Optional[str]] = ContextVar("session_flow_id", default=None)

class ReentrantAsyncLock:
    """
    Verrou asynchrone ré-entrant basé sur ContextVar.
    Permet à un même flux d'exécution (Request GraphQL ou boucle de Worker)
    d'acquérir le verrou plusieurs fois sans s'auto-bloquer.
    """
    def __init__(self):
        self._lock = asyncio.Lock()
        self._owner_id = None
        self._count = 0

    async def acquire(self):
        me = session_flow_id.get()
        if me is None:
            me = str(uuid.uuid4())
            session_flow_id.set(me)

        if self._owner_id == me:
            self._count += 1
            return
            
        await self._lock.acquire()
        self._owner_id = me
        self._count = 1

    def release(self):
        me = session_flow_id.get()
        if self._owner_id != me:
            return
            
        self._count -= 1
        if self._count == 0:
            self._owner_id = None
            self._lock.release()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    class SerializedAsyncSession(AsyncSession):
        pass
else:
    class SerializedAsyncSession:
        pass


class SerializedAsyncSession(SerializedAsyncSession):
    """
    Wrapper pour SQLAlchemy AsyncSession qui sérialise toutes les opérations asynchrones.
    
    FORCE la consommation immédiate des résultats pour garantir que la connexion
    est libre (IDLE) dès que le verrou est relâché.
    """
    def __init__(self, session: AsyncSession, lock: ReentrantAsyncLock):
        self._session = session
        self._lock = lock

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            return getattr(self._session, name)

        attr = getattr(self._session, name)
        
        async_methods = ['execute', 'commit', 'rollback', 'flush', 'refresh', 'get', 'scalar', 'scalars', 'begin', 'merge', 'delete']
        
        if asyncio.iscoroutinefunction(attr) or name in async_methods:
            async def wrapped(*args, **kwargs):
                async with self._lock:
                    result = await attr(*args, **kwargs)
                    
                    # --- Eager Result Draining (V3) ---
                    has_all = hasattr(result, 'all')
                    
                    if has_all and not isinstance(result, (EagerResult, EagerScalarResult)):
                        is_scalar = hasattr(result, 'scalars') is False
                        
                        try:
                            # We drain all rows first to avoid partial consumption if unique() fails
                            data = result.all()
                            
                            # Attempt manual deduplication if unique was likely intended
                            if hasattr(result, '_unique_filter_state'):
                                try:
                                    data = list(dict.fromkeys(data))
                                except TypeError:
                                    pass
                                    
                            if is_scalar:
                                return EagerScalarResult(data)
                            return EagerResult(data)
                        except Exception as e:
                            return result
                        
                    return result
            return wrapped
            
        return attr

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
