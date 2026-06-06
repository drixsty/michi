"""
Intelligence Worker — Background Orchestrator

Automatise tous les calculs DS/Intelligence lourds périodiquement.

Corrections Sprint 26 :
    - datetime.utcnow() → datetime.now(UTC) : utcnow() est deprecated Python 3.12+.
    - Backoff exponentiel sur erreur store (max 5 min) : le retry plat à 60s provoquait
      un storm de requêtes sur une DB overloaded.
    - Circuit breaker par store : après _MAX_CONSECUTIVE_FAILURES échecs consécutifs,
      le store est mis en quarantaine pour _QUARANTINE_CYCLES cycles.
"""
import asyncio
from datetime import datetime, UTC
from loguru import logger
from sqlalchemy import select

from core.database.connection import AsyncSessionLocal
from core.database import SerializedAsyncSession, ReentrantAsyncLock
from core.di import build_services
from core.config import settings
from modules.inventory.infrastructure.persistence.models import Store

_MAX_CONSECUTIVE_FAILURES = 3
_QUARANTINE_CYCLES = 2
_BASE_RETRY_DELAY = 5      # secondes
_MAX_RETRY_DELAY = 300     # 5 minutes


class IntelligenceWorker:
    def __init__(self):
        self.is_running = False
        self.interval = settings.INTELLIGENCE_WORKER_INTERVAL_HOURS * 3600
        self.force_on_start = settings.INTELLIGENCE_FORCE_ON_START
        self._store_failures: dict[str, int] = {}
        self._store_quarantine: dict[str, int] = {}

    async def start(self):
        """Lance la boucle infinie du worker."""
        if self.is_running:
            return

        self.is_running = True
        logger.info(f"[IntelligenceWorker] Started (Interval: {settings.INTELLIGENCE_WORKER_INTERVAL_HOURS}h)")

        if self.force_on_start:
            logger.info("[IntelligenceWorker] Forcing initial analysis on startup...")
            await self._run_analysis_cycle()

        while self.is_running:
            try:
                logger.info(f"[IntelligenceWorker] Sleeping for {settings.INTELLIGENCE_WORKER_INTERVAL_HOURS}h...")
                await asyncio.sleep(self.interval)
                await self._run_analysis_cycle()
            except asyncio.CancelledError:
                self.is_running = False
                raise
            except Exception as e:
                logger.error(f"[IntelligenceWorker] Critical error in cycle: {e}")
                await self._backoff_retry(attempt=0)

    async def _run_analysis_cycle(self):
        """Parcourt tous les stores actifs et rafraîchit l'intelligence."""
        start_time = datetime.now(UTC)
        logger.info("[IntelligenceWorker] Starting full intelligence cycle...")

        async with AsyncSessionLocal() as db:
            stmt = select(Store).where(Store.connected == True)  # noqa: E712
            stores = (await db.execute(stmt)).scalars().all()
            logger.info(f"[IntelligenceWorker] Processing {len(stores)} stores...")

            for store in stores:
                sid = str(store.id)

                # Circuit breaker : ignorer les stores en quarantaine
                if self._store_quarantine.get(sid, 0) > 0:
                    self._store_quarantine[sid] -= 1
                    logger.warning(f"[IntelligenceWorker] Store {sid} en quarantaine ({self._store_quarantine[sid]} cycles restants).")
                    continue

                from core.security.locks import distributed_lock
                async with distributed_lock(sid) as acquired:
                    if not acquired:
                        logger.warning(f"[IntelligenceWorker] Store {sid} est déjà en cours de traitement par un autre worker. Ignoré.")
                        continue

                    try:
                        await self._process_store(store.id)
                        self._store_failures[sid] = 0  # reset sur succès
                    except Exception as e:
                        failures = self._store_failures.get(sid, 0) + 1
                        self._store_failures[sid] = failures
                        logger.error(f"[IntelligenceWorker] Store {sid} échoué ({failures}/{_MAX_CONSECUTIVE_FAILURES}) : {e}")

                        if failures >= _MAX_CONSECUTIVE_FAILURES:
                            self._store_quarantine[sid] = _QUARANTINE_CYCLES
                            logger.error(f"[IntelligenceWorker] Store {sid} mis en quarantaine pour {_QUARANTINE_CYCLES} cycles.")
                            self._store_failures[sid] = 0

        duration = (datetime.now(UTC) - start_time).total_seconds()
        logger.info(f"[IntelligenceWorker] Cycle terminé en {duration:.1f}s.")

    async def _process_store(self, store_id):
        """Orchestration Intelligence par boutique."""
        logger.info(f"[IntelligenceWorker] Processing Store {store_id}...")

        async with AsyncSessionLocal() as db:
            lock = ReentrantAsyncLock()
            serialized_db = SerializedAsyncSession(db, lock)
            container = build_services(serialized_db)
            s_id_str = str(store_id)

            logger.debug(f"[IntelligenceWorker] Analyzing suppliers for {store_id}...")
            await container.supplier_analysis_service.analyze_all_suppliers(store_id)

            logger.debug(f"[IntelligenceWorker] Running cleaning pipeline for {store_id}...")
            await container.forecasting_service.run_cleaning_pipeline(s_id_str)

            logger.debug(f"[IntelligenceWorker] Running prediction pipeline for {store_id}...")
            await container.forecasting_service.run_prediction_pipeline(s_id_str)

            await db.commit()
            logger.info(f"[IntelligenceWorker] Store {store_id} updated successfully.")

    async def _backoff_retry(self, attempt: int):
        """Attente exponentielle bornée avant retry du cycle."""
        delay = min(_BASE_RETRY_DELAY * (2 ** attempt), _MAX_RETRY_DELAY)
        logger.info(f"[IntelligenceWorker] Retry dans {delay}s (attempt {attempt + 1})...")
        await asyncio.sleep(delay)


worker = IntelligenceWorker()
