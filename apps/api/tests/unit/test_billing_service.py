import pytest
from unittest.mock import MagicMock, AsyncMock
from modules.billing.application.service import ApplicationBillingService
from core.config import settings
from modules.billing.domain.entities import SubscriptionStatus
import uuid

@pytest.fixture
def mock_provider():
    return AsyncMock()

@pytest.fixture
def mock_repo():
    return AsyncMock()

@pytest.fixture
def billing_service(mock_provider, mock_repo):
    return ApplicationBillingService(provider=mock_provider, repository=mock_repo)

@pytest.mark.asyncio
async def test_create_customer_success(billing_service, mock_provider, mock_repo):
    org_id = str(uuid.uuid4())
    mock_provider.create_customer.return_value = "cus_123"
    
    customer_id = await billing_service.create_customer("Test Org", "admin@test.com", org_id)
    
    assert customer_id == "cus_123"
    mock_provider.create_customer.assert_called_once_with(
        name="Test Org",
        email="admin@test.com",
        org_id=org_id
    )
    mock_repo.update_org_billing_info.assert_called_once_with(
        org_id, customer_id="cus_123", plan=None, status=None
    )

@pytest.mark.asyncio
async def test_create_customer_if_missing_exists(billing_service, mock_repo):
    org_id = str(uuid.uuid4())
    mock_info = MagicMock()
    mock_info.customer_id = "cus_existing"
    mock_repo.get_org_billing_info.return_value = mock_info
    
    customer_id = await billing_service.create_customer_if_missing(org_id)
    
    assert customer_id == "cus_existing"
    mock_repo.get_org_billing_info.assert_called_once_with(org_id)

@pytest.mark.asyncio
async def test_create_checkout_session(billing_service, mock_provider, mock_repo):
    org_id = str(uuid.uuid4())
    # Mock customer check
    mock_info = MagicMock()
    mock_info.customer_id = "cus_123"
    mock_repo.get_org_billing_info.return_value = mock_info
    
    mock_provider.create_checkout_session.return_value = "https://checkout.url"
    
    url = await billing_service.create_checkout_session(
        org_id=org_id,
        plan="PRO",
        success_url="http://success",
        cancel_url="http://cancel"
    )
    
    assert url == "https://checkout.url"
    mock_provider.create_checkout_session.assert_called_once()

@pytest.mark.asyncio
async def test_mock_upgrade_organization(billing_service, mock_repo):
    org_id = str(uuid.uuid4())
    mock_repo.update_org_billing_info.return_value = True
    
    success = await billing_service.mock_upgrade_organization(org_id, "PRO")
    
    assert success is True
    mock_repo.update_org_billing_info.assert_called_once_with(
        org_id=org_id,
        customer_id=None,
        plan="PRO",
        status=SubscriptionStatus.ACTIVE.value
    )
