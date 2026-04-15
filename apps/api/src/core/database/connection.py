from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
from core.config.settings import settings

# Engine async
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_recycle=3600,  # Refresh connections every hour
    pool_size=20,
    max_overflow=30,
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
            # Final commit only if session is still active and has uncommitted changes
            if session.is_active:
                await session.commit()
        except Exception:
            if session.is_active:
                await session.rollback()
            raise
        finally:
            await session.close()
