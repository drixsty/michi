from core.database.models import Organization, User, OrganizationMember
import pandas as pd
"""
ForecastingService — Application Layer
Pipeline de nettoyage + prédictions opérationnelles (Agnostique Michi).
"""
from datetime import date, datetime
from typing import Optional, List, Dict
import uuid
from loguru import logger

from modules.forecasting.domain.entities import CleanedDemandEntity, PredictionEntity
from modules.forecasting.domain.ports import ICleanedDemandRepository, IPredictionRepository
from modules.inventory.domain.ports import IProductRepository, ISalesLogRepository, IStoreRepository, ISupplierRepository

from modules.forecasting.domain.schemas import PipelineResultSchema, PredictionRunResultSchema, DashboardKPISchema
from modules.intelligence.algorithms import (
    correct_out_of_stock_batch,
    detect_outliers_batch,
    calculate_run_rate_batch,
    predict_stockout_date,
    calculate_reorder_quantity,
    calculate_abc_ranks_batch,
    detect_seasonality_factor,
)

class ForecastingService:
    def __init__(
        self, 
        cleaned_demand_repo: ICleanedDemandRepository,
        prediction_repo: IPredictionRepository,
        product_repo: IProductRepository,
        sales_log_repo: ISalesLogRepository,
        store_repo: IStoreRepository,
        supplier_repo: ISupplierRepository
    ):
        self.cleaned_demand_repo = cleaned_demand_repo
        self.prediction_repo = prediction_repo
        self.product_repo = product_repo
        self.sales_log_repo = sales_log_repo
        self.store_repo = store_repo
        self.supplier_repo = supplier_repo

    async def run_cleaning_pipeline(self, store_id: str) -> PipelineResultSchema:
        """
        Exécute la pipeline de nettoyage OOS + IQR (DDD version).
        """
        logger.info(f"[ForecastingService] Pipeline start — store {store_id}")
        s_uuid = uuid.UUID(store_id)

        # 1. Charger les produits du store
        products = await self.product_repo.list_by_store([s_uuid])
        if not products:
            return PipelineResultSchema(
                success=False, 
                products_processed=0, 
                rows_written=0, 
                stockout_corrections=0,
                outlier_corrections=0,
                message="Aucun produit trouvé."
            )

        product_ids = [p.id for p in products]

        # 2. Charger les sales_logs
        # Note: In real app, we might want a list_by_products in ISalesLogRepository
        # Let's assume list_by_product 90d is enough or we use a more generic search.
        # For now, we'll fetch logs for each product or optimize repository.
        all_logs = []
        for pid in product_ids:
            logs = await self.sales_log_repo.list_by_product(pid)
            all_logs.extend(logs)

        if not all_logs:
            return PipelineResultSchema(
                success=False, 
                products_processed=0, 
                rows_written=0, 
                stockout_corrections=0,
                outlier_corrections=0,
                message="Aucun historique trouvé."
            )

        # 3. DataFrame processing (Keep Pandas logic in application layer for volume handling)
        df = pd.DataFrame([{
            "product_id": str(log.product_id),
            "date": log.date,
            "units_sold": float(log.units_sold),
            "end_of_day_stock": int(log.end_of_day_stock),
        } for log in all_logs])

        df = correct_out_of_stock_batch(df)
        df = detect_outliers_batch(df)

        def _correction_type(row) -> str:
            if row["is_stockout"] and row["is_outlier"]: return "stockout+outlier"
            if row["is_stockout"]: return "stockout"
            if row["is_outlier"]: return "outlier"
            return "none"

        df["correction_type"] = df.apply(_correction_type, axis=1)

        # 4. Clean old and save new
        await self.cleaned_demand_repo.delete_by_products(product_ids)
        
        entities = [
            CleanedDemandEntity(
                id=uuid.uuid4(),
                product_id=uuid.UUID(row["product_id"]),
                date=row["date"],
                raw_units_sold=float(row["units_sold"]),
                corrected_units_sold=float(row["corrected_units_sold"]),
                inventory_level=int(row["end_of_day_stock"]),
                is_stockout=bool(row["is_stockout"]),
                is_outlier=bool(row["is_outlier"]),
                correction_type=str(row["correction_type"]),
                computed_at=datetime.utcnow()
            ) for _, row in df.iterrows()
        ]

        await self.cleaned_demand_repo.save_batch(entities)

        return PipelineResultSchema(
            success=True,
            products_processed=len(products),
            rows_written=len(entities),
            stockout_corrections=int(df["is_stockout"].sum()),
            outlier_corrections=int(df["is_outlier"].sum()),
            message="Pipeline de nettoyage terminée."
        )

    async def run_prediction_pipeline(self, store_id: str) -> PredictionRunResultSchema:
        """
        Calcule le run rate + prédictions (DDD version).
        """
        logger.info(f"[ForecastingService] Prediction pipeline start — store {store_id}")
        s_uuid = uuid.UUID(store_id)

        # 1. Charger les produits
        products = await self.product_repo.list_by_store([s_uuid])
        if not products:
            return PredictionRunResultSchema(success=False, products_processed=0, message="Aucun produit.")

        product_ids = [p.id for p in products]
        product_map = {str(p.id): p for p in products}

        # 2. Charger cleaned demand
        all_demand = []
        for pid in product_ids:
            d = await self.cleaned_demand_repo.list_by_product(pid)
            all_demand.extend(d)

        if not all_demand:
            return PredictionRunResultSchema(success=False, products_processed=0, message="Nettoyez d'abord.")

        # 3. Charger les fournisseurs pour le store
        suppliers = await self.supplier_repo.list_by_store(s_uuid)
        supplier_map = {s.id: s for s in suppliers}

        # 4. Logic algorithms
        df = pd.DataFrame([{
            "product_id": str(d.product_id),
            "date": d.date,
            "corrected_units_sold": float(d.corrected_units_sold),
            "is_stockout": bool(d.is_stockout),
            "is_outlier": bool(d.is_outlier),
        } for d in all_demand])

        df = calculate_run_rate_batch(df)
        latest = df.sort_values("date").groupby("product_id").last().reset_index()
        
        latest['sale_price'] = latest['product_id'].map(lambda pid: product_map.get(pid).sale_price if product_map.get(pid) else 0)
        latest['cost_price'] = latest['product_id'].map(lambda pid: product_map.get(pid).cost_price if product_map.get(pid) else 0)
        latest = calculate_abc_ranks_batch(latest)

        # 5. Save predictions
        await self.prediction_repo.delete_by_products(product_ids)
        
        today = date.today()
        prediction_entities = []
        for _, row in latest.iterrows():
            pid_str = str(row["product_id"])
            p = product_map.get(pid_str)
            if not p: continue

            run_rate = float(row["run_rate"]) * (float(p.boost_factor) if p.boost_factor else 1.0)
            sigma = float(row["demand_sigma"]) if "demand_sigma" in row else 0.0
            
            # Récupérer les données de performance du fournisseur associé
            supplier_data = supplier_map.get(p.supplier_id) if p.supplier_id else None
            avg_delay = supplier_data.average_delay_days if supplier_data else 0.0
            lt_sigma = supplier_data.lead_time_sigma if supplier_data else 0.0

            stockout_date = predict_stockout_date(
                current_stock=float(p.current_stock),
                run_rate=run_rate,
                reference_date=today
            )
            
            reorder_qty = calculate_reorder_quantity(
                run_rate=run_rate,
                lead_time=int(p.lead_time),
                moq=int(p.moq),
                current_stock=float(p.current_stock),
                sigma=sigma,
                service_level=0.95,
                average_delay=avg_delay,
                lead_time_sigma=lt_sigma
            )

            prediction_entities.append(PredictionEntity(
                id=uuid.uuid4(),
                product_id=p.id,
                run_rate=run_rate,
                days_of_stock=float(p.current_stock) / run_rate if run_rate > 0 else None,
                predicted_stockout_date=stockout_date,
                reorder_quantity=reorder_qty,
                current_stock_snapshot=float(p.current_stock),
                lead_time_snapshot=int(p.lead_time),
                moq_snapshot=int(p.moq),
                mape_score=None,
                abc_rank=row["abc_rank"],
                annual_gross_profit=row["annual_gross_profit"],
                demand_sigma=sigma,
                computed_at=datetime.utcnow()
            ))

        for pe in prediction_entities:
            await self.prediction_repo.save(pe)

        return PredictionRunResultSchema(
            success=True,
            products_processed=len(prediction_entities),
            message=f"Prédictions calculées pour {len(prediction_entities)} produits."
        )

    async def get_predictions(self, org_id: Optional[str] = None, store_id: Optional[str] = None) -> List[PredictionEntity]:
        """Récupère les prédictions filtrées par Store ou Organisation."""
        if store_id:
            return await self.prediction_repo.list_by_store(uuid.UUID(store_id))
        elif org_id:
            return await self.prediction_repo.list_by_organization(uuid.UUID(org_id))
        return []

    async def get_dashboard_kpis(self, store_id: Optional[str] = None, organization_id: Optional[str] = None) -> DashboardKPISchema:
        """Retourne les KPIs agrégés pour le dashboard (store ou organisation)."""
        if store_id:
            predictions = await self.prediction_repo.list_by_store(uuid.UUID(store_id))
        elif organization_id:
            predictions = await self.prediction_repo.list_by_organization(uuid.UUID(organization_id))
        else:
            predictions = []

        total = len(predictions)
        stockouts = sum(1 for p in predictions if getattr(p, "days_of_stock", 999) == 0)
        urgent = sum(1 for p in predictions if 0 < getattr(p, "days_of_stock", 999) <= 7)
        predicted_30d = sum(1 for p in predictions if 0 < getattr(p, "days_of_stock", 999) <= 30)

        return DashboardKPISchema(
            total_products=total,
            actual_stockouts=stockouts,
            urgent_alerts=urgent,
            predicted_stockouts_30d=predicted_30d,
            message=f"{total} produits analysés",
        )
