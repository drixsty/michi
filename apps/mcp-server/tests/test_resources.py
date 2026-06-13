import pytest
import sys
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add src to python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from resources.resources import (
    get_product_resource,
    get_alerts_resource,
    get_suppliers_resource,
    get_kpis_resource
)

@pytest.mark.asyncio
@patch("resources.resources.client")
@patch("resources.resources._get_auth_credentials")
async def test_get_product_resource(mock_auth, mock_client):
    mock_auth.return_value = ("org1", "jwt1")
    mock_client.get_predictions = AsyncMock(return_value=[
        {"sku": "SKU1", "title": "Product 1"}
    ])
    
    res_str = await get_product_resource(sku="SKU1")
    data = json.loads(res_str)
    assert data["sku"] == "SKU1"
    assert data["title"] == "Product 1"

@pytest.mark.asyncio
@patch("resources.resources.client")
@patch("resources.resources._get_auth_credentials")
async def test_get_alerts_resource(mock_auth, mock_client):
    mock_auth.return_value = ("org1", "jwt1")
    mock_client.get_predictions = AsyncMock(return_value=[
        {"sku": "SKU1", "title": "Product 1"}
    ])
    
    res_str = await get_alerts_resource()
    data = json.loads(res_str)
    assert isinstance(data, list)
    assert data[0]["sku"] == "SKU1"

@pytest.mark.asyncio
@patch("resources.resources.client")
@patch("resources.resources._get_auth_credentials")
async def test_get_suppliers_resource(mock_auth, mock_client):
    mock_auth.return_value = ("org1", "jwt1")
    mock_client.get_suppliers = AsyncMock(return_value=[
        {"id": "sup1", "name": "Supplier 1", "leadTime": 14, "moq": 50}
    ])
    
    res_str = await get_suppliers_resource()
    data = json.loads(res_str)
    assert isinstance(data, list)
    assert data[0]["id"] == "sup1"

@pytest.mark.asyncio
@patch("resources.resources.client")
@patch("resources.resources._get_auth_credentials")
async def test_get_kpis_resource(mock_auth, mock_client):
    mock_auth.return_value = ("org1", "jwt1")
    mock_client.get_dashboard_kpis = AsyncMock(return_value={
        "totalProducts": 10,
        "actualStockouts": 2,
        "urgentAlerts": 1,
        "predictedStockouts30d": 3,
        "message": "Healthy"
    })
    
    res_str = await get_kpis_resource()
    data = json.loads(res_str)
    assert data["totalProducts"] == 10
    assert data["actualStockouts"] == 2
