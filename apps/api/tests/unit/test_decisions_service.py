import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime
from modules.decisions.application.decisions_service import ApplicationDecisionsService
from modules.auth.infrastructure.persistence.models import User
from modules.inventory.domain.entities import PlatformSource
from modules.inventory.infrastructure.persistence.models import Store, Product
from modules.forecasting.infrastructure.persistence.models import Prediction

from tests.unit.auth.fakes import FakeUserRepository, FakeOrganizationRepository
from tests.unit.auth.fakes import FakeDb # For the others if needed, but let's use more specific fakes

from modules.auth.domain.entities import UserEntity, OrganizationEntity
from modules.auth.domain.value_objects import Email
from modules.inventory.domain.entities import ProductEntity, PlatformSource
from modules.forecasting.domain.entities import PredictionEntity

@pytest.mark.asyncio
async def test_get_overview_no_user():
    """Test overview when user is not found"""
    user_repo = FakeUserRepository()
    store_repo = AsyncMock()
    prod_repo = AsyncMock()
    pred_repo = AsyncMock()
    
    service = ApplicationDecisionsService(user_repo, store_repo, prod_repo, pred_repo)
    with pytest.raises(Exception, match="Utilisateur non trouvé"):
        await service.get_overview(str(uuid4()))

@pytest.mark.asyncio
async def test_get_overview_empty_org():
    """Test overview when user has no organization"""
    user_repo = FakeUserRepository()
    user = UserEntity(
        id=uuid4(),
        email=Email("test@michi.com"),
        first_name="Test",
        last_name="User",
        is_active=True,
        created_at=datetime.utcnow(),
        current_organization_id=None
    )
    user_repo.seed_user(user)
    
    store_repo = AsyncMock()
    prod_repo = AsyncMock()
    pred_repo = AsyncMock()
    
    service = ApplicationDecisionsService(user_repo, store_repo, prod_repo, pred_repo)
    result = await service.get_overview(str(user.id))
    
    assert result.kpis.inventory_value_cost == 0
    assert result.message == "Pas d'organisation active."

@pytest.mark.asyncio
async def test_get_overview_with_data():
    """Test overview with mocked products and predictions"""
    org_id = uuid4()
    user = UserEntity(
        id=uuid4(),
        email=Email("test@michi.com"),
        first_name="Test",
        last_name="User",
        is_active=True,
        created_at=datetime.utcnow(),
        current_organization_id=org_id,
        preferences={"currency": "€"}
    )
    user_repo = FakeUserRepository()
    user_repo.seed_user(user)

    store_repo = AsyncMock()
    # Mock stores list
    store = MagicMock()
    store.id = uuid4()
    store.platform.value = "SHOPIFY"
    store_repo.list_by_organization.return_value = [store]

    prod_repo = AsyncMock()
    # Mock products list
    prod = ProductEntity(
        id=uuid4(),
        sku="SKU1",
        title="Test Prod",
        current_stock=10,
        cost_price=10.0,
        sale_price=20.0,
        source_platform=PlatformSource.SHOPIFY,
        store_id=store.id
    )
    prod_repo.list_by_store.return_value = [prod]

    pred_repo = AsyncMock()
    # Mock predictions list
    pred = PredictionEntity(
        id=uuid4(),
        product_id=prod.id,
        run_rate=1.0,
        reorder_quantity=5
    )
    pred_repo.list_by_organization.return_value = [pred]
    
    service = ApplicationDecisionsService(user_repo, store_repo, prod_repo, pred_repo)
    result = await service.get_overview(str(user.id))
    
    assert result.total_stock == 10
    assert result.health_score > 0
    assert result.kpis.inventory_value_cost == 100.0 # 10 * 10.0
    assert len(result.active_platforms) == 1
    assert result.active_platforms[0] == "SHOPIFY"

