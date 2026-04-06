from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import date

class BaseConnector(ABC):
    """
    Interface universelle pour les connecteurs d'inventaire (Shopify, CSV, Woo, etc.).
    Toute plateforme source doit implémenter ces méthodes pour être compatible avec Michi.
    """

    @abstractmethod
    async def fetch_products(self, shop_id: str) -> List[Dict[str, Any]]:
        """
        Récupère la liste des produits depuis la source.
        Doit retourner un format unifié : [ { "sku": str, "title": str, "inventory": int } ]
        """
        pass

    @abstractmethod
    async def fetch_sales_history(self, product_id: str, days: int = 365) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des ventes.
        Format unifié : [ { "date": date, "units_sold": int, "stock_at_end": int } ]
        """
        pass
