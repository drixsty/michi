import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from src.modules.decisions.service import DecisionCenterService
from src.modules.auth.models import User
from src.modules.inventory.models import Store, Product, PlatformSource
from src.modules.forecasting.models import Prediction

@pytest.mark.asyncio
async def test_get_overview_no_user():
    """Test overview when user is not found"""
    db = AsyncMock()
    
    # Mock return for user query (not found)
    mock_res = MagicMock()
    mock_res.scalars.return_value.first.return_value = None
    db.execute.return_value = mock_res
    
    service = DecisionCenterService(db)
    with pytest.raises(Exception, match="Utilisateur non trouvé"):
        await service.get_overview(str(uuid4()))

@pytest.mark.asyncio
async def test_get_overview_empty_org():
    """Test overview when user has no organization"""
    db = AsyncMock()
    user = User(id=uuid4(), current_organization_id=None, preferences={})
    
    # Mock return for user query
    mock_res = MagicMock()
    mock_res.scalars.return_value.first.return_value = user
    db.execute.return_value = mock_res
    
    service = DecisionCenterService(db)
    result = await service.get_overview(str(user.id))
    
    assert result.kpis.inventory_value_cost == 0
    assert result.message == "Pas d'organisation."

@pytest.mark.asyncio
async def test_get_overview_with_data():
    """Test overview with mocked products and predictions"""
    db = AsyncMock()
    org_id = uuid4()
    user = User(id=uuid4(), current_organization_id=org_id, preferences={"currency": "€"})
    
    # 1. User query result
    mock_user_res = MagicMock()
    mock_user_res.scalars.return_value.first.return_value = user
    
    # 2. Stores query result
    store = Store(id=uuid4(), organization_id=org_id, connected=True, platform=PlatformSource.SHOPIFY)
    mock_stores_res = MagicMock()
    mock_stores_res.scalars.return_value.all.return_value = [store]
    
    # 3. Products/Predictions query result
    prod = Product(
        id=uuid4(), 
        sku="SKU1", title="Test Prod", 
        current_stock=10, cost_price=10.0, sale_price=20.0,
        source_platform=PlatformSource.SHOPIFY
    )
    pred = Prediction(product_id=prod.id, run_rate=1.0, reorder_quantity=5)
    mock_data_res = MagicMock()
    mock_data_res.all.return_value = [(prod, pred)]
    
    # Set side effect to return these mocks in order
    db.execute.side_effect = [mock_user_res, mock_stores_res, mock_data_res]
    
    service = DecisionCenterService(db)
    result = await service.get_overview(str(user.id))
    
    assert result.total_stock == 10
    assert result.health_score > 0
    assert result.kpis.inventory_value_cost == 100.0 # 10 * 10.0
    assert len(result.active_platforms) == 1
    assert result.active_platforms[0] == "SHOPIFY"
