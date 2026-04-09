#!/usr/bin/env python3
"""
Script pour seed la DB avec un user de développement

Usage:
    python scripts/seed_dev_data.py
"""
import asyncio
import sys
import uuid
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.core.security import hash_password
from src.core.database import Base
from src.modules.auth.models import User
from src.modules.inventory.models import Product, SalesLog, Alert, Supplier, PurchaseOrder
from src.modules.forecasting.models import CleanedDemand, Prediction


async def create_tables():
    """Crée toutes les tables"""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("Tables creees")


async def seed_dev_user():
    """Crée un user de développement"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Vérifier si user existe déjà
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == "dev@michi.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("⚠️  User dev@michi.com existe déjà")
            print(f"   User ID: {existing_user.id}")
            print(f"   Shop ID: {existing_user.shop_id}")
            return
        
        # Créer nouveau user
        shop_id = uuid.uuid4()
        user = User(
            email="dev@michi.com",
            hashed_password=hash_password("password123"),
            shop_id=shop_id,
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # 1. Créer deux fournisseurs de démonstration
        s1 = Supplier(
            shop_id=shop_id,
            name="Fournisseur Premium Co.",
            contact_email="premium@example.com",
            reliability_score=1.0,
            average_delay_days=0.0
        )
        s2 = Supplier(
            shop_id=shop_id,
            name="Late Supply Logistics",
            contact_email="late@example.com",
            reliability_score=0.6,
            average_delay_days=5.5  # 5.5 jours de retard en moyenne
        )
        session.add_all([s1, s2])
        await session.flush()

        print(f"Fournisseurs crees: {s1.name}, {s2.name}")
        
        await session.commit()
        await session.refresh(user)
    
    await engine.dispose()


async def main():
    """Main function"""
    print("Seeding database...")
    print(f"Database: {settings.DATABASE_URL}")
    print()
    
    # Créer tables
    await create_tables()
    print()
    
    # Créer user de dev
    await seed_dev_user()
    print()
    
    print("Seed termine !")
    print()
    print("Vous pouvez maintenant :")
    print("   1. Lancer le backend : cd backend && uvicorn src.main:app --reload")
    print("   2. Lancer le frontend : cd frontend && npm run dev")
    print("   3. Se connecter sur http://localhost:3000/login")
    print("      Email: dev@michi.com")
    print("      Password: password123")


if __name__ == "__main__":
    asyncio.run(main())
