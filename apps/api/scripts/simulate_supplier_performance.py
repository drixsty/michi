import os

# Injection manuelle des variables minimales pour satisfaire Pydantic Settings
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://michi:michi123@localhost:5433/michi_db")
os.environ.setdefault("SECRET_KEY", "dummy_secret_for_simulation")
os.environ.setdefault("SHOPIFY_API_KEY", "mock")
os.environ.setdefault("SHOPIFY_API_SECRET", "mock")
os.environ.setdefault("SHOPIFY_REDIRECT_URI", "http://localhost")
os.environ.setdefault("SHOPIFY_SCOPES", "read_products")
os.environ.setdefault("STRIPE_API_KEY", "mock")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "mock")
os.environ.setdefault("STRIPE_PRICE_BASIC", "mock")
os.environ.setdefault("STRIPE_PRICE_PRO", "mock")
os.environ.setdefault("STRIPE_PRICE_ENTERPRISE", "mock")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("SMTP_PORT", "1025")
os.environ.setdefault("SMTP_USER", "mock")
os.environ.setdefault("SMTP_PASSWORD", "mock")
os.environ.setdefault("EMAIL_FROM", "test@test.com")

import asyncio
import uuid
import random
from datetime import date, timedelta, datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Récupération manuelle de la DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

from modules.inventory.infrastructure.persistence.models import Store, Supplier, PurchaseOrder, Product
# Import Invitation to resolve SQLAlchemy relationship mapping
from modules.auth.infrastructure.persistence.models import Invitation
# Import Prediction to resolve SQLAlchemy relationship mapping
from modules.forecasting.infrastructure.persistence.models import Prediction
# Import Organization/User to create baseline data
from core.database.models import Organization, User, OrganizationMember

async def simulate_supplier_performance():
    print("=== Phase 1 : Simulation de Performance Fournisseur ===")
    
    async with AsyncSessionLocal() as session:
        # 1. Récupérer un store existant ou en créer un
        stmt = select(Store).limit(1)
        result = await session.execute(stmt)
        store = result.scalar_one_or_none()
        
        if not store:
            print("Aucun store trouvé. Création d'une organisation et d'un store de test...")
            org_id = uuid.uuid4()
            org = Organization(
                id=org_id,
                name="Michi Test Corp",
                slug="michi-test-corp"
            )
            session.add(org)
            
            store_id = uuid.uuid4()
            store = Store(
                id=store_id,
                organization_id=org_id,
                name="Main Warehouse",
                platform="CUSTOM",
                connected=True
            )
            session.add(store)
            await session.flush()
            print(f"Organisation '{org.name}' et Store '{store.name}' créés.")

        print(f"Utilisation du Store : {store.name} (ID: {store.id})")

        # 2. Définition des profils de fournisseurs
        supplier_profiles = [
            {
                "name": "Global Logistics (Stable)",
                "email": "stable@global.log",
                "delay_distribution": lambda: random.randint(-1, 1), # Stable autour de 0
                "reliability_target": 0.98
            },
            {
                "name": "FastTrack Asia (Dériveur)",
                "email": "delay@fasttrack.asia",
                "delay_distribution": lambda: random.randint(4, 7), # Toujours en retard
                "reliability_target": 0.60
            },
            {
                "name": "Variable Source (Imprévisible)",
                "email": "chaos@var-source.com",
                "delay_distribution": lambda: random.choice([-2, 0, 5, 12, 20]), # Imprévisible
                "reliability_target": 0.40
            }
        ]

        created_suppliers = []

        # 3. Création des fournisseurs et de leur historique
        for profile in supplier_profiles:
            # Suppression si déjà existant par son nom pour ré-exécution propre
            stmt = select(Supplier).where(Supplier.name == profile["name"], Supplier.store_id == store.id)
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if existing:
                await session.delete(existing)
                await session.flush()

            supplier = Supplier(
                id=uuid.uuid4(),
                store_id=store.id,
                name=profile["name"],
                contact_email=profile["email"],
                reliability_score=profile["reliability_target"],
                average_delay_days=0.0 # Sera calculé par le service plus tard
            )
            session.add(supplier)
            created_suppliers.append((supplier, profile))
            print(f"Création du fournisseur : {profile['name']}")

        await session.flush()

        # 4. Générer l'historique de commandes (PurchaseOrders)
        # On suppose que chaque fournisseur livre un produit différent dans cette simulation
        products_stmt = select(Product).where(Product.store_id == store.id).limit(len(created_suppliers))
        products = (await session.execute(products_stmt)).scalars().all()
        
        if not products:
            print("Attention : Pas assez de produits pour l'assignation. Création de produits fictifs.")
            for i in range(len(created_suppliers)):
                p = Product(
                    id=uuid.uuid4(),
                    store_id=store.id,
                    sku=f"SIM-PROD-{i}",
                    title=f"Simulation Product {i}",
                    current_stock=100,
                    lead_time=14
                )
                session.add(p)
                products.append(p)
            await session.flush()

        today = date.today()
        
        for i, (supplier, profile) in enumerate(created_suppliers):
            product = products[i % len(products)]
            product.supplier_id = supplier.id # Liaison
            
            print(f"Assignation du produit {product.sku} au fournisseur {supplier.name}")
            
            # Générer 15 commandes passées
            for po_idx in range(15):
                # Date de commande reculant de 20 jours à chaque fois
                order_date = today - timedelta(days=(po_idx + 1) * 25)
                # Délai théorique de 14 jours
                expected_arrival = order_date + timedelta(days=14)
                
                # Appliquer la distribution de délai du profil
                real_delay = profile["delay_distribution"]()
                actual_arrival = expected_arrival + timedelta(days=real_delay)
                
                po = PurchaseOrder(
                    id=uuid.uuid4(),
                    store_id=store.id,
                    product_id=product.id,
                    supplier_id=supplier.id,
                    quantity=random.randint(50, 200),
                    order_date=order_date,
                    expected_arrival_date=expected_arrival,
                    actual_arrival_date=actual_arrival,
                    status="COMPLETED"
                )
                session.add(po)

        await session.commit()
        print("\nSimulation terminée avec succès.")
        print("Toutes les commandes sont marquées comme COMPLETED avec des dates réelles variées.")

if __name__ == "__main__":
    asyncio.run(simulate_supplier_performance())
