"""
ReportingService — Application Layer
Orchestrates data aggregation for periodic reports.
"""
from typing import List, Dict, Any, Optional
from loguru import logger
import uuid
from uuid import UUID
from datetime import datetime, UTC, timedelta

from modules.inventory.domain.ports import IProductRepository, ISalesLogRepository, IStoreRepository, IAlertRepository
from modules.inventory.application.email_service import EmailService

class ReportingService:
    def __init__(
        self,
        product_repo: IProductRepository,
        sales_log_repo: ISalesLogRepository,
        store_repo: IStoreRepository,
        alert_repo: IAlertRepository,
        email_service: EmailService
    ):
        self.product_repo = product_repo
        self.sales_log_repo = sales_log_repo
        self.store_repo = store_repo
        self.alert_repo = alert_repo
        self.email_service = email_service

    async def generate_and_send_organization_report(self, org_id: UUID, frequency: str = "weekly"):
        """
        Génère les KPIs réels et envoie le rapport par email.
        """
        logger.info(f"[ReportingService] Generating {frequency} report for organization {org_id}")
        
        # 1. Déterminer la période
        days = 7
        if frequency == "daily": days = 1
        elif frequency == "monthly": days = 30

        today = datetime.now(UTC)
        since_date = today - timedelta(days=days)
        date_range = f"{since_date.strftime('%d %b')} - {today.strftime('%d %b')}"

        # 2. Récupérer les ventes réelles
        total_sales_units = await self.sales_log_repo.get_total_sales_for_org(org_id, days)
        
        # 3. Récupérer les produits critiques
        stores = await self.store_repo.list_by_organization(org_id, connected_only=True)
        store_ids = [s.id for s in stores]
        
        all_products = await self.product_repo.list_by_store(store_ids)
        critical_products = []
        stockout_count = 0
        
        for p in all_products:
            if p.current_stock <= 0:
                stockout_count += 1
            
            # Logic de statut visuel
            color = "#0f172a"
            stock_label = f"{p.current_stock} en stock"
            
            if p.current_stock == 0:
                color = "#ef4444" # Red
                stock_label = "EN RUPTURE"
            elif p.current_stock <= p.lead_time:
                color = "#f59e0b" # Orange
                stock_label = "STOCK FAIBLE"

            if p.current_stock <= p.lead_time:
                critical_products.append({
                    "title": p.title,
                    "sku": p.sku,
                    "days_left": max(0, p.current_stock), # Run rate simulation
                    "color": color,
                    "stock_label": stock_label
                })

        # 4. Calculer le score de santé et Insight IA
        health_score = 100
        if all_products and len(all_products) > 0:
            health_score = int(((len(all_products) - stockout_count) / len(all_products)) * 100)

        strategic_insight = "Votre stock est sain sur l'ensemble de vos catalogues."
        if stockout_count > 0:
            potential_loss = stockout_count * 125 # Mock estimation
            strategic_insight = f"Vous avez {stockout_count} produits en rupture. Michi estime une perte potentielle de CA de {potential_loss}€ sur la période."

        # 5. Récupérer le nom de l'organisation
        organization_name = "Ma Boutique Michi" # To be fetched from OrgService
        recipient_email = "admin@michi.app"

        # 6. Envoyer le mail
        await self.email_service.send_periodic_report(
            to_email=recipient_email,
            organization_name=organization_name,
            frequency=frequency,
            total_sales=total_sales_units,
            stockout_count=stockout_count,
            health_score=health_score,
            critical_products=critical_products[:5],
            date_range=date_range,
            strategic_insight=strategic_insight
        )
        
        logger.success(f"[ReportingService] {frequency.capitalize()} report sent for {org_id}")
