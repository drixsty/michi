import asyncio
import uuid
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, text

from src.core.database import engine, Base, AsyncSessionLocal
from src.core.security import hash_password

# Import models to ensure they are registered with Base
from src.modules.auth.models import User, Organization, OrganizationMember, UserRole
from src.modules.inventory.models import Store, Product, SalesLog, Supplier, Alert, PlatformSource
from src.modules.forecasting.models import Prediction

async def seed_v2():
    print("[SEED V2] Database Synchronization — Multi-Tenant SaaS Mode")
    
    async with engine.begin() as conn:
        print("[SEED V2] Hard reset: Dropping schema public...")
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;")) 
        
        print("[SEED V2] Recreating all tables...")
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 1. Users
        users_to_create = [
            {"email": "test@test.com", "password": "michi123"},
            {"email": "dev@michi.com", "password": "michi123"} # Added habitual dev email
        ]
        
        users = []
        for u_info in users_to_create:
            name_part = u_info["email"].split('@')[0]
            user = User(
                email=u_info["email"],
                first_name=name_part.capitalize(),
                last_name="Michi",
                hashed_password=hash_password(u_info["password"]),
                preferences={"currency": "EUR", "language": "fr"}
            )
            db.add(user)
            users.append(user)
        
        await db.flush()
        print(f"DONE: {len(users)} users created.")

        # 2. Organization 1: Michi Corp
        org1 = Organization(
            name="Michi Corp",
            slug="michi-corp",
            plan="ENTERPRISE",
            subscription_status="ACTIVE"
        )
        db.add(org1)
        await db.flush()

        for user in users:
            member = OrganizationMember(
                user_id=user.id,
                organization_id=org1.id,
                role=UserRole.ADMIN,
                permissions={"all": True}
            )
            db.add(member)
            user.current_organization_id = org1.id
        
        await db.flush()
        print(f"DONE: Organization 1 created: {org1.name}")

        # 3. Organization 2: Zen Garden
        org2 = Organization(
            name="Zen Garden",
            slug="zen-garden",
            plan="GROWTH",
            subscription_status="ACTIVE"
        )
        db.add(org2)
        await db.flush()

        for user in users:
            member = OrganizationMember(
                user_id=user.id,
                organization_id=org2.id,
                role=UserRole.ADMIN if user.email == "dev@michi.com" else UserRole.VIEWER,
                permissions={"all": True}
            )
            db.add(member)
            
        await db.flush()
        print(f"DONE: Organization 2 created: {org2.name}")

        # 4. Stores for Michi Corp
        stores_org1 = [
            {"name": "Shopify France", "platform": PlatformSource.SHOPIFY},
            {"name": "Amazon Europe", "platform": PlatformSource.AMAZON},
        ]
        
        # 5. Store for Zen Garden
        stores_org2 = [
            {"name": "Woo Store", "platform": PlatformSource.WOOCOMMERCE},
        ]
        
        all_stores_config = [
            (org1.id, stores_org1),
            (org2.id, stores_org2)
        ]

        for org_id, config in all_stores_config:
            for s_info in config:
                store = Store(
                    organization_id=org_id,
                    name=s_info["name"],
                    platform=s_info["platform"],
                    connected=True,
                    last_sync_at=datetime.utcnow()
                )
                db.add(store)
                await db.flush()
                
                # Supplier
                supplier = Supplier(
                    store_id=store.id,
                    name=f"Supplier {store.name}",
                    contact_email=f"contact@{store.name.lower().replace(' ', '')}.com"
                )
                db.add(supplier)
                await db.flush()

                # Products
                for i in range(1, 4):
                    prod = Product(
                        store_id=store.id,
                        title=f"Produit {store.platform.value} #{i}",
                        sku=f"SKU-{org_id.hex[:4]}-{store.platform.value.upper()}-{i}",
                        lead_time=7,
                        moq=10,
                        current_stock=20 * i,
                        supplier_id=supplier.id,
                        source_platform=store.platform,
                        cost_price=15.0,
                        sale_price=35.0
                    )
                    db.add(prod)
                    await db.flush()

                    # Sales Logs
                    for d in range(1, 15):
                        log = SalesLog(
                            product_id=prod.id,
                            date=date.today() - timedelta(days=d),
                            units_sold=i + d % 4,
                            end_of_day_stock=prod.current_stock
                        )
                        db.add(log)
            
        await db.commit()
        print("FINISHED: [SEED V2] Successfully created 2 Users (including dev@michi.com), 2 Orgs and 3 Stores.")

if __name__ == "__main__":
    asyncio.run(seed_v2())
