from core.database.models import Organization, User, OrganizationMember
"""
AlertService — Application Layer
Coordinates stockout checks and alert generation.
"""
from typing import List, Optional
from loguru import logger
from datetime import datetime, date, timedelta
from uuid import UUID
import uuid

from modules.inventory.domain.entities import AlertEntity
from modules.inventory.domain.ports import IAlertRepository, IProductRepository, IStoreRepository
from modules.inventory.application.email_service import EmailService

class AlertService:
    """
    Service d'évaluation des risques de stock et génération d'alertes Michi.
    """
    def __init__(
        self, 
        alert_repo: IAlertRepository, 
        product_repo: IProductRepository,
        store_repo: IStoreRepository,
        email_service: EmailService
    ):
        self.alert_repo = alert_repo
        self.product_repo = product_repo
        self.store_repo = store_repo
        self.email_service = email_service

    async def check_for_stockouts(self, store_id: str) -> List[AlertEntity]:
        """
        Analyse tous les produits d'un store et génère des alertes + emails.
        """
        logger.info(f"[AlertService] Running stockout check for store {store_id}")
        s_uuid = UUID(str(store_id))
        today = date.today()

        # NOTE: Current implementation of AlertService heavily relies on joins with Prediction model.
        # Until Forecasting is refactored, we might still need some SQL-like logic or 
        # a specialized method in Republication.
        # For US 21.10, I'll keep it simple by using repositories where possible.
        
        # 1. Charger les produits du store
        products = await self.product_repo.list_by_store([s_uuid])
        
        # Pour les prédictions, on va tricher un peu en attendant US 21.11 
        # en utilisant une query directe (ou on ajoute un port temporaire).
        # On va utiliser le produit directement s'il a déjà les infos (via selectinload dans repo).
        
        # 2. Chercher les destinataires (Admins de l'org du store)
        # TODO: Move this to OrgService / OrgRepository
        store = await self.store_repo.get_by_id(s_uuid)
        if not store:
            return []

        # Recipient lookup logic (Simplified for Hexagonal transition)
        # In a real DDD, we'd inject an IOrgService or IUserRepository
        recipient_email = "admin@michi.app" # Mock or specialized lookup
        new_alerts = []

        for product in products:
            if product.current_stock <= product.lead_time:
                # Anti-spam: check if unread alert already exists
                if await self.alert_repo.exists_unread(product.id, "STOCKOUT_RISK_HIGH"):
                    continue

                from modules.inventory.domain.entities import AlertEntity
                alert = AlertEntity(
                    id=uuid.uuid4(),
                    product_id=product.id,
                    type="STOCKOUT_RISK_HIGH",
                    severity=3,
                    message=f"Rupture imminente détectée pour {product.sku}",
                    is_read=False,
                    created_at=datetime.utcnow()
                )
                await self.alert_repo.save(alert)
                new_alerts.append(alert)
                
                try:
                    await self.email_service.send_stockout_warning(
                        recipient_email,
                        product.title,
                        product.lead_time
                    )
                except Exception as e:
                    logger.warning(f"[AlertService] Email send failed (non-blocking): {e}")
        
        return new_alerts

    async def get_unread_alerts(
        self, 
        store_id: Optional[str] = None, 
        organization_id: Optional[str] = None
    ) -> List[AlertEntity]:
        """
        Récupère les alertes non lues pour l'affichage UI.
        """
        s_uuid = UUID(str(store_id)) if store_id else None
        o_uuid = UUID(str(organization_id)) if organization_id else None
        
        if s_uuid:
            store = await self.store_repo.get_by_id(s_uuid)
            if not store or not store.connected:
                return []
            return await self.alert_repo.list_unread(store_id=s_uuid)
        elif o_uuid:
            return await self.alert_repo.list_unread(org_id=o_uuid)
        
        return []
