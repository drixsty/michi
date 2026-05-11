"""
DataValidationService — Vérifie la cohérence du dataset mock généré.

Règles métier contrôlées :
  R1  Nombre de produits attendu (>= 1)
  R2  Tous les champs produit ont des valeurs valides (stock >= 0, lead_time et MOQ dans les plages)
  R3  Chaque produit a exactement 365 entrées de sales_logs (historique complet)
  R4  Aucun gap de dates dans l'historique (jours consécutifs)
  R5  units_sold >= 0 et end_of_day_stock >= 0 sur toutes les lignes
  R6  Ratio ruptures simulées entre 8% et 20% (tolérance autour de 10-15%)
"""
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from modules.inventory.infrastructure.persistence.models import Product, SalesLog
from ..domain.schemas import ValidationReportSchema, ValidationIssue

VALID_LEAD_TIMES = {7, 14, 21, 30, 45}
VALID_MOQS = {5, 10, 20, 50}
EXPECTED_DAYS = 365
STOCKOUT_RATIO_MIN = 0.08
STOCKOUT_RATIO_MAX = 0.20


class DataValidationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate(self, shop_id: str) -> ValidationReportSchema:
        """
        Valide la cohérence du dataset mock pour un shop.

        Args:
            shop_id: UUID du shop à valider.

        Returns:
            ValidationReportSchema avec is_valid, ratio ruptures, et liste d'issues.
        """
        logger.info(f"[DataValidationService] Validating shop {shop_id}")
        issues: list[ValidationIssue] = []

        # ── Charger produits ──────────────────────────────────────────────────
        products_result = await self.db.execute(
            select(Product).where(Product.store_id == shop_id).order_by(Product.sku)
        )
        products = list(products_result.scalars().all())
        product_count = len(products)

        # R1 — Au moins un produit
        if product_count == 0:
            issues.append(ValidationIssue(
                rule="R1",
                severity="error",
                detail="Aucun produit trouvé pour ce shop. Lancez d'abord une synchronisation.",
            ))
            return ValidationReportSchema(
                is_valid=False,
                product_count=0,
                sales_log_count=0,
                stockout_ratio=0.0,
                issues=issues,
                summary="Dataset vide — synchronisation requise.",
            )

        # R2 — Valeurs produit valides
        for p in products:
            if p.current_stock < 0:
                issues.append(ValidationIssue(
                    rule="R2",
                    severity="error",
                    detail=f"Produit {p.sku} : current_stock négatif ({p.current_stock}).",
                ))
            if p.lead_time not in VALID_LEAD_TIMES:
                issues.append(ValidationIssue(
                    rule="R2",
                    severity="warning",
                    detail=f"Produit {p.sku} : lead_time={p.lead_time} hors plage attendue {VALID_LEAD_TIMES}.",
                ))
            if p.moq not in VALID_MOQS:
                issues.append(ValidationIssue(
                    rule="R2",
                    severity="warning",
                    detail=f"Produit {p.sku} : moq={p.moq} hors plage attendue {VALID_MOQS}.",
                ))

        # ── Charger sales logs ────────────────────────────────────────────────
        product_ids = [p.id for p in products]

        logs_count_result = await self.db.execute(
            select(func.count()).where(SalesLog.product_id.in_(product_ids))
        )
        sales_log_count = logs_count_result.scalar() or 0

        # R3 — 365 entrées par produit
        logs_per_product_result = await self.db.execute(
            select(SalesLog.product_id, func.count().label("cnt"))
            .where(SalesLog.product_id.in_(product_ids))
            .group_by(SalesLog.product_id)
        )
        logs_per_product = {str(row.product_id): row.cnt for row in logs_per_product_result}

        for p in products:
            cnt = logs_per_product.get(str(p.id), 0)
            if cnt != EXPECTED_DAYS:
                issues.append(ValidationIssue(
                    rule="R3",
                    severity="error",
                    detail=f"Produit {p.sku} : {cnt} entrées de ventes (attendu: {EXPECTED_DAYS}).",
                ))

        # R4 — Pas de gaps dans l'historique (vérification par échantillon : 5 produits max)
        sample_products = products[:5]
        for p in sample_products:
            dates_result = await self.db.execute(
                select(SalesLog.date)
                .where(SalesLog.product_id == p.id)
                .order_by(SalesLog.date)
            )
            dates = [row[0] for row in dates_result]
            if len(dates) >= 2:
                for i in range(1, len(dates)):
                    if (dates[i] - dates[i - 1]).days != 1:
                        issues.append(ValidationIssue(
                            rule="R4",
                            severity="error",
                            detail=f"Produit {p.sku} : gap détecté entre {dates[i-1]} et {dates[i]}.",
                        ))
                        break  # un seul report par produit suffit

        # R5 — Valeurs négatives dans les logs
        negative_sold_result = await self.db.execute(
            select(func.count())
            .where(SalesLog.product_id.in_(product_ids))
            .where(SalesLog.units_sold < 0)
        )
        negative_sold = negative_sold_result.scalar() or 0
        if negative_sold > 0:
            issues.append(ValidationIssue(
                rule="R5",
                severity="error",
                detail=f"{negative_sold} entrée(s) avec units_sold < 0.",
            ))

        negative_stock_result = await self.db.execute(
            select(func.count())
            .where(SalesLog.product_id.in_(product_ids))
            .where(SalesLog.end_of_day_stock < 0)
        )
        negative_stock = negative_stock_result.scalar() or 0
        if negative_stock > 0:
            issues.append(ValidationIssue(
                rule="R5",
                severity="error",
                detail=f"{negative_stock} entrée(s) avec end_of_day_stock < 0.",
            ))

        # R6 — Ratio ruptures entre 8% et 20%
        stockout_products = 0
        for p in products:
            stockout_result = await self.db.execute(
                select(func.count())
                .where(SalesLog.product_id == p.id)
                .where(SalesLog.units_sold == 0)
                .where(SalesLog.end_of_day_stock == 0)
            )
            cnt = stockout_result.scalar() or 0
            if cnt >= 3:   # au moins 3 jours de rupture = rupture simulée
                stockout_products += 1

        stockout_ratio = stockout_products / product_count if product_count else 0.0

        if not (STOCKOUT_RATIO_MIN <= stockout_ratio <= STOCKOUT_RATIO_MAX):
            issues.append(ValidationIssue(
                rule="R6",
                severity="warning",
                detail=(
                    f"Ratio ruptures = {stockout_ratio:.1%} "
                    f"(attendu entre {STOCKOUT_RATIO_MIN:.0%} et {STOCKOUT_RATIO_MAX:.0%})."
                ),
            ))

        # ── Synthèse ──────────────────────────────────────────────────────────
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]
        is_valid = len(errors) == 0

        if is_valid and len(warnings) == 0:
            summary = (
                f"Dataset valide — {product_count} produits, "
                f"{sales_log_count} logs, "
                f"{stockout_ratio:.1%} ruptures simulées."
            )
        elif is_valid:
            summary = f"Dataset valide avec {len(warnings)} avertissement(s)."
        else:
            summary = f"Dataset invalide — {len(errors)} erreur(s), {len(warnings)} avertissement(s)."

        logger.info(f"[DataValidationService] Result: valid={is_valid}, issues={len(issues)}")

        return ValidationReportSchema(
            is_valid=is_valid,
            product_count=product_count,
            sales_log_count=sales_log_count,
            stockout_ratio=round(stockout_ratio, 4),
            issues=issues,
            summary=summary,
        )
