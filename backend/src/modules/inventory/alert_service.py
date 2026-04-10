from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from loguru import logger
from datetime import datetime, date, timedelta
import uuid

from .models import Product, Alert, PlatformSource, SourceConnection
from src.modules.forecasting.models import Prediction

class AlertService:
    """
    Service d'évaluation des risques de stock et génération d'alertes Michi.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_for_stockouts(self, shop_id: str) -> List[Alert]:
        """
        Analyse tous les produits d'un shop et génère des alertes + emails (US 10.4).
        Logic: Stock < (RunRate * LeadTime) + SafetyBuffer
        """
        from .email_service import EmailService
        from .models import AlertEmail
        from src.modules.auth.models import User
        
        logger.info(f"[AlertService] Running stockout check for shop {shop_id}")
        s_uuid = uuid.UUID(str(shop_id))
        today = date.today()

        # 1. Charger les produits avec leurs prédictions (Run Rate, Stockout Date)
        stmt = (
            select(Product, Prediction)
            .join(Prediction, Product.id == Prediction.product_id)
            .where(Product.shop_id == s_uuid)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        # 2. Chercher l'email du propriétaire du shop pour les notifications
        user_stmt = select(User).where(User.shop_id == s_uuid).limit(1)
        user_res = await self.db.execute(user_stmt)
        shop_owner = user_res.scalars().first()
        recipient_email = shop_owner.email if shop_owner else None

        new_alerts = []
        email_service = EmailService()

        for product, prediction in rows:
            stockout_date = prediction.predicted_stockout_date
            if not stockout_date:
                continue

            days_until_stockout = (stockout_date - today).days
            lead_time = product.lead_time
            
            # --- Logique Alertes UI ---
            alert_type = None
            message = ""
            severity = 0

            if days_until_stockout < 0:
                alert_type = "STOCKOUT_CRITICAL"
                message = f"DANGER : Le produit {product.sku} est en rupture de stock."
                severity = 3
            elif days_until_stockout <= lead_time:
                alert_type = "STOCKOUT_RISK_HIGH"
                message = f"ALERTE : Rupture inévitable pour {product.sku} dans {days_until_stockout} jours (Délai réappro: {lead_time}j)."
                severity = 3
            elif days_until_stockout <= (lead_time + 7):
                alert_type = "STOCKOUT_WARNING"
                message = f"ATTENTION : Commandez {product.sku} bientôt (Rupture dans {days_until_stockout}j)."
                severity = 2

            if alert_type:
                # Éviter les doublons d'alertes UI non lues
                existing_alert = await self.db.execute(
                    select(Alert).where(Alert.product_id == product.id, Alert.type == alert_type, Alert.is_read == False)
                )
                if not existing_alert.scalars().first():
                    new_alert = Alert(product_id=product.id, type=alert_type, message=message, severity=severity)
                    new_alerts.append(new_alert)

            # --- Logique Alertes Email (US 10.4) ---
            # On envoie un email si rupture <= lead_time + 2 jours
            if recipient_email and days_until_stockout <= (lead_time + 2):
                # Anti-spam : Vérifier si un email a été envoyé pour ce produit dans les dernières 24h
                since_yesterday = datetime.utcnow() - timedelta(hours=24)
                email_check_stmt = select(AlertEmail).where(
                    AlertEmail.product_id == product.id,
                    AlertEmail.sent_at >= since_yesterday
                )
                existing_email = await self.db.execute(email_check_stmt)
                
                if not existing_email.scalars().first():
                    success = await email_service.send_stockout_warning(
                        to_email=recipient_email,
                        product_title=product.title,
                        days_left=days_until_stockout
                    )
                    if success:
                        new_log = AlertEmail(product_id=product.id)
                        self.db.add(new_log)

        if new_alerts:
            self.db.add_all(new_alerts)
            
        await self.db.flush()
        return new_alerts

    async def get_unread_alerts(self, shop_id: str) -> List[Alert]:
        """
        Récupère les alertes non lues pour l'affichage UI.
        """
        s_uuid = uuid.UUID(str(shop_id))
        # Isolation Sprint 18 : Ne prendre que les alertes des sources connectées
        active_conn_stmt = select(SourceConnection.platform).where(
            SourceConnection.shop_id == s_uuid,
            SourceConnection.connected == True
        )
        active_platforms = (await self.db.execute(active_conn_stmt)).scalars().all()
        
        if not active_platforms:
            return []

        result = await self.db.execute(
            select(Alert)
            .join(Product)
            .where(
                Product.shop_id == s_uuid, 
                Alert.is_read == False,
                Product.source_platform.in_(active_platforms)
            )
            .order_by(Alert.severity.desc(), Alert.created_at.desc())
        )
        return list(result.scalars().all())
