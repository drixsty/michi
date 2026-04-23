"""
CronWorker — Application Layer
Background task runner for scheduled jobs.
"""
import asyncio
from loguru import logger
from core.config import settings
from core.infrastructure.cron_jobs import run_periodic_reports

class CronWorker:
    def __init__(self):
        self.is_running = False

    async def start(self):
        """
        Boucle infinie vérifiant les tâches périodiques chaque heure.
        """
        if not settings.CRON_REPORTING_ENABLED:
            logger.info("[CronWorker] Disabled by config.")
            return

        self.is_running = True
        logger.info("[CronWorker] Started successfully.")

        while self.is_running:
            try:
                # Vérification toutes les heures
                now = asyncio.get_event_loop().time()
                
                # Exécution du job
                await run_periodic_reports()
                
                # Attendre 1 heure (3600 secondes)
                # Note: Dans un environnement de test, on pourrait réduire cet intervalle
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"[CronWorker] Error in loop: {str(e)}")
                await asyncio.sleep(60) # Attendre 1 min avant de réessayer en cas d'erreur

    def stop(self):
        self.is_running = False

worker = CronWorker()
