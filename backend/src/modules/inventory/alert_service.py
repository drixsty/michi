from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from loguru import logger
from datetime import date, timedelta
import uuid

from .models import Product, Alert, PlatformSource
from src.modules.forecasting.models import Prediction

class AlertService:
    """
    Service d'évaluation des risques de stock et génération d'alertes Michi.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_for_stockouts(self, shop_id: str) -> List[Alert]:
        """
        Analyse tous les produits d'un shop et génère des alertes si nécessaire.
        Logic: Stock < (RunRate * LeadTime) + SafetyBuffer
        """
        logger.info(f"[AlertService] Running stockout check for shop {shop_id}")
        s_uuid = uuid.UUID(str(shop_id))

        # 1. Charger les produits avec leurs prédictions (Run Rate, Stockout Date)
        stmt = (
            select(Product, Prediction)
            .join(Prediction, Product.id == Prediction.product_id)
            .where(Product.shop_id == s_uuid)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        new_alerts = []
        for product, prediction in rows:
            # 2. Évaluer le risque
            # Un risque est critique si la date de rupture est AVANT la réception d'une commande passée aujourd'hui.
            # Délai de réception = lead_time
            today = date.today()
            stockout_date = prediction.predicted_stockout_date
            
            if not stockout_date:
                continue

            days_until_stockout = (stockout_date - today).days
            lead_time = product.lead_time
            
            # Message d'alerte spécifique
            if days_until_stockout < 0:
                # DÉJÀ EN RUPTURE
                alert_type = "STOCKOUT_CRITICAL"
                message = f"DANGER : Le produit {product.sku} est en rupture de stock."
                severity = 3
            elif days_until_stockout <= lead_time:
                # RISQUE IMMINENT (Impossible d'éviter la rupture même en commandant aujourd'hui)
                alert_type = "STOCKOUT_RISK_HIGH"
                message = f"ALERTE : Rupture inévitable pour {product.sku} dans {days_until_stockout} jours (Délai réappro: {lead_time}j)."
                severity = 3
            elif days_until_stockout <= (lead_time + 7):
                # ATTENTION (Il reste peu de temps pour commander)
                alert_type = "STOCKOUT_WARNING"
                message = f"ATTENTION : Commandez {product.sku} bientôt (Rupture dans {days_until_stockout}j)."
                severity = 2
            else:
                # Tout va bien
                continue

            # 3. Éviter les alertes en double pour le même produit
            existing_alert = await self.db.execute(
                select(Alert).where(Alert.product_id == product.id, Alert.type == alert_type, Alert.is_read == False)
            )
            if existing_alert.scalars().first():
                continue

            # 4. Créer l'alerte
            new_alert = Alert(
                product_id=product.id,
                type=alert_type,
                message=message,
                severity=severity
            )
            new_alerts.append(new_alert)

        if new_alerts:
            self.db.add_all(new_alerts)
            await self.db.flush()
            logger.info(f"[AlertService] {len(new_alerts)} new alerts generated.")

        return new_alerts

    async def get_unread_alerts(self, shop_id: str) -> List[Alert]:
        """
        Récupère les alertes non lues pour l'affichage UI.
        """
        s_uuid = uuid.UUID(str(shop_id))
        result = await self.db.execute(
            select(Alert)
            .join(Product)
            .where(Product.shop_id == s_uuid, Alert.is_read == False)
            .order_by(Alert.severity.desc(), Alert.created_at.desc())
        )
        return list(result.scalars().all())
