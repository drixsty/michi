"""
ForecastingService — Pipeline de nettoyage + prédictions opérationnelles.

Pipeline nettoyage (US 2.4) :
    1. Lecture des sales_logs du shop (SQLAlchemy → Pandas)
    2. Out-of-Stock Correction (médiane mobile 14j)
    3. Outlier Detection & Correction (IQR)
    4. Écriture dans cleaned_demand (delete + insert par shop)

Pipeline prédictions (US 2.8) :
    1. Lecture cleaned_demand + produits
    2. Run Rate 30j par produit (US 2.5)
    3. Stockout date (US 2.6) + Reorder quantity (US 2.7)
    4. Écriture dans predictions (delete + insert par shop)
"""
from datetime import date
from typing import Optional, List

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete, func, case
from loguru import logger

from src.modules.inventory.models import Product, SalesLog, PlatformSource
from .models import CleanedDemand, Prediction
from .schemas import PipelineResultSchema, CleanedDemandSchema, PredictionRunResultSchema, DashboardKPISchema
from .algorithms.out_of_stock_correction import correct_out_of_stock_batch
from .algorithms.outlier_detection import detect_outliers_batch
from .algorithms.run_rate import calculate_run_rate_batch
from .algorithms.predictions import predict_stockout_date, calculate_reorder_quantity
from .algorithms.abc_analysis import calculate_abc_ranks_batch
from .algorithms.seasonality import detect_seasonality_factor


class ForecastingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_cleaning_pipeline(self, store_id: str) -> PipelineResultSchema:
        """
        Exécute la pipeline complète OOS + IQR pour tous les produits du store.

        Args:
            store_id: UUID du store.

        Returns:
            PipelineResultSchema avec les statistiques de nettoyage.
        """
        logger.info(f"[ForecastingService] Pipeline start — store {store_id}")

        # ── 1. Charger les produits du store ───────────────────────────────────
        products_result = await self.db.execute(
            select(Product).where(Product.store_id == store_id)
        )
        products = list(products_result.scalars().all())

        if not products:
            return PipelineResultSchema(
                success=False,
                products_processed=0,
                rows_written=0,
                stockout_corrections=0,
                outlier_corrections=0,
                message="Aucun produit trouvé. Lancez d'abord une synchronisation.",
            )

        product_ids = [p.id for p in products]

        # ── 2. Charger les sales_logs ─────────────────────────────────────────
        logs_result = await self.db.execute(
            select(SalesLog)
            .where(SalesLog.product_id.in_(product_ids))
            .order_by(SalesLog.product_id, SalesLog.date)
        )
        logs = logs_result.scalars().all()

        if not logs:
            return PipelineResultSchema(
                success=False,
                products_processed=0,
                rows_written=0,
                stockout_corrections=0,
                outlier_corrections=0,
                message="Aucun historique de ventes trouvé.",
            )

        # ── 3. Construire le DataFrame ────────────────────────────────────────
        df = pd.DataFrame([{
            "product_id": str(log.product_id),
            "date": log.date,
            "units_sold": float(log.units_sold),
            "end_of_day_stock": int(log.end_of_day_stock),
        } for log in logs])

        # ── 4. OOS Correction ─────────────────────────────────────────────────
        df = correct_out_of_stock_batch(df)

        # ── 5. Outlier Detection ──────────────────────────────────────────────
        df = detect_outliers_batch(df)

        # ── 6. Déterminer correction_type ─────────────────────────────────────
        def _correction_type(row) -> str:
            if row["is_stockout"] and row["is_outlier"]:
                return "stockout+outlier"
            if row["is_stockout"]:
                return "stockout"
            if row["is_outlier"]:
                return "outlier"
            return "none"

        df["correction_type"] = df.apply(_correction_type, axis=1)

        # ── 7. Supprimer l'ancienne cleaned_demand du shop ────────────────────
        await self.db.execute(
            delete(CleanedDemand).where(CleanedDemand.product_id.in_(product_ids))
        )
        await self.db.flush()

        # ── 8. Insérer les nouvelles lignes ───────────────────────────────────
        rows = []
        for _, row in df.iterrows():
            rows.append(CleanedDemand(
                product_id=row["product_id"],
                date=row["date"],
                raw_units_sold=float(row["units_sold"]),
                corrected_units_sold=float(row["corrected_units_sold"]),
                inventory_level=int(row["end_of_day_stock"]),
                is_stockout=bool(row["is_stockout"]),
                is_outlier=bool(row["is_outlier"]),
                correction_type=str(row["correction_type"]),
            ))

        self.db.add_all(rows)
        await self.db.flush()

        # ── Statistiques ──────────────────────────────────────────────────────
        stockout_corrections = int(df["is_stockout"].sum())
        outlier_corrections = int(df["is_outlier"].sum())

        logger.info(
            f"[ForecastingService] Done — {len(products)} products, "
            f"{len(rows)} rows, {stockout_corrections} OOS, {outlier_corrections} outliers"
        )

        return PipelineResultSchema(
            success=True,
            products_processed=len(products),
            rows_written=len(rows),
            stockout_corrections=stockout_corrections,
            outlier_corrections=outlier_corrections,
            message=(
                f"Pipeline terminée : {len(products)} produits traités, "
                f"{stockout_corrections} corrections OOS, "
                f"{outlier_corrections} outliers corrigés."
            ),
        )

    async def run_prediction_pipeline(self, store_id: str) -> PredictionRunResultSchema:
        """
        Calcule le run rate + prédictions pour tous les produits du store.

        Nécessite que la pipeline de nettoyage ait été exécutée au préalable.

        Args:
            store_id: UUID du store.

        Returns:
            PredictionRunResultSchema avec les statistiques.
        """
        logger.info(f"[ForecastingService] Prediction pipeline start — store {store_id}")

        # ── 1. Charger les produits du store ───────────────────────────────────
        products_result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.supplier))
            .where(Product.store_id == store_id)
        )
        products = list(products_result.scalars().all())

        if not products:
            return PredictionRunResultSchema(
                success=False,
                products_processed=0,
                message="Aucun produit trouvé. Lancez d'abord une synchronisation.",
            )

        product_ids = [p.id for p in products]
        product_map = {str(p.id): p for p in products}

        # ── 2. Charger la cleaned_demand ──────────────────────────────────────
        demand_result = await self.db.execute(
            select(CleanedDemand)
            .where(CleanedDemand.product_id.in_(product_ids))
            .order_by(CleanedDemand.product_id, CleanedDemand.date)
        )
        demand_rows = demand_result.scalars().all()

        if not demand_rows:
            return PredictionRunResultSchema(
                success=False,
                products_processed=0,
                message=(
                    "Aucune demande nettoyée trouvée. "
                    "Lancez d'abord runCleaningPipeline."
                ),
            )

        # ── 3. Construire le DataFrame ────────────────────────────────────────
        df = pd.DataFrame([{
            "product_id": str(d.product_id),
            "date": d.date,
            "corrected_units_sold": float(d.corrected_units_sold),
            "is_stockout": bool(d.is_stockout),
            "is_outlier": bool(d.is_outlier),
        } for d in demand_rows])

        # ── 4. Run Rate 30j par produit ───────────────────────────────────────
        df = calculate_run_rate_batch(df)

        # ── 5. Extraire le run_rate du dernier jour par produit ───────────────
        latest = df.sort_values("date").groupby("product_id").last().reset_index()

        # ── 5b. ABC Analysis by Margin (Sprint 15) ─────────────────────────────
        # On ajoute les données financières au DataFrame pour l'algorithme ABC
        latest['sale_price'] = latest['product_id'].map(lambda pid: product_map.get(pid).sale_price if product_map.get(pid) else 0)
        latest['cost_price'] = latest['product_id'].map(lambda pid: product_map.get(pid).cost_price if product_map.get(pid) else 0)
        
        latest = calculate_abc_ranks_batch(latest)

        # ── 6. Supprimer les anciennes prédictions ────────────────────────────
        await self.db.execute(
            delete(Prediction).where(Prediction.product_id.in_(product_ids))
        )
        await self.db.flush()

        # ── 7. Calculer et insérer les prédictions ────────────────────────────
        today = date.today()
        predictions = []

        abc_map = {row["product_id"]: (row["abc_rank"], row["annual_gross_profit"]) for _, row in latest.iterrows()}

        for _, row in latest.iterrows():
            pid = str(row["product_id"])
            product = product_map.get(pid)
            if product is None:
                continue

            # ── 7b. Seasonality & Boosts (Sprint 15) ──────────────────────────
            # 1. Manual User Boost (from Product model)
            manual_boost = float(product.boost_factor) if product.boost_factor is not None else 1.0
            
            # 2. Auto Seasonality Factor (ML detection)
            prod_demand = df[df["product_id"] == pid]
            auto_season_factor = detect_seasonality_factor(prod_demand)
            
            # Combined Final Run Rate (Vectorized base * Manual * Auto)
            run_rate = float(row["run_rate"]) * manual_boost * auto_season_factor
            
            current_stock = float(product.current_stock)
            lead_time = int(product.lead_time)
            moq = int(product.moq)

            # Jours de stock restants
            days_of_stock = (
                current_stock / run_rate if run_rate > 0 else None
            )

            # Date de rupture prévisionnelle
            stockout_date = predict_stockout_date(
                current_stock=current_stock,
                run_rate=run_rate,
                reference_date=today,
            )

            # Quantité de commande recommandée
            # On injecte le retard fournisseur moyen (Sprint 8)
            avg_delay = product.supplier.average_delay_days if product.supplier else 0.0
            
            reorder_qty = calculate_reorder_quantity(
                run_rate=run_rate,
                lead_time=lead_time,
                moq=moq,
                current_stock=current_stock,
                average_delay=avg_delay
            )

            # --- US 10.1 MAPE Backtesting (Sprint 10) ---
            mape_score = self._calculate_mape_backtest(df[df["product_id"] == pid])

            # --- Sprint 15 : ABC Rank ---
            abc_rank, annual_profit = abc_map.get(pid, ("C", 0.0))

            predictions.append(Prediction(
                product_id=pid,
                run_rate=run_rate,
                days_of_stock=days_of_stock,
                predicted_stockout_date=stockout_date,
                reorder_quantity=reorder_qty,
                current_stock_snapshot=current_stock,
                lead_time_snapshot=lead_time,
                moq_snapshot=moq,
                mape_score=mape_score,
                abc_rank=abc_rank,
                annual_gross_profit=annual_profit
            ))

        self.db.add_all(predictions)
        await self.db.flush()

        logger.info(
            f"[ForecastingService] Predictions done — {len(predictions)} products"
        )

        return PredictionRunResultSchema(
            success=True,
            products_processed=len(predictions),
            message=f"Prédictions calculées pour {len(predictions)} produits.",
        )

    async def get_cleaned_demand(
        self, product_id: str, limit: int = 365
    ) -> list[CleanedDemand]:
        """
        Retourne la demande nettoyée pour un produit, triée par date décroissante.

        Args:
            product_id: UUID du produit.
            limit: Nombre maximum d'entrées (défaut: 365).

        Returns:
            Liste de CleanedDemand.
        """
        result = await self.db.execute(
            select(CleanedDemand)
            .where(CleanedDemand.product_id == product_id)
            .order_by(CleanedDemand.date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_predictions(self, store_id: Optional[str] = None, organization_id: Optional[str] = None) -> list[Prediction]:
        """
        Retourne les prédictions pour tous les produits du store ou de l'organisation.
        """
        from src.modules.inventory.models import Store
        
        stmt = select(Prediction).join(Product)
        
        if store_id:
            # Isolation SaaS : Ne prendre les produits que si le store est connecté
            store_res = await self.db.execute(select(Store).where(Store.id == store_id))
            store = store_res.scalars().first()
            if not store or not store.connected:
                return []
            stmt = stmt.where(Product.store_id == store_id)
        elif organization_id:
            stmt = stmt.join(Store, Product.store_id == Store.id).where(
                Store.organization_id == organization_id,
                Store.connected == True
            )
        else:
            return []

        result = await self.db.execute(
            stmt.order_by(Prediction.predicted_stockout_date.asc().nullslast())
        )
        return list(result.scalars().all())

    async def get_prediction_for_product(self, product_id: str) -> Prediction | None:
        """
        Retourne la prédiction pour un produit spécifique.
        """
        result = await self.db.execute(
            select(Prediction)
            .where(Prediction.product_id == product_id)
        )
        return result.scalars().first()

    async def recalculate_prediction_for_product(self, product_id: str) -> Prediction | None:
        """
        Recalcule les prédictions pour un produit spécifique (US 3.1).
        Utilisé après une mise à jour du Lead Time ou du MOQ.
        """
        # 1. Charger le produit et sa prédiction actuelle
        product_res = await self.db.execute(select(Product).where(Product.id == product_id))
        product = product_res.scalars().first()
        if not product:
            return None

        prediction_res = await self.db.execute(select(Prediction).where(Prediction.product_id == product_id))
        prediction = prediction_res.scalars().first()

        # Si pas de prédiction (pas encore de run rate), on ne peut rien recalculer
        if not prediction:
            return None

        # 2. Recalculer avec les nouvelles valeurs du produit
        run_rate = prediction.run_rate
        current_stock = float(product.current_stock)
        lead_time = int(product.lead_time)
        moq = int(product.moq)

        # Date de rupture prévisionnelle
        prediction.predicted_stockout_date = predict_stockout_date(
            current_stock=current_stock,
            run_rate=run_rate,
            reference_date=date.today(),
        )

        # Quantité de commande recommandée
        prediction.reorder_quantity = calculate_reorder_quantity(
            run_rate=run_rate,
            lead_time=lead_time,
            moq=moq,
            current_stock=current_stock,
        )

        # Mise à jour des snapshots
        prediction.current_stock_snapshot = current_stock
        prediction.lead_time_snapshot = lead_time
        prediction.moq_snapshot = moq
        prediction.days_of_stock = current_stock / run_rate if run_rate > 0 else None

        await self.db.flush()
        return prediction

    async def get_dashboard_kpis(self, store_id: Optional[str] = None, organization_id: Optional[str] = None) -> DashboardKPISchema:
        """
        Calcule les KPIs globaux pour le store ou l'organisation (US 3.5 + Sprint 10).
        """
        from src.modules.inventory.models import Store
        
        base_stmt = select(Product)
        if store_id:
            store_res = await self.db.execute(select(Store).where(Store.id == store_id))
            store = store_res.scalars().first()
            if not store or not store.connected:
                return DashboardKPISchema(total_products=0, actual_stockouts=0, urgent_alerts=0, predicted_stockouts_30d=0, message="Boutique inactive.")
            base_stmt = base_stmt.where(Product.store_id == store_id)
        elif organization_id:
            base_stmt = base_stmt.join(Store, Product.store_id == Store.id).where(
                Store.organization_id == organization_id,
                Store.connected == True
            )
        else:
            return DashboardKPISchema(total_products=0, actual_stockouts=0, urgent_alerts=0, predicted_stockouts_30d=0, message="Aucun contexte.")

        # 1. Total produits & Ruptures réelles
        res = await self.db.execute(
            select(
                func.count(Product.id),
                func.sum(case((Product.current_stock == 0, 1), else_=0))
            ).select_from(base_stmt.subquery())
        )
        total_products, actual_stockouts = res.one()
        total_products = total_products or 0
        actual_stockouts = actual_stockouts or 0

        # 2. Alertes de réapprovisionnement (Urgence & Warning)
        today = date.today()
        
        pred_stmt = select(Prediction, Product).join(Product).options(selectinload(Product.supplier))
        if store_id:
            pred_stmt = pred_stmt.where(Product.store_id == store_id)
        elif organization_id:
            pred_stmt = pred_stmt.join(Store, Product.store_id == Store.id).where(
                Store.organization_id == organization_id,
                Store.connected == True
            )
            
        pred_res = await self.db.execute(pred_stmt)
        data = pred_res.all()
        
        urgent_alerts = 0
        warning_alerts = 0

        for pred, prod in data:
            if prod.current_stock == 0:
                continue # Déjà compté dans Ruptures réelles
            
            if pred.predicted_stockout_date:
                effective_lead_time = prod.lead_time + (prod.supplier.average_delay_days if prod.supplier else 0)
                days_to_stockout = (pred.predicted_stockout_date - today).days
                
                # US 10.2 : Seuils dynamiques
                if days_to_stockout <= effective_lead_time:
                    urgent_alerts += 1
                elif days_to_stockout <= (effective_lead_time + 7):
                    warning_alerts += 1

        return DashboardKPISchema(
            total_products=total_products,
            actual_stockouts=actual_stockouts,
            urgent_alerts=urgent_alerts,
            predicted_stockouts_30d=warning_alerts,
            message="KPIs Omnicanaux calculés avec succès"
        )

    def _calculate_mape_backtest(self, product_df: pd.DataFrame, test_days: int = 7) -> float | None:
        """
        Calcule le MAPE par backtesting sur les N derniers jours.
        Training sur [H-60 à H-test_days], Evaluation sur [H-test_days à H].
        """
        if len(product_df) < (test_days + 5):
            return None

        df = product_df.sort_values("date")
        
        # Split train/test
        train_df = df.iloc[:-test_days].copy()
        test_df = df.iloc[-test_days:].copy()
        
        # Run rate "passé" sur le training set
        train_df = calculate_run_rate_batch(train_df)
        past_run_rate = float(train_df["run_rate"].iloc[-1])
        
        if past_run_rate <= 0:
            return 0.0 # On ne peut pas prédire 0 ventes avec erreur relative

        # Ventes attendues vs réelles sur les 7 derniers jours
        expected_total = past_run_rate * test_days
        actual_total = float(test_df["corrected_units_sold"].sum())
        
        # MAPE simple sur le volume total de la période
        mape = abs(actual_total - expected_total) / max(actual_total, 1.0) * 100
        return min(mape, 100.0) # Capé à 100% pour la lisibilité

    async def get_replenishment_alerts(self, store_id: Optional[str] = None, organization_id: Optional[str] = None) -> list[Prediction]:
        """
        Retourne la liste des produits prioritaires pour le réapprovisionnement (Store ou Organisation).
        """
        from datetime import date, timedelta
        from src.modules.inventory.models import Store
        limit_date = date.today() + timedelta(days=14)

        stmt = select(Prediction).join(Product).where(
            Prediction.predicted_stockout_date <= limit_date
        )

        if store_id:
            store_res = await self.db.execute(select(Store).where(Store.id == store_id))
            store = store_res.scalars().first()
            if not store or not store.connected:
                return []
            stmt = stmt.where(Product.store_id == store_id)
        elif organization_id:
            stmt = stmt.join(Store, Product.store_id == Store.id).where(
                Store.organization_id == organization_id,
                Store.connected == True
            )
        else:
            return []

        result = await self.db.execute(stmt.order_by(Prediction.predicted_stockout_date.asc()))
        return list(result.scalars().all())
