#!/usr/bin/env python3
"""
Script pour seed la DB avec un user de développement (Version Multi-Tenant Robuste)
"""
import asyncio
import sys
import uuid
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from src.core.config import settings
from src.core.security import hash_password
from src.core.database import Base
from src.modules.auth.models import User, Organization, OrganizationMember, UserRole
from src.modules.inventory.models import Product, Supplier, Store, PlatformSource
from src.modules.forecasting.models import Prediction # Important pour SQLAlchemy

async def create_tables():
    """Crée toutes les tables"""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Tables creees")

async def _ensure_user_with_org(session: AsyncSession, email: str, org_name: str, plan="BASIC", status="ACTIVE"):
    """Vérifie ou crée un utilisateur avec une organisation et des données de démo"""
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            email=email,
            first_name=email.split('@')[0].capitalize(),
            last_name="Test",
            hashed_password=hash_password("password123"),
            shop_id=uuid.uuid4()
        )
        session.add(user)
        await session.flush()
        print(f"[USER] {email} cree.")
    else:
        print(f"[USER] {email} existe deja.")

    # Vérifier l'organisation
    member_result = await session.execute(
        select(OrganizationMember).where(OrganizationMember.user_id == user.id)
    )
    member = member_result.scalars().first()
    
    if not member:
        org = Organization(
            name=org_name,
            slug=f"{org_name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:4]}",
            plan=plan,
            subscription_status=status,
            stripe_customer_id=f"cus_mock_{uuid.uuid4().hex[:8]}"
        )
        session.add(org)
        await session.flush()
        
        member = OrganizationMember(
            user_id=user.id,
            organization_id=org.id,
            role=UserRole.ADMIN
        )
        session.add(member)
        user.current_organization_id = org.id
        print(f"[ORG] {org_name} ({plan}/{status}) creee pour {email}.")
        
        # 1. Créer un Store
        store = Store(
            organization_id=org.id,
            name=f"Boutique {org_name}",
            platform=PlatformSource.SHOPIFY,
            connected=True
        )
        session.add(store)
        await session.flush()

        # 2. Créer un Fournisseur
        supplier = Supplier(
            store_id=store.id,
            name=f"Fournisseur Premium {email.split('@')[0]}",
            contact_email=f"contact@{email.split('@')[0]}.com",
            reliability_score=1.0,
            average_delay_days=0.0
        )
        session.add(supplier)
        await session.flush()

        # 3. Créer un Produit
        product = Product(
            id=uuid.uuid4(),
            store_id=store.id,
            sku=f"DEMO-{plan}-{uuid.uuid4().hex[:4]}",
            title=f"Produit Test {plan}",
            current_stock=50,
            lead_time=14,
            moq=5,
            source_platform=PlatformSource.SHOPIFY,
            supplier_id=supplier.id
        )
        session.add(product)
        print(f"   [DATA] Store, Supplier et Product crees pour {email}.")
    
    await session.commit()

async def seed_dev_data():
    """Crée les données de développement (Multi-Tenant & Billing)"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Cas Standard Dev (ENTERPRISE ACTIVE)
        await _ensure_user_with_org(session, "dev@michi.com", "Michi Dev Corp", "ENTERPRISE")
        
        # 2. Cas Plan BASIC
        await _ensure_user_with_org(session, "basic@michi.com", "StartUp Essentials", "BASIC")
        
        # 3. Cas Plan PRO (Paiement OK)
        await _ensure_user_with_org(session, "pro@michi.com", "Scale-up Pro", "PRO")
        
        # 4. Cas Incident de paiement (PAST_DUE)
        await _ensure_user_with_org(session, "late@michi.com", "Late Payers Inc", "PRO", "PAST_DUE")

    await engine.dispose()
    print("\nSeed multi-tenant avec divers abonnements termine !")

async def main():
    print("Seeding database...")
    await create_tables()
    await seed_dev_data()
    print("\nSeed termine !")

if __name__ == "__main__":
    asyncio.run(main())
