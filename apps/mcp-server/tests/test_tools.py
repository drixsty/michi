import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add src to python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.tools import (
    get_inventory_status,
    get_replenishment_alerts,
    simulate_forecast,
    generate_purchase_order,
    trigger_data_sync
)

@pytest.mark.asyncio
@patch("tools.tools.client")
@patch("tools.tools._get_auth_credentials")
async def test_get_inventory_status(mock_auth, mock_client):
    mock_auth.return_value = ("org1", "jwt1")
    mock_client.get_omnichannel_inventory = AsyncMock(return_value=[
        {"sku": "SKU1", "title": "Product 1", "totalStock": 10, "daysOfStock": 30, "riskValue": 0.0}
    ])
    
    res = await get_inventory_status()
    assert "SKU1" in res
    assert "Product 1" in res
    mock_client.get_omnichannel_inventory.assert_called_once_with("org1", "jwt1")

@pytest.mark.asyncio
@patch("tools.tools.client")
@patch("tools.tools._get_auth_credentials")
async def test_get_replenishment_alerts(mock_auth, mock_client):
    mock_auth.return_value = ("org1", "jwt1")
    mock_client.get_predictions = AsyncMock(return_value=[
        {
            "sku": "SKU1",
            "title": "Product 1",
            "runRate": 1.5,
            "predictedStockoutDate": "2026-07-01",
            "replenishmentQuantity": 50,
            "reorderAlertDate": "2026-06-15"
        }
    ])
    
    res = await get_replenishment_alerts()
    assert "SKU1" in res
    assert "2026-07-01" in res
    assert "50" in res

@pytest.mark.asyncio
@patch("tools.tools.client")
@patch("tools.tools._get_auth_credentials")
async def test_simulate_forecast(mock_auth, mock_client):
    mock_auth.return_value = ("org1", "jwt1")
    mock_client.get_predictions = AsyncMock(return_value=[
        {
            "sku": "SKU1",
            "title": "Product 1",
            "runRate": 1.5,
            "replenishmentQuantity": 50
        }
    ])
    
    res = await simulate_forecast(sku="SKU1", safety_factor=1.5)
    assert "SKU1" in res
    assert "75 units" in res

@pytest.mark.asyncio
@patch("tools.tools.client")
@patch("tools.tools._get_auth_credentials")
async def test_generate_purchase_order(mock_auth, mock_client):
    mock_auth.return_value = ("org1", "jwt1")
    mock_client.create_purchase_order = AsyncMock(return_value={
        "id": "po123",
        "quantity": 100,
        "status": "DRAFT",
        "createdAt": "2026-06-13T12:00:00"
    })
    
    res = await generate_purchase_order(product_id="prod1", supplier_id="sup1", quantity=100)
    assert "po123" in res
    assert "DRAFT" in res

@pytest.mark.asyncio
@patch("tools.tools.client")
@patch("tools.tools._get_auth_credentials")
async def test_trigger_data_sync(mock_auth, mock_client):
    mock_auth.return_value = ("org1", "jwt1")
    mock_client.run_prediction_pipeline = AsyncMock(return_value={
        "success": True,
        "productsProcessed": 5,
        "message": "Sync complete"
    })
    
    res = await trigger_data_sync(store_id="store1")
    assert "Sync complete" in res
    assert "5" in res
