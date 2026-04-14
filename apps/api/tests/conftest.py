"""
Fixtures pytest pour les tests Michi - Sprint 22
Utilise une base SQLite éphémère (in-memory) pour la rapidité et l'isolation.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient

from michi_core.database import Base
from michi_core.config import settings
from michi_core.database import get_db
from src.main import app

# Imports des modèles pour enregistrement dans Metadata
from src.modules.auth.infrastructure.persistence.models import User, Organization, OrganizationMember, Invitation
from src.modules.inventory.infrastructure.persistence.models import Product, SalesLog, Supplier, Alert, AlertEmail, PurchaseOrder, Store
from src.modules.forecasting.infrastructure.persistence.models import CleanedDemand, Prediction
from michi_core.security import hash_password

# Database de test éphémère (SQLite Async)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    """Engine de test global pour la session"""
    # StaticPool est requis pour garder la base SQLite :memory: vivante entre les connexions
    engine = create_async_engine(
        TEST_DATABASE_URL, 
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    async with engine.begin() as conn:
        print(f"[DEBUG] Metadata tables: {list(Base.metadata.tables.keys())}")
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Session DB de test isolée par test (via transaction)"""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # On utilise une transaction imbriquée pour pouvoir rollback après chaque test
    async with db_engine.connect() as conn:
        transaction = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")
        
        yield session
        
        await session.close()
        await transaction.rollback()

@pytest.fixture(scope="function")
async def test_user(db_session) -> User:
    """Créer un user de test et son organisation/store associés"""
    import uuid
    from src.modules.inventory.models import Store, PlatformSource
    from src.modules.auth.models import Organization, OrganizationMember, UserRole
    
    shop_uuid = uuid.uuid4()
    org_uuid = uuid.uuid4()
    user_uuid = uuid.uuid4()
    
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
        id=user_uuid,
        email="test@michi.com",
        hashed_password=hash_password("testpassword"),
        shop_id=shop_uuid,
        current_organization_id=org_uuid
    )
    db_session.add(user)
    await db_session.flush()

    member = OrganizationMember(
        organization_id=org_uuid,
        user_id=user_uuid,
        role=UserRole.ADMIN
    )
    db_session.add(member)
    
    await db_session.commit()
    await db_session.refresh(user)
    
    return user

@pytest.fixture(scope="function")
async def auth_token(test_user) -> str:
    """Token JWT pour user de test"""
    from michi_core.security import create_access_token
    
    token = create_access_token({
        "user_id": str(test_user.id),
        "org_id": str(test_user.current_organization_id),
        "email": test_user.email,
    })
    
    return token

@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP de test avec surcharge DB"""
    async def _get_db_override():
        yield db_session
        
    app.dependency_overrides[get_db] = _get_db_override
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
