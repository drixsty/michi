"""
Re-export layer for backward compatibility.
Implementation moved to modules.forecasting.persistence.models.
"""
from .persistence.models import (
    CleanedDemand,
    Prediction,
)

__all__ = [
    "CleanedDemand",
    "Prediction",
]
