from core.database.models import Organization, User, OrganizationMember
"""
AlertService — Application Layer
Coordinates stockout checks and alert generation.
"""
from typing import List, Optional
from loguru import logger
from datetime import datetime, date, timedelta, timezone
from uuid import UUID
import uuid

from modules.inventory.domain.entities import AlertEntity
from modules.inventory.domain.ports import IAlertRepository, IProductRepository, IStoreRepository
from modules.auth.domain.ports import IMembershipRepository, IUserRepository
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
        membership_repo: IMembershipRepository,
        user_repo: IUserRepository,
        email_service: EmailService
    ):
        self.alert_repo = alert_repo
        self.product_repo = product_repo
        self.store_repo = store_repo
        self.membership_repo = membership_repo
        self.user_repo = user_repo
        self.email_service = email_service

    async def check_for_stockouts(self, store_id: str) -> List[AlertEntity]:
        """
        Analyse tous les produits d'un store et génère des alertes + emails.
        """
        logger.info(f"[AlertService] Running stockout check for store {store_id}")
        s_uuid = UUID(store_id)
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
        
        # 2. Chercher les destinataires (Admins/Owner de l'org du store)
        store = await self.store_repo.get_by_id(s_uuid)
        if not store:
            return []

        # Recipient lookup logic (Fetch organization members)
        memberships = await self.membership_repo.list_for_org(store.organization_id)
        # Filter for ADMIN or OWNER (simplified: anyone with a role for now, but should be filtered)
        recipients = []
        for m in memberships:
            user = await self.user_repo.get_by_id(m.user_id)
            if user:
                recipients.append(str(user.email))
        
        if not recipients:
            logger.warning(f"[AlertService] No recipients found for organization {store.organization_id}")
            recipients = ["admin@michi.app"] # Fallback

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
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None)
                )
                await self.alert_repo.save(alert)
                new_alerts.append(alert)
                
                for email in recipients:
                    try:
                        await self.email_service.send_stockout_warning(
                            email,
                            product.title,
                            product.lead_time
                        )
                    except Exception as e:
                        logger.warning(f"[AlertService] Email send failed to {email}: {e}")
        
        return new_alerts

    async def get_unread_alerts(
        self, 
        store_id: Optional[str] = None, 
        organization_id: Optional[str] = None
    ) -> List[AlertEntity]:
        """
        Récupère les alertes non lues pour l'affichage UI.
        """
        s_uuid = UUID(store_id) if store_id else None
        o_uuid = UUID(organization_id) if organization_id else None
        
        if s_uuid:
            store = await self.store_repo.get_by_id(s_uuid)
            if not store or not store.connected:
                return []
            return await self.alert_repo.list_unread(store_id=s_uuid)
        elif o_uuid:
            return await self.alert_repo.list_unread(org_id=o_uuid)
        
        return []
