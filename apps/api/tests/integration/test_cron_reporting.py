import pytest
from uuid import uuid4
from sqlalchemy import insert
from core.database.models import Organization
from core.infrastructure.cron_jobs import run_periodic_reports
from unittest.mock import patch, AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_cron_job_filters_organizations_correctly():
    """
    Vérifie que le job cron ne traite que les organisations ayant activé le reporting.
    """
    # 1. Setup mocks
    mock_session = AsyncMock()
    
    # Créer deux organisations : une avec reporting, une sans
    org_enabled = MagicMock()
    org_enabled.id = uuid4()
    org_enabled.settings = {"report_enabled": True, "report_frequency": "daily"}
    
    org_disabled = MagicMock()
    org_disabled.id = uuid4()
    org_disabled.settings = {"report_enabled": False}
    
    # Mocker le résultat de session.execute
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [org_enabled, org_disabled]
    mock_session.execute.return_value = mock_result

    # 2. Mocker le ReportingService
    with patch("core.infrastructure.cron_jobs.ReportingService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.generate_and_send_organization_report = AsyncMock()
        
        # Mocker AsyncSessionLocal pour retourner notre mock_session
        with patch("core.infrastructure.cron_jobs.AsyncSessionLocal") as MockSessionLocal:
            # Gérer le context manager async with
            MockSessionLocal.return_value.__aenter__.return_value = mock_session
            
            # 3. Exécuter le job
            from core.config import settings
            with patch.object(settings, "CRON_REPORTING_ENABLED", True):
                await run_periodic_reports()

            # 4. Assertions
            mock_instance.generate_and_send_organization_report.assert_called_once_with(org_enabled.id, "daily")
