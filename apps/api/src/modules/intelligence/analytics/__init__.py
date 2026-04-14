"""
Sous-module analytics — KPIs financiers, health score, risk scoring.
"""
from .financial_kpis import FinancialKpis, calculate_financial_kpis
from .health_score import calculate_health_score
from .risk_scoring import RiskItem, score_products

__all__ = [
    "FinancialKpis",
    "calculate_financial_kpis",
    "calculate_health_score",
    "RiskItem",
    "score_products",
]
