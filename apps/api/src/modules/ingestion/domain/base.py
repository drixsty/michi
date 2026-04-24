from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date
from .schemas import IngestedProduct, IngestedSale

class BaseConnector(ABC):
    """
    Interface universelle pour les connecteurs d'inventaire (Shopify, CSV, Woo, etc.).
    Toute plateforme source doit implémenter ces méthodes pour être compatible avec Michi.
    """

    @abstractmethod
    async def validate_connection(self, credentials: Dict[str, Any]) -> bool:
        """
        Vérifie si les accès (API Key, URL, etc.) sont valides.
        """
        pass

    @abstractmethod
    async def fetch_products(self, shop_id: str) -> List[IngestedProduct]:
        """
        Récupère la liste des produits depuis la source.
        """
        pass

    @abstractmethod
    async def fetch_sales_history(self, product_sku: str, shop_id: str, days: int = 365) -> List[IngestedSale]:
        """
        Récupère l'historique des ventes pour un produit.
        """
        pass

    @abstractmethod
    async def fetch_all_data(self, shop_id: str) -> Dict[str, Any]:
        """
        Récupère produits et ventes de manière optimisée.
        Retourne : {"products": List[IngestedProduct], "sales": List[IngestedSale]}
        """
        pass
