from typing import List, Dict, Any
from ..domain.base import BaseConnector
from ..domain.schemas import IngestedProduct, IngestedSale
from modules.shopify.infrastructure.mock_generator import generate_full_mock_dataset
from core.utils import retry

class ShopifyConnector(BaseConnector):
    """
    Connecteur Shopify pour Michi.
    Dans le MVP, il utilise le générateur de données Mock.
    En production, il utilisera l'API Shopify (REST/GraphQL).
    """

    async def validate_connection(self, credentials: Dict[str, Any]) -> bool:
        """
        Simule la validation des credentials Shopify.
        """
        return True # Toujours valide pour le mock

    @retry(retries=3, delay=1.0)
    async def fetch_products(self, shop_id: str) -> List[IngestedProduct]:
        """
        Récupère les produits Shopify (Mock).
        """
        products_data, _ = generate_full_mock_dataset(count=50, shop_id=shop_id)
        return [IngestedProduct(**p) for p in products_data]

    async def fetch_sales_history(self, product_sku: str, shop_id: str, days: int = 365) -> List[IngestedSale]:
        """
        Récupère l'historique des ventes pour un produit.
        """
        _, sales_data = generate_full_mock_dataset(count=50, shop_id=shop_id)
        return [IngestedSale(**s) for s in sales_data if s["sku"] == product_sku]

    async def fetch_all_data(self, shop_id: str) -> Dict[str, Any]:
        """
        Récupère produits et ventes.
        """
        products_raw, sales_raw = generate_full_mock_dataset(count=50, shop_id=shop_id)
        return {
            "products": [IngestedProduct(**p) for p in products_raw],
            "sales": [IngestedSale(**s) for s in sales_raw]
        }
