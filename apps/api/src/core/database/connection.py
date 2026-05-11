from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
from core.config.settings import settings

# Engine async
# Configuration conditionnelle de l'engine
engine_kwargs = {
    "echo": settings.ENVIRONMENT == "development",
    "pool_recycle": 3600,
}

# SQLite ne supporte pas pool_size/max_overflow
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 30
else:
    # Pour SQLite in-memory dans les tests, on évite les problèmes de thread
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency pour injecter une session DB dans les resolvers."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            if session.is_active:
                await session.rollback()
            raise
        finally:
            try:
                await session.close()
            except Exception as e:
                # Éviter de crasher la requête si la clôture échoue (déjà loggué par SQLAlchemy)
                import logging
                logging.getLogger("uvicorn.error").warning(f"Error closing session: {e}")
