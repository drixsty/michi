"""
Fixtures pytest pour les tests
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient

from src.core.database import Base
from src.core.config import settings
from src.main import app
from src.modules.auth.models import User
from src.modules.inventory.models import Product, SalesLog, Supplier, Alert, AlertEmail, PurchaseOrder
from src.modules.forecasting.models import CleanedDemand, Prediction
from src.core.security import hash_password
from src.core.database import get_db


# Database de test (utilise une DB séparée)
TEST_DATABASE_URL = "postgresql+asyncpg://michi:michi123@localhost:5433/michi_test"




@pytest.fixture(scope="function")
async def db_engine():
    """Engine de test (recrée DB à chaque test)"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Session DB de test"""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def test_user(db_session) -> User:
    """Créer un user de test et son store associé"""
    import uuid
    from src.modules.inventory.models import Store, PlatformSource
    
    shop_uuid = uuid.uuid4()
    org_uuid = uuid.uuid4()
    
    from src.modules.auth.models import Organization
    org = Organization(
        id=org_uuid,
        name="Test Org",
        slug=f"test-org-{org_uuid.hex[:6]}"
    )
    db_session.add(org)
    
    store = Store(
        id=shop_uuid,
        organization_id=org_uuid,
        name="Test Store",
        platform=PlatformSource.SHOPIFY,
        connected=True
    )
    db_session.add(store)
    
    user = User(
        email="test@michi.com",
        hashed_password=hash_password("testpassword"),
        shop_id=shop_uuid,
        current_organization_id=org_uuid
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
async def auth_token(test_user) -> str:
    """Token JWT pour user de test"""
    from src.core.security import create_access_token
    
    token = create_access_token({
        "user_id": str(test_user.id),
        "org_id": str(test_user.current_organization_id),
        "email": test_user.email,
    })
    
    return token


@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP de test avec surcharge DB (Générateur)"""
    async def _get_db_override():
        yield db_session
        
    app.dependency_overrides[get_db] = _get_db_override
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
