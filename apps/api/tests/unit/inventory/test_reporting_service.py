import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta
from modules.inventory.application.reporting_service import ReportingService

@pytest.fixture
def mock_repos():
    return {
        "product": AsyncMock(),
        "sales": AsyncMock(),
        "store": AsyncMock(),
        "alert": AsyncMock(),
        "email": AsyncMock()
    }

@pytest.fixture
def service(mock_repos):
    return ReportingService(
        product_repo=mock_repos["product"],
        sales_log_repo=mock_repos["sales"],
        store_repo=mock_repos["store"],
        alert_repo=mock_repos["alert"],
        email_service=mock_repos["email"]
    )

@pytest.mark.asyncio
async def test_reporting_weekly_nominal_flow(service, mock_repos):
    """Test du flux nominal hebdomadaire avec des données mixtes."""
    org_id = uuid4()
    
    # Mocks
    mock_repos["sales"].get_total_sales_for_org.return_value = 5000.0
    mock_repos["store"].list_by_organization.return_value = [MagicMock(id=uuid4())]
    
    p_critical = MagicMock(title="Product Crit", sku="SKU-CRIT", current_stock=0, lead_time=14)
    p_healthy = MagicMock(title="Product OK", sku="SKU-OK", current_stock=100, lead_time=14)
    mock_repos["product"].list_by_store.return_value = [p_critical, p_healthy]

    await service.generate_and_send_organization_report(org_id, frequency="weekly")

    # Assertions
    mock_repos["sales"].get_total_sales_for_org.assert_called_once_with(org_id, 7)
    _, kwargs = mock_repos["email"].send_periodic_report.call_args
    
    assert kwargs['total_sales'] == 5000.0
    assert kwargs['stockout_count'] == 1
    assert kwargs['health_score'] == 50
    assert "perte potentielle" in kwargs['strategic_insight'].lower()
    assert len(kwargs['critical_products']) == 1

@pytest.mark.asyncio
async def test_reporting_empty_organization(service, mock_repos):
    """Vérifie que le service ne plante pas pour une organisation sans produits."""
    org_id = uuid4()
    mock_repos["sales"].get_total_sales_for_org.return_value = 0.0
    mock_repos["store"].list_by_organization.return_value = []
    mock_repos["product"].list_by_store.return_value = []

    await service.generate_and_send_organization_report(org_id, frequency="daily")

    _, kwargs = mock_repos["email"].send_periodic_report.call_args
    assert kwargs['total_sales'] == 0.0
    assert kwargs['health_score'] == 100 # Par défaut si vide
    assert "sain" in kwargs['strategic_insight']

@pytest.mark.asyncio
async def test_reporting_frequency_intervals(service, mock_repos):
    """Vérifie que l'intervalle de jours change selon la fréquence."""
    org_id = uuid4()
    mock_repos["product"].list_by_store.return_value = []
    mock_repos["store"].list_by_organization.return_value = []
    
    # Test Daily
    await service.generate_and_send_organization_report(org_id, frequency="daily")
    mock_repos["sales"].get_total_sales_for_org.assert_any_call(org_id, 1)
    
    # Test Monthly
    await service.generate_and_send_organization_report(org_id, frequency="monthly")
    mock_repos["sales"].get_total_sales_for_org.assert_any_call(org_id, 30)

@pytest.mark.asyncio
async def test_reporting_all_stockouts(service, mock_repos):
    """Vérifie le score de santé et l'insight quand tout est en rupture."""
    org_id = uuid4()
    mock_repos["sales"].get_total_sales_for_org.return_value = 0.0
    mock_repos["store"].list_by_organization.return_value = [MagicMock(id=uuid4())]
    
    p1 = MagicMock(title="P1", sku="S1", current_stock=0, lead_time=5)
    mock_repos["product"].list_by_store.return_value = [p1]

    await service.generate_and_send_organization_report(org_id)

    _, kwargs = mock_repos["email"].send_periodic_report.call_args
    assert kwargs['health_score'] == 0
    assert kwargs['stockout_count'] == 1
    assert "perte potentielle" in kwargs['strategic_insight']

@pytest.mark.asyncio
async def test_reporting_date_range_format(service, mock_repos):
    """Vérifie que le format de la date est correct (ex: 23 Apr - 30 Apr)."""
    org_id = uuid4()
    mock_repos["product"].list_by_store.return_value = []
    
    await service.generate_and_send_organization_report(org_id)
    
    _, kwargs = mock_repos["email"].send_periodic_report.call_args
    date_range = kwargs['date_range']
    
    # Format attendu: "DD Mon - DD Mon"
    import re
    assert re.match(r"\d{2} \w{3} - \d{2} \w{3}", date_range)
