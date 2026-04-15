import pandas as pd
"""
Ports du domaine intelligence/ — Sprint 21.

Définit les interfaces (Protocol) que les adaptateurs doivent implémenter
pour fournir des données au moteur intelligence.

Aucune dépendance externe — pure abstraction Python.
"""

from typing import Any, Protocol, runtime_checkable


from .entities import DemandSignal, PredictionResult, InventoryHealthReport


@runtime_checkable
class IDemandDataPort(Protocol):
    """
    Port entrant : fournit les données de demande brutes pour un SKU.

    Implémenté par l'infrastructure (SQLAlchemy repository, CSV loader, etc.)
    """

    async def get_demand_series(self, sku: str, days: int = 90) -> pd.DataFrame:
        """
        Retourne la série de demande brute pour un SKU.

        Returns:
            DataFrame avec colonnes : date (index), quantity (float)
        """
        ...

    async def get_demand_series_batch(
        self, skus: list[str], days: int = 90
    ) -> dict[str, pd.DataFrame]:
        """Retourne les séries de demande pour plusieurs SKUs."""
        ...


@runtime_checkable
class IIntelligenceEngine(Protocol):
    """
    Port sortant : interface principale du moteur intelligence.

    Utilisé par les services applicatifs pour obtenir les signaux
    nettoyés et les prédictions.
    """

    def process_demand(
        self, raw_series: pd.DataFrame, sku: str
    ) -> list[DemandSignal]:
        """
        Applique le pipeline complet (OOS → IQR → RunRate) sur la série brute.

        Args:
            raw_series: DataFrame avec colonnes date + quantity.
            sku: Identifiant SKU.

        Returns:
            Liste de DemandSignal nettoyés.
        """
        ...

    def predict(
        self,
        sku: str,
        product_id: str,
        current_stock: int,
        run_rate: float,
        sale_price: float,
        reorder_point: int = 0,
    ) -> PredictionResult:
        """
        Calcule la prédiction de rupture et quantité de réassort.

        Args:
            sku: Identifiant SKU.
            product_id: ID produit.
            current_stock: Stock actuel.
            run_rate: Run rate journalier.
            sale_price: Prix de vente unitaire.
            reorder_point: Seuil de réassort (défaut: 0).

        Returns:
            PredictionResult avec date de rupture et quantité recommandée.
        """
        ...

    def compute_inventory_health(
        self, sku_aggregation: dict[str, dict[str, Any]]
    ) -> InventoryHealthReport:
        """
        Calcule le rapport de santé inventaire complet.

        Args:
            sku_aggregation: Agrégation SKU après first-pass decisions/service.py.

        Returns:
            InventoryHealthReport avec KPIs financiers, health_score et top_risks.
        """
        ...
