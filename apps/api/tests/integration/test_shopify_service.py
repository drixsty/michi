import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from src.modules.shopify.application.service import ShopifyService
from src.modules.inventory.domain.entities import PlatformSource
from src.modules.inventory.infrastructure.persistence.models import Product, SalesLog

@pytest.mark.asyncio
async def test_trigger_mock_sync_success():
    """Test successful mock synchronization for Shopify"""
    db = AsyncMock()
    store_id = str(uuid4())
    
    # 1. Existing products mock
    mock_existing_res = MagicMock()
    mock_existing_res.scalars.return_value.all.return_value = []
    
    # 2. Suppliers mock
    mock_suppliers_res = MagicMock()
    mock_suppliers_res.scalars.return_value.all.return_value = []
    
    # 3. Data generation mock
    mock_products = [
        {"id": "temp-1", "sku": "SKU1", "title": "Prod 1", "current_stock": 10, "store_id": store_id, "source_platform": PlatformSource.SHOPIFY}
    ]
    mock_sales = [
        {"product_id": "temp-1", "units_sold": 2, "date": "2024-01-01"}
    ]
    
    db.execute.side_effect = [mock_existing_res, mock_suppliers_res, MagicMock()] # 3rd is delete saleslogs
    
    with patch("src.modules.shopify.application.service.generate_full_mock_dataset", return_value=(mock_products, mock_sales)):
        service = ShopifyService(db)
        result = await service.trigger_mock_sync(store_id)
        
        assert result.success is True
        assert result.products_created == 1
        assert result.sales_logs_created == 1
        assert "Sync mock" in result.message
        
        # Verify db.add was called for the new product
        assert db.add.called
        # Verify db.add_all was called for sales logs
        assert db.add_all.called

@pytest.mark.asyncio
async def test_trigger_mock_sync_update_existing():
    """Test updating existing products during sync"""
    db = AsyncMock()
    store_id = str(uuid4())
    
    existing_p = Product(sku="SKU1", title="Old Title", current_stock=5, source_platform=PlatformSource.SHOPIFY)
    
    mock_existing_res = MagicMock()
    mock_existing_res.scalars.return_value.all.return_value = [existing_p]
    
    mock_suppliers_res = MagicMock()
    mock_suppliers_res.scalars.return_value.all.return_value = []
    
    mock_products = [
        {"id": "temp-1", "sku": "SKU1", "title": "New Title", "current_stock": 20, "store_id": store_id, "source_platform": PlatformSource.SHOPIFY}
    ]
    
    db.execute.side_effect = [mock_existing_res, mock_suppliers_res, MagicMock()]
    
    with patch("src.modules.shopify.application.service.generate_full_mock_dataset", return_value=(mock_products, [])):
        service = ShopifyService(db)
        await service.trigger_mock_sync(store_id)
        
        assert existing_p.title == "New Title"
        assert existing_p.current_stock == 20


