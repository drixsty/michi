"""
Cron Jobs — Infrastructure Layer
Entry point for scheduled tasks (Hexagonal Inbound Adapter).
"""
import asyncio
from datetime import datetime
from loguru import logger
from sqlalchemy import select

from core.database.connection import AsyncSessionLocal
from core.database.models import Organization
from core.config import settings
from modules.inventory.application.reporting_service import ReportingService
from modules.inventory.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
from modules.inventory.infrastructure.repositories.sales_log_repository import SQLAlchemySalesLogRepository
from modules.inventory.infrastructure.repositories.store_repository import SQLAlchemyStoreRepository
from modules.inventory.infrastructure.repositories.alert_repository import SQLAlchemyAlertRepository
from modules.inventory.application.email_service import EmailService

async def run_periodic_reports():
    """
    Tâche planifiée pour envoyer les rapports par email aux organisations éligibles.
    """
    if not settings.CRON_REPORTING_ENABLED:
        logger.info("[Cron] Reporting disabled by configuration.")
        return

    logger.info(f"[Cron] Starting periodic reporting job at {datetime.utcnow()}")
    
    async with AsyncSessionLocal() as session:
        # 1. Récupérer toutes les organisations actives
        stmt = select(Organization)
        result = await session.execute(stmt)
        organizations = result.scalars().all()

        # 2. Initialiser le service (Composition manuelle car hors DI FastAPI ici)
        # Note: Dans une version plus avancée, on utiliserait un container de dépendances
        product_repo = SQLAlchemyProductRepository(session)
        sales_repo = SQLAlchemySalesLogRepository(session)
        store_repo = SQLAlchemyStoreRepository(session)
        alert_repo = SQLAlchemyAlertRepository(session)
        email_service = EmailService()
        
        reporting_service = ReportingService(
            product_repo=product_repo,
            sales_log_repo=sales_repo,
            store_repo=store_repo,
            alert_repo=alert_repo,
            email_service=email_service
        )

        # 3. Parcourir et filtrer selon les réglages
        for org in organizations:
            org_settings = org.settings or {}
            
            # Vérifier si activé pour cette org
            if not org_settings.get("report_enabled", False):
                continue
                
            frequency = org_settings.get("report_frequency", "weekly")
            
            # Logique simplifiée pour décider si on envoie AUJOURD'HUI
            # Dans un vrai système, on comparerait last_report_at
            should_send = False
            today = datetime.utcnow()
            
            if frequency == "daily":
                should_send = True # Tous les jours
            elif frequency == "weekly" and today.weekday() == 0: # Lundi
                should_send = True
            elif frequency == "monthly" and today.day == 1: # 1er du mois
                should_send = True
                
            if should_send:
                try:
                    await reporting_service.generate_and_send_organization_report(org.id, frequency)
                except Exception as e:
                    logger.error(f"[Cron] Failed to send report for org {org.id}: {str(e)}")

    logger.info("[Cron] Periodic reporting job finished.")

if __name__ == "__main__":
    # Permet de lancer manuellement : python -m core.infrastructure.cron_jobs
    asyncio.run(run_periodic_reports())
