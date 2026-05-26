import sys
import os
import pytest
import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import select
from httpx import AsyncClient

# 1. Setup environment variables BEFORE core imports
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "test_secret_key_123_test_secret_key_123"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_mock"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_mock"
os.environ["BILLING_MODE"] = "STRIPE"
os.environ["SHOPIFY_API_KEY"] = "mock_key"
os.environ["SHOPIFY_API_SECRET"] = "mock_secret"
os.environ["SMTP_HOST"] = "localhost"
os.environ["SMTP_PORT"] = "587"
os.environ["SMTP_USER"] = "test@michi.app"
os.environ["SMTP_PASSWORD"] = "your_password"
os.environ["EMAIL_FROM"] = "noreply@michi.app"
os.environ["STRIPE_PRICE_STARTER"] = "price_1"
os.environ["STRIPE_PRICE_PRO"] = "price_2"
os.environ["STRIPE_PRICE_ENTERPRISE"] = "price_3"

from core.database import Base, get_db
from core.database.models import User, Organization, OrganizationMember
from modules.auth.infrastructure.persistence.models import Invitation
from modules.inventory.infrastructure.persistence.models import Product, SalesLog, Supplier, Alert, AlertEmail, PurchaseOrder, Store, StoreCredential
from modules.forecasting.infrastructure.persistence.models import Prediction
from core.security.hashing import hash_password


@pytest.fixture(scope="session")
async def db_engine():
    """Create a session-wide database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a function-scoped database session."""
    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="function")
async def test_user(db_session) -> User:
    """Create a test user and organization."""
    try:
        user = User(
            id=uuid.uuid4(),
            email=f"test_{uuid.uuid4().hex[:8]}@michi.com",
            hashed_password=hash_password("password123"),
            is_active=True
        )
        db_session.add(user)
        
        org = Organization(
            id=uuid.uuid4(),
            name="Test Org", 
            slug=f"test-org-{uuid.uuid4().hex[:6]}", 
            plan="PRO"
        )
        db_session.add(org)
        await db_session.flush()
        
        user.current_organization_id = org.id
        from core.database.constants import UserRole
        member = OrganizationMember(organization_id=org.id, user_id=user.id, role=UserRole.ADMIN)
        db_session.add(member)
        await db_session.flush()
        
        return user
    except Exception as e:
        sys.stderr.write(f">>> [ERROR] test_user fixture failed: {str(e)}\n")
        raise e

@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient for integration testing."""
    from main import app
    
    # Override get_db dependency
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def auth_token(test_user) -> str:
    """Generate a valid JWT token for the test user."""
    from core.security import create_access_token
    token_data = {
        "user_id": str(test_user.id),
        "org_id": str(test_user.current_organization_id),
        "email": test_user.email
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def auth_headers(auth_token) -> dict[str, str]:
    """Provide authentication headers for integration tests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
async def test_organization(db_session, test_user) -> Organization:
    """Retrieve the test organization associated with the test user."""
    result = await db_session.execute(
        select(Organization).where(Organization.id == test_user.current_organization_id)
    )
    return result.scalar_one()
