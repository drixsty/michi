from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .schemas import IngestedProduct, IngestedSale


class BaseConnector(ABC):
    """
    Interface universelle pour les connecteurs marketplace Michi.

    Contrat :
    - validate_connection : vérifier que les credentials permettent d'accéder à l'API
    - fetch_products      : retourner la liste normalisée des produits
    - fetch_sales_history : retourner l'historique quotidien pour un SKU
    - fetch_all_data      : récupérer produits + ventes en un seul appel optimisé

    Le paramètre `credentials` (Dict optionnel) contient les secrets déchiffrés
    issus de StoreCredential. Les connecteurs CSV/WooCommerce l'ignorent et
    acceptent le contenu du fichier via kwargs.
    """

    @abstractmethod
    async def validate_connection(self, credentials: Dict[str, Any]) -> bool:
        """Vérifie si les accès (API Key, OAuth tokens, etc.) sont valides."""
        pass

    @abstractmethod
    async def fetch_products(
        self,
        shop_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[IngestedProduct]:
        """
        Récupère la liste des produits depuis la source.

        Args:
            shop_id     : UUID ou identifiant interne du store Michi.
            credentials : Secrets déchiffrés du StoreCredential (None en mode CSV).
            **kwargs    : Arguments spécifiques au connecteur (ex: csv_content, mapping).
        """
        pass

    @abstractmethod
    async def fetch_sales_history(
        self,
        product_sku: str,
        shop_id: str,
        days: int = 365,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[IngestedSale]:
        """
        Récupère l'historique de ventes pour un SKU donné.

        Args:
            product_sku : SKU du produit cible.
            shop_id     : UUID ou identifiant interne du store Michi.
            days        : Fenêtre temporelle en jours (défaut : 365).
            credentials : Secrets déchiffrés du StoreCredential.
        """
        pass

    @abstractmethod
    async def fetch_all_data(
        self,
        shop_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Récupère produits et ventes de manière optimisée (batch si possible).

        Returns:
            {"products": List[IngestedProduct], "sales": List[IngestedSale]}
        """
        pass
