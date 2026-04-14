#!/usr/bin/env python3
import asyncio
import sys
import uuid
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from michi_core.config import settings
from michi_core.security import hash_password
from michi_core.database import Base

# Imports requis pour que SQLAlchemy découvre les modèles lors du drop/create
from src.modules.auth.models import User, Organization, OrganizationMember, Invitation
from src.modules.inventory.models import Product, SalesLog, Store, Supplier, PurchaseOrder, Alert
from src.modules.forecasting.models import CleanedDemand, Prediction

async def recreate_all():
    """Supprime et recrée toutes les tables"""
    print(f"📍 Database: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        print("🔥 Suppression des tables existantes...")
        await conn.run_sync(Base.metadata.drop_all)
        print("🏗️  Création des nouvelles tables (OMNICANAL)...")
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ Schéma mis à jour avec succès.")

async def seed_dev_user():
    """Recrée le user de développement par défaut"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        shop_id = uuid.uuid4()
        user = User(
            email="dev@michi.com",
            hashed_password=hash_password("password123"),
            shop_id=shop_id,
        )
        session.add(user)
        await session.commit()
        print(f"✅ User créé: dev@michi.com / password123")
        print(f"   Shop ID: {shop_id}")
    
    await engine.dispose()

async def main():
    await recreate_all()
    await seed_dev_user()
    print("\n✨ Base de données rafraîchie pour le Sprint 7 !")

if __name__ == "__main__":
    asyncio.run(main())
