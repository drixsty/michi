from typing import List, Dict, Any
from ..base import BaseConnector
from modules.shopify.infrastructure.mock_generator import generate_full_mock_dataset

class ShopifyConnector(BaseConnector):
    """
    Connecteur Shopify pour Michi.
    Dans le MVP, il utilise le générateur de données Mock.
    En production, il utilisera l'API Shopify (REST/GraphQL).
    """

    async def fetch_products(self, shop_id: str) -> List[Dict[str, Any]]:
        """
        Récupère les produits Shopify (Mock).
        """
        # On délègue à l'existant pour la génération
        products_data, _ = generate_full_mock_dataset(count=50, shop_id=shop_id)
        
        # Le format retourné par mock_generator est déjà compatible
        return products_data

    async def fetch_sales_history(self, product_sku: str, shop_id: str, days: int = 365) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des ventes pour un produit.
        """
        # Le mock generator génère tout d'un coup, on filtre ici si besoin 
        # ou on laisse l'orchestrateur gérer le batch complet.
        _, sales_data = generate_full_mock_dataset(count=50, shop_id=shop_id)
        
        return [s for s in sales_data if s["sku"] == product_sku]

    async def fetch_all_data(self, shop_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Récupère les produits ET les ventes en un seul appel (Efficace pour le Mock).
        """
        products_data, sales_data = generate_full_mock_dataset(count=50, shop_id=shop_id)
        return {
            "products": products_data,
            "sales": sales_data
        }
