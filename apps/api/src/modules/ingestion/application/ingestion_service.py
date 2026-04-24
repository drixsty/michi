import uuid
from typing import List
from sqlalchemy import select
from .factory import ConnectorFactory
from ..domain.schemas import IngestionResult
from core.database import AsyncSessionLocal
from modules.inventory.infrastructure.persistence.models import Store, Product

class IngestionService:
    """
    Service Orchestrateur : Ingestion -> Normalisation -> Persistance.
    """

    async def ingest_store_data(self, store_id: uuid.UUID) -> IngestionResult:
        """
        Déclenche l'ingestion complète pour une boutique donnée.
        """
        async with AsyncSessionLocal() as session:
            # 1. Récupérer la boutique
            result = await session.execute(select(Store).filter(Store.id == store_id))
            store = result.scalar_one_or_none()
            if not store:
                raise ValueError("Boutique non trouvée")

            # 2. Obtenir le connecteur
            connector = ConnectorFactory.get_connector(str(store.platform))
            
            # 3. Récupérer les données (Mock ou Réel selon le connecteur)
            data = await connector.fetch_all_data(str(store.id))
            products_data = data["products"] # List[IngestedProduct]
            sales_data = data["sales"]       # List[IngestedSale]

            # 4. Persistance (Batch insert/update)
            for p_data in products_data:
                # Upsert Product
                prod_result = await session.execute(
                    select(Product).filter(
                        Product.store_id == store_id, 
                        Product.sku == p_data.sku
                    )
                )
                product = prod_result.scalar_one_or_none()

                if not product:
                    product = Product(
                        id=uuid.uuid4(),
                        store_id=store_id,
                        sku=p_data.sku,
                        title=p_data.title,
                        current_stock=p_data.current_stock
                    )
                    session.add(product)
                else:
                    product.title = p_data.title
                    product.current_stock = p_data.current_stock
            
            await session.commit()

            return IngestionResult(
                store_id=str(store_id),
                products_count=len(products_data),
                sales_count=len(sales_data)
            )
