from typing import Dict, Type
from ..domain.base import BaseConnector
from ..connectors.shopify import ShopifyConnector
from ..connectors.woocommerce import WooCommerceConnector
from ..connectors.csv import CsvConnector

class ConnectorFactory:
    """
    Factory pour instancier le bon connecteur selon la plateforme.
    """
    _connectors: Dict[str, Type[BaseConnector]] = {
        "SHOPIFY": ShopifyConnector,
        "WOOCOMMERCE": WooCommerceConnector,
        "CSV": CsvConnector,
        # "AMAZON": AmazonConnector, # À venir
    }

    @classmethod
    def get_connector(cls, platform: str) -> BaseConnector:
        """
        Retourne une instance du connecteur pour la plateforme donnée.
        """
        connector_class = cls._connectors.get(platform.upper())
        if not connector_class:
            raise ValueError(f"Plateforme non supportée : {platform}")
        
        return connector_class()
