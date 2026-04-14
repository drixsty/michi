"""
Domaine intelligence/ — entités pures et ports (interfaces).
"""
from .entities import DemandSignal, PredictionResult, RiskScore, InventoryHealthReport
from .ports import IDemandDataPort, IIntelligenceEngine

__all__ = [
    "DemandSignal",
    "PredictionResult",
    "RiskScore",
    "InventoryHealthReport",
    "IDemandDataPort",
    "IIntelligenceEngine",
]
