from enum import Enum
from typing import Dict, Any, List

class PlanName(str, Enum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"

# Définition des capacités et limites par plan
PLAN_LIMITS: Dict[PlanName, Dict[str, Any]] = {
    PlanName.FREE: {
        "max_stores": 1,
        "can_use_ai_ingestion": True,
        "forecasting_days": 30,
        "has_smart_alerts": False,
        "max_skus": 500
    },
    PlanName.PRO: {
        "max_stores": 5,
        "can_use_ai_ingestion": True,
        "forecasting_days": 90,
        "has_smart_alerts": True,
        "max_skus": 5000
    },
    PlanName.ENTERPRISE: {
        "max_stores": 999,
        "can_use_ai_ingestion": True,
        "forecasting_days": 365,
        "has_smart_alerts": True,
        "max_skus": 1000000
    }
}

def get_plan_limits(plan: str) -> Dict[str, Any]:
    """Récupère les limites pour un plan donné, ou FREE par défaut."""
    try:
        p_name = PlanName(plan.upper())
    except (ValueError, AttributeError):
        p_name = PlanName.FREE
    return PLAN_LIMITS[p_name]
