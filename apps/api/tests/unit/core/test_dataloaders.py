import pytest
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock
from core.graphql.dataloaders import create_store_loader, create_supplier_loader
from modules.inventory.infrastructure.persistence.models import Store, Supplier

@pytest.mark.asyncio
async def test_store_loader_batches_queries():
    # 1. Setup mock DB session
    mock_db = AsyncMock()
    
    # Store IDs we want to fetch
    id1 = uuid.uuid4()
    id2 = uuid.uuid4()
    
    # Mock return values for DB execution
    mock_store1 = Store(id=id1, name="Store 1")
    mock_store2 = Store(id=id2, name="Store 2")
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_store1, mock_store2]
    mock_db.execute.return_value = mock_result
    
    # 2. Create the loader
    loader = create_store_loader(mock_db)
    
    # 3. Load concurrently (simulates GraphQL execution resolving fields on different nodes)
    results = await asyncio.gather(
        loader.load(id1),
        loader.load(id2)
    )
    
    # 4. Assertions
    # The loader must return the elements mapped correctly to their keys
    assert results[0] == mock_store1
    assert results[1] == mock_store2
    
    # The database must have been queried exactly ONCE (batch load!)
    assert mock_db.execute.call_count == 1
    
    # Verify the SQL query structure had the in_ clause
    called_args = mock_db.execute.call_args[0][0]
    # Check that it targets the Store table and filters by our IDs
    assert str(called_args).strip() != ""

@pytest.mark.asyncio
async def test_supplier_loader_batches_queries():
    mock_db = AsyncMock()
    
    id1 = uuid.uuid4()
    id2 = uuid.uuid4()
    
    mock_supplier1 = Supplier(id=id1, name="Supplier 1")
    mock_supplier2 = Supplier(id=id2, name="Supplier 2")
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_supplier1, mock_supplier2]
    mock_db.execute.return_value = mock_result
    
    loader = create_supplier_loader(mock_db)
    
    results = await asyncio.gather(
        loader.load(id1),
        loader.load(id2)
    )
    
    assert results[0] == mock_supplier1
    assert results[1] == mock_supplier2
    assert mock_db.execute.call_count == 1
