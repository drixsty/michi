#!/usr/bin/env python3
"""
Seed script démo — Sprint 2 (US 1.5)

Réinitialise et régénère un dataset mock complet pour un shop donné.
Utile pour préparer une démo propre en moins de 10 secondes.

Usage:
    python scripts/seed_demo.py
    python scripts/seed_demo.py --shop-id <UUID>
    python scripts/seed_demo.py --count 20
"""
import asyncio
import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, delete

from michi_core.config import settings
from src.modules.auth.models import User, Organization, OrganizationMember
from src.modules.inventory.models import Product, SalesLog, Alert, Supplier, PurchaseOrder, Store, AlertEmail
from src.modules.forecasting.models import CleanedDemand, Prediction
from src.modules.forecasting.application.forecasting_service import ForecastingService
from src.modules.inventory.application.alert_service import AlertService
from src.modules.shopify.mock_generator import generate_full_mock_dataset
from michi_core.database import Base


async def get_or_create_demo_shop(session: AsyncSession) -> tuple[str, str, str]:
    """
    Récupère ou crée l'utilisateur de démo.
    Retourne (email, shop_id, organization_id).
    """
    from src.modules.auth.infrastructure.persistence.models import Organization, OrganizationMember, UserRole
    
    email = "dev@michi.com"
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        print(f"   [INFO] Creation utilisateur de demo {email}...")
        shop_id = uuid.uuid4()
        from src.modules.auth.infrastructure.persistence.models import User as AuthUser
        from michi_core.security import hash_password
        user = AuthUser(
            email=email,
            hashed_password=hash_password("password123"),
            shop_id=shop_id
        )
        session.add(user)
        await session.flush()
    else:
        shop_id = user.shop_id

    # S'assurer d'avoir une organisation (Sprint 16+)
    member_res = await session.execute(
        select(OrganizationMember).where(OrganizationMember.user_id == user.id)
    )
    member = member_res.scalar_one_or_none()
    
    if not member:
        print("   [INFO] Creation organisation de demo...")
        org = Organization(name="Michi Demo Org", slug=f"demo-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.flush()
        
        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=UserRole.ADMIN
        )
        session.add(member)
        user.current_organization_id = org.id
        await session.flush()
        org_id = org.id
    else:
        org_id = member.organization_id
        if not user.current_organization_id:
            user.current_organization_id = org_id
            await session.flush()

    return email, str(shop_id), str(org_id)


async def reset_and_seed(shop_id: str, count: int, session: AsyncSession) -> dict:
    """Supprime les données existantes et régénère le dataset mock."""
    # Supprimer les données existantes (ordres importants pour FKs)
    from src.modules.inventory.models import Alert, AlertEmail, SalesLog
    from src.modules.forecasting.models import CleanedDemand, Prediction
    
    # On supprime tout ce qui est lié aux produits de ce shop
    p_ids_query = select(Product.id).where(Product.store_id == shop_id)
    p_ids_res = await session.execute(p_ids_query)
    p_ids = p_ids_res.scalars().all()
    
    if p_ids:
        await session.execute(delete(AlertEmail).where(AlertEmail.product_id.in_(p_ids)))
        await session.execute(delete(Alert).where(Alert.product_id.in_(p_ids)))
        await session.execute(delete(Prediction).where(Prediction.product_id.in_(p_ids)))
        await session.execute(delete(CleanedDemand).where(CleanedDemand.product_id.in_(p_ids)))
        await session.execute(delete(SalesLog).where(SalesLog.product_id.in_(p_ids)))
        await session.execute(delete(Product).where(Product.id.in_(p_ids)))
    
    await session.flush()

    # Générer le nouveau dataset
    products_data, sales_data = generate_full_mock_dataset(count=count, store_id=shop_id)

    products = [Product(**p) for p in products_data]
    session.add_all(products)
    await session.flush()

    sales_logs = [SalesLog(**s) for s in sales_data]
    session.add_all(sales_logs)
    await session.commit()

    # Calculer ratio ruptures
    stockout_ids = set()
    for log in sales_data:
        if log["units_sold"] == 0 and log["end_of_day_stock"] == 0:
            stockout_ids.add(log["product_id"])
    ratio = len(stockout_ids) / count if count else 0

    return {
        "products": len(products),
        "sales_logs": len(sales_logs),
        "stockout_count": len(stockout_ids),
        "stockout_ratio": ratio,
    }


async def main(shop_id: str | None, count: int) -> None:
    print()
    print("Michi - Seed Demo")
    print(f"   Database : {settings.DATABASE_URL}")
    print()

    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    # S'assurer que les tables existent (Suppression et recréation pour un clean seed)
    async with engine.begin() as conn:
        print("[INFO] Suppression des tables existantes...")
        await conn.run_sync(Base.metadata.drop_all)
        print("[INFO] Creation des nouvelles tables (OMNICANAL)...")
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        # Résoudre le shop_id si non fourni
        if not shop_id:
            email, shop_id, org_id = await get_or_create_demo_shop(session)
            print(f"   Shop     : {email} -> {shop_id}")
            print(f"   Org ID   : {org_id}")
        else:
            print(f"   Shop     : {shop_id}")

        print(f"   Produits : {count}")
        print()
        print("Generation en cours...")

        stats = await reset_and_seed(shop_id=shop_id, count=count, session=session)

        # SEED BOUTIQUE LYON (Sprint 13 QA)
        print("Scénario Multi-boutique (Lyon)...")
        shop_lyon_id = str(uuid.uuid4())
        # On génère moins de produits pour Lyon, certains partagent le même SKU
        await reset_and_seed(shop_id=shop_lyon_id, count=10, session=session)

        # Calculer les prédictions pour les deux shops
        print("Calcul des predictions IA (Paris & Lyon)...")
        forecasting_service = ForecastingService(session)
        await forecasting_service.run_cleaning_pipeline(shop_id)
        await forecasting_service.run_prediction_pipeline(shop_id)
        await forecasting_service.run_cleaning_pipeline(shop_lyon_id)
        await forecasting_service.run_prediction_pipeline(shop_lyon_id)
        
        print("Generation des alertes...")
        alert_service = AlertService(session)
        await alert_service.check_for_stockouts(shop_id)
        await alert_service.check_for_stockouts(shop_lyon_id)

    await engine.dispose()

    print()
    print("Dataset demo pret !")
    print()
    print(f"   Produits créés    : {stats['products']}")
    print(f"   Sales logs créés  : {stats['sales_logs']:,}")
    print(f"   Ruptures simulées : {stats['stockout_count']} produits ({stats['stockout_ratio']:.1%})")
    print()
    print("Prochaines etapes :")
    print("   1. make dev-backend")
    print("   2. make dev-frontend")
    print("   3. http://localhost:3000 -> Synchroniser (charge les donnees)")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed script démo Michi")
    parser.add_argument(
        "--shop-id",
        type=str,
        default=None,
        help="UUID du shop à seeder (défaut: shop du user dev@michi.com)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Nombre de produits à générer (défaut: 50)",
    )
    args = parser.parse_args()
    asyncio.run(main(shop_id=args.shop_id, count=args.count))
