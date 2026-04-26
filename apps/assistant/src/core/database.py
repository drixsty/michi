from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from core.config.settings import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    # Import des modèles ici pour s'assurer qu'ils sont enregistrés dans Base.metadata
    from modules.chat.infrastructure.models import ChatSessionModel, ChatMessageModel
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
