"""
Intelligence Worker — Background Orchestrator
Automates all heavy DS/Intelligence calculations periodically.
"""
import asyncio
from datetime import datetime
from loguru import logger
from sqlalchemy import select

from core.database.connection import AsyncSessionLocal
from core.database import SerializedAsyncSession, ReentrantAsyncLock
from core.di import build_services
from core.config import settings
from modules.inventory.infrastructure.persistence.models import Store

class IntelligenceWorker:
    def __init__(self):
        self.is_running = False
        self.interval = settings.INTELLIGENCE_WORKER_INTERVAL_HOURS * 3600
        self.force_on_start = settings.INTELLIGENCE_FORCE_ON_START

    async def start(self):
        """Lance la boucle infinie du worker."""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info(f"[IntelligenceWorker] Started (Interval: {settings.INTELLIGENCE_WORKER_INTERVAL_HOURS}h)")
        
        # Premier passage immédiat si configuré
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
            except Exception as e:
                logger.error(f"[IntelligenceWorker] Error in cycle: {e}")
                await asyncio.sleep(60) # Éviter le spam en cas d'erreur critique

    async def _run_analysis_cycle(self):
        """Parcourt tous les stores et rafraîchit l'intelligence."""
        start_time = datetime.utcnow()
        logger.info("[IntelligenceWorker] Starting full intelligence cycle...")
        
        async with AsyncSessionLocal() as db:
            # Récupérer toutes les boutiques actives/connectées
            stmt = select(Store).where(Store.connected == True)
            result = await db.execute(stmt)
            stores = result.scalars().all()
            
            logger.info(f"[IntelligenceWorker] Processing {len(stores)} stores...")
            
            for store in stores:
                try:
                    await self._process_store(store.id)
                except Exception as e:
                    logger.error(f"[IntelligenceWorker] Failed to process store {store.id}: {e}")
                    continue
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"[IntelligenceWorker] Cycle finished in {duration:.1f}s.")

    async def _process_store(self, store_id):
        """Orchestration Intelligence par boutique."""
        logger.info(f"[IntelligenceWorker] Processing Store {store_id}...")
        
        # On utilise une session dédiée et isolée par store pour éviter les sessions trop longues
        async with AsyncSessionLocal() as db:
            # Sérialisation indispensable pour la concurrence des services si nécessaire
            lock = ReentrantAsyncLock()
            serialized_db = SerializedAsyncSession(db, lock)
            
            # Rebuild DI container for this session
            container = build_services(serialized_db)
            
            s_id_str = str(store_id)
            
            # 1. Analyse Performance Fournisseur (Dual-Sigma)
            logger.debug(f"[IntelligenceWorker] Analyzing suppliers for {store_id}...")
            await container.supplier_analysis_service.analyze_all_suppliers(store_id)
            
            # 2. Pipeline de nettoyage (OOS + Outliers)
            logger.debug(f"[IntelligenceWorker] Running cleaning pipeline for {store_id}...")
            await container.forecasting_service.run_cleaning_pipeline(s_id_str)
            
            # 3. Pipeline de prédiction (Run Rate + Stockout Date + ABC Ranks)
            logger.debug(f"[IntelligenceWorker] Running prediction pipeline for {store_id}...")
            await container.forecasting_service.run_prediction_pipeline(s_id_str)
            
            # Commit final pour cette boutique
            await db.commit()
            logger.info(f"[IntelligenceWorker] Store {store_id} updated successfully.")

# Instance unique accessible par lifespan
worker = IntelligenceWorker()
