"""
Fixtures pytest pour les tests Michi - Sprint 22
Utilise une base SQLite éphémère (in-memory) pour la rapidité et l'isolation.
"""
import pytest
import asyncio
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient

# --- Mock environment variables for Pydantic Settings ---
# This ensures API tests can run without a .env file (Hexagonal logic)
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost:5432/db"
os.environ["SECRET_KEY"] = "test-secret-key-12345"
os.environ["ENVIRONMENT"] = "testing"
os.environ["MASTER_ENCRYPTION_KEY"] = "rE-f4L_Xp-6_T7_Y_p-8_D7_W_p-9_A7_Z_p-0_B7_C=" # Fernet valid dummy key

# SMTP
os.environ["SMTP_HOST"] = "localhost"
os.environ["SMTP_PORT"] = "1025"
os.environ["SMTP_USER"] = "test"
os.environ["SMTP_PASSWORD"] = "test"
os.environ["EMAIL_FROM"] = "test@michi.io"

# Shopify
os.environ["SHOPIFY_API_KEY"] = "test_key"
os.environ["SHOPIFY_API_SECRET"] = "test_secret"
os.environ["SHOPIFY_REDIRECT_URI"] = "http://localhost/callback"
os.environ["SHOPIFY_SCOPES"] = "read_products"

# Stripe
os.environ["STRIPE_API_KEY"] = "sk_test_api"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
os.environ["BILLING_MODE"] = "MOCK"
os.environ["STRIPE_PRICE_BASIC"] = "price_1"
os.environ["STRIPE_PRICE_PRO"] = "price_2"
os.environ["STRIPE_PRICE_ENTERPRISE"] = "price_3"
# --- End of Mock ---

from core.database import Base, get_db
from main import app

# Utilisation des modèles centralisés dans Core
from core.database.models import User, Organization, OrganizationMember, Invitation
from modules.inventory.infrastructure.persistence.models import Product, SalesLog, Supplier, Alert, AlertEmail, PurchaseOrder, Store, StoreCredential
from core.security.hashing import hash_password

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
        # Initialisation de la session sur la connexion avec transaction
        session = AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")
        
        yield session
        
        await session.close()
        await transaction.rollback()

@pytest.fixture(scope="function")
async def test_user(db_session) -> User:
    """Créer un user de test et son organisation/store associés"""
    import uuid
    from modules.inventory.domain.entities import PlatformSource
    from modules.auth.domain.entities import UserRole
    # Models are in infrastructure
    from core.database.models import Organization, OrganizationMember, User
    from modules.inventory.infrastructure.persistence.models import Store
    
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
        email=f"test_{user_uuid.hex[:8]}@michi.com",
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
    from core.middleware.auth import create_access_token
    
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
