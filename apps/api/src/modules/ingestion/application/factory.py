from typing import Dict, Type
from ..domain.base import BaseConnector
from ..connectors.shopify import ShopifyConnector
from ..connectors.woocommerce import WooCommerceConnector
from ..connectors.csv import CSVConnector
from ..connectors.amazon import AmazonConnector
from ..connectors.ebay import EbayConnector
from ..connectors.etsy import EtsyConnector


class ConnectorFactory:
    """
    Factory pour instancier le bon connecteur selon la plateforme.
    Supporte : Shopify, WooCommerce, CSV, Amazon, eBay, Etsy.
    """

    _connectors: Dict[str, Type[BaseConnector]] = {
        "SHOPIFY": ShopifyConnector,
        "WOOCOMMERCE": WooCommerceConnector,
        "CSV": CSVConnector,
        "AMAZON": AmazonConnector,
        "EBAY": EbayConnector,
        "ETSY": EtsyConnector,
    }

    @classmethod
    def get_connector(cls, platform: str) -> BaseConnector:
        """
        Retourne une instance du connecteur pour la plateforme donnée.

        Args:
            platform: Nom de la plateforme (insensible à la casse).

        Raises:
            ValueError: Si la plateforme n'est pas supportée.
        """
        connector_class = cls._connectors.get(platform.upper())
        if not connector_class:
            supported = ", ".join(sorted(cls._connectors.keys()))
            raise ValueError(
                f"Plateforme non supportée : '{platform}'. "
                f"Plateformes disponibles : {supported}"
            )
        return connector_class()

    @classmethod
    def supported_platforms(cls) -> list[str]:
        """Retourne la liste des plateformes supportées."""
        return sorted(cls._connectors.keys())
