"""
Entités du domaine intelligence/ — Sprint 21.

Définit les value objects et entités pures du bounded context Intelligence.
Aucune dépendance externe (pas de SQLAlchemy, pas de Pydantic v2 imposé).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class DemandSignal:
    """
    Signal de demande nettoyé pour un SKU à une date donnée.

    Produit par le pipeline cleaning (OOS correction → IQR → RunRate).
    """
    sku: str
    reference_date: date
    raw_quantity: float
    cleaned_quantity: float
    run_rate: float
    is_oos_corrected: bool
    is_iqr_corrected: bool
    seasonality_factor: float = 1.0


@dataclass(frozen=True)
class PredictionResult:
    """
    Résultat de prédiction pour un SKU.

    Produit par les algorithmes predict_stockout_date / calculate_reorder_quantity.
    """
    sku: str
    product_id: str
    current_stock: int
    run_rate: float
    predicted_stockout_date: Optional[date]
    coverage_days: float
    reorder_quantity: int
    risk_value: float


@dataclass(frozen=True)
class RiskScore:
    """
    Score de risque consolidé pour un SKU.

    Produit par intelligence/analytics/risk_scoring.py.
    """
    sku: str
    product_id: str
    title: str
    risk_value: float
    days_of_stock: float
    stockout_date: Optional[date]
    reorder_quantity: int
    run_rate: float
    supplier_id: Optional[str]
    source_platform: str
    cost_price: float
    sale_price: float


@dataclass(frozen=True)
class InventoryHealthReport:
    """
    Rapport de santé inventaire complet.

    Agrège FinancialKpis + health_score + top_risks.
    """
    health_score: int
    inventory_value_cost: float
    inventory_value_sale: float
    revenue_at_risk: float
    stock_coverage_avg_days: float
    total_run_rate: float
    total_stock: int
    avg_sale_price: float
    stockout_count: int
    total_skus: int
    top_risks: list[RiskScore] = field(default_factory=list)
