"""
Re-export layer for backward compatibility.
Implementation moved to src.modules.forecasting.infrastructure.persistence.models.
"""
from .infrastructure.persistence.models import (
    CleanedDemand,
    Prediction,
)

__all__ = [
    "CleanedDemand",
    "Prediction",
]
