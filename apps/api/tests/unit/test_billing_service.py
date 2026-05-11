import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from modules.billing.application.service import BillingService
from config import settings
import uuid

@pytest.fixture
def billing_service():
    with patch.object(settings, 'BILLING_MODE', 'STRIPE'):
        return BillingService()

@pytest.fixture
def mock_billing_service():
    with patch.object(settings, 'BILLING_MODE', 'MOCK'):
        return BillingService()

@pytest.mark.asyncio
async def test_create_customer_mock(mock_billing_service):
    org_id = str(uuid.uuid4())
    customer_id = await mock_billing_service.create_customer("Test Org", "admin@test.com", org_id)
    assert customer_id == f"cus_mock_{org_id[:8]}"

@pytest.mark.asyncio
async def test_create_customer_stripe_success(billing_service):
    with patch('stripe.Customer.create') as mock_create:
        mock_create.return_value.id = "cus_123456"
        customer_id = await billing_service.create_customer("Test Org", "admin@test.com", "org-123")
        assert customer_id == "cus_123456"
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_get_checkout_url_success(billing_service):
    with patch('stripe.checkout.Session.create') as mock_create:
        mock_create.return_value.url = "https://checkout.stripe.com/pay/123"
        url = await billing_service.get_checkout_url("cus_123", "http://success", "http://cancel", "price_123")
        assert url == "https://checkout.stripe.com/pay/123"

@pytest.mark.asyncio
async def test_get_invoices_mock(mock_billing_service):
    invoices = await mock_billing_service.get_invoices("cus_mock", "PRO")
    assert len(invoices) == 12
    assert invoices[0]["amount"] == 49.0
    assert invoices[0]["status"] == "PAID"

@pytest.mark.asyncio
async def test_get_invoices_mock_basic(mock_billing_service):
    invoices = await mock_billing_service.get_invoices("cus_mock", "BASIC")
    assert len(invoices) == 0

@pytest.mark.asyncio
async def test_mock_upgrade_organization():
    # We need to mock the DB session for this
    db = AsyncMock()
    mock_res = MagicMock()
    mock_org = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_org
    db.execute.return_value = mock_res
    
    service = BillingService()
    org_id = str(uuid.uuid4())
    success = await service.mock_upgrade_organization(db, org_id, "PRO")
    
    assert success is True
    assert mock_org.plan == "PRO"
    assert mock_org.subscription_status == "ACTIVE"
    db.commit.assert_called_once()
