import asyncio
import uuid
from sqlalchemy import delete
from core.database import AsyncSessionLocal, Base, engine
from core.database.models import User, Organization, OrganizationMember, UserRole
from core.security import hash_password
from modules.inventory.infrastructure.persistence.models import Store, Product
from modules.forecasting.infrastructure.persistence.models import Prediction
from modules.inventory.domain.entities import PlatformSource as Platform

async def seed_data():
    """
    Script de Seeding pour le développement.
    Réinitialise et peuple la base de données avec des jeux de tests.
    """
    print("[SEED] Starting database seeding...")
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Nettoyage (Ordre inverse des dépendances)
            print("[SEED] Cleaning existing data...")
            await session.execute(delete(Prediction))
            await session.execute(delete(Product))
            await session.execute(delete(Store))
            await session.execute(delete(OrganizationMember))
            await session.execute(delete(Organization))
            await session.execute(delete(User))
            await session.commit()

            # 2. Création de l'utilisateur de test
            print("[SEED] Creating test user...")
            user_id = uuid.UUID("c946f5b8-662a-4808-8acf-d58b4dab49bc")
            test_user = User(
                id=user_id,
                email="dev@michi.com",
                hashed_password=hash_password("password123"),
                first_name="Kevin",
                last_name="Tsague",
                is_active=True
            )
            session.add(test_user)

            # 3. Création de l'organisation
            print("[SEED] Creating organization...")
            org_id = uuid.UUID("0532244f-d215-4f49-9e1e-c8461f9ec529")
            org = Organization(
                id=org_id,
                name="Michi Corp",
                slug="michi-corp",
                onboarding_completed=True
            )
            session.add(org)
            
            # Lier l'utilisateur à l'organisation comme ADMIN
            member = OrganizationMember(
                user_id=user_id,
                organization_id=org_id,
                role=UserRole.ADMIN
            )
            session.add(member)
            
            # Mettre à jour l'organisation courante de l'utilisateur
            test_user.current_organization_id = org_id

            # 4. Création des Boutiques (Stores)
            print("[SEED] Creating stores...")
            shopify_store = Store(
                id=uuid.uuid4(),
                organization_id=org_id,
                name="Shopify Global",
                platform=Platform.SHOPIFY,
                connected=True
            )
            amazon_store = Store(
                id=uuid.uuid4(),
                organization_id=org_id,
                name="Amazon FR",
                platform=Platform.AMAZON,
                connected=True
            )
            session.add_all([shopify_store, amazon_store])

            # 5. Création de produits et prédictions de test
            print("[SEED] Creating products and predictions...")
            products = [
                ("MICHI-001", "Sérum Anti-Âge Premium", 150, 4.5, shopify_store.id),
                ("MICHI-002", "Crème Hydratante Bio", 45, 12.0, shopify_store.id),
                ("AMZ-X1", "Huile Essentielle Lavande", 10, 25.0, amazon_store.id),
            ]

            from datetime import datetime, timedelta
            for sku, title, stock, run_rate, s_id in products:
                p = Product(
                    id=uuid.uuid4(),
                    store_id=s_id,
                    sku=sku,
                    title=title,
                    current_stock=stock
                )
                session.add(p)
                await session.flush() # Pour avoir l'ID du produit

                # Prediction
                pred = Prediction(
                    id=uuid.uuid4(),
                    product_id=p.id,
                    run_rate=run_rate,
                    days_of_stock=int(stock / run_rate) if run_rate > 0 else 999,
                    predicted_stockout_date=datetime.utcnow() + timedelta(days=int(stock/run_rate)) if run_rate > 0 else None,
                    reorder_quantity=0,
                    computed_at=datetime.utcnow(),
                    demand_sigma=0.0,
                    moq_snapshot=1,
                    abc_rank="A" if run_rate > 10 else "B",
                    annual_gross_profit=0.0,
                    current_stock_snapshot=stock,
                    lead_time_snapshot=14,
                    mape_score=0.1
                )
                session.add(pred)

            await session.commit()
            print("[SEED] Seeding completed successfully! ✅")
            print(f"User: dev@michi.com / password123")

        except Exception as e:
            await session.rollback()
            print(f"[ERROR] Seeding failed: {e}")
            raise e

if __name__ == "__main__":
    asyncio.run(seed_data())
