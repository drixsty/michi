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

from src.core.config import settings
from src.modules.auth.models import User
from src.modules.inventory.models import Product, SalesLog, Alert, Supplier, PurchaseOrder
from src.modules.forecasting.models import CleanedDemand, Prediction
from src.modules.forecasting.service import ForecastingService
from src.modules.inventory.alert_service import AlertService
from src.modules.shopify.mock_generator import generate_full_mock_dataset
from src.core.database import Base


async def get_or_create_demo_shop(session: AsyncSession) -> tuple[str, str]:
    """
    Récupère le shop_id de l'utilisateur admin@michi.com (ou dev@michi.com).
    Retourne (email, shop_id).
    """
    for email in ("admin@michi.com", "dev@michi.com"):
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            return email, str(user.shop_id)
    raise RuntimeError(
        "Aucun utilisateur de démo trouvé. Lancez d'abord : make seed"
    )


async def reset_and_seed(shop_id: str, count: int, session: AsyncSession) -> dict:
    """Supprime les données existantes et régénère le dataset mock."""
    # Supprimer les données existantes (ordres importants pour FKs)
    from src.modules.inventory.models import Alert, AlertEmail, SalesLog
    from src.modules.forecasting.models import CleanedDemand, Prediction
    
    # On supprime tout ce qui est lié aux produits de ce shop
    p_ids_query = select(Product.id).where(Product.shop_id == shop_id)
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
    products_data, sales_data = generate_full_mock_dataset(count=count, shop_id=shop_id)

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

    # S'assurer que les tables existent
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        # Résoudre le shop_id si non fourni
        if not shop_id:
            email, shop_id = await get_or_create_demo_shop(session)
            print(f"   Shop     : {email} -> {shop_id}")
        else:
            print(f"   Shop     : {shop_id}")

        print(f"   Produits : {count}")
        print()
        print("Generation en cours...")

        stats = await reset_and_seed(shop_id=shop_id, count=count, session=session)

        # TRIGGER AI PIPELINE (Sprint 12)
        print("Calcul des predictions IA...")
        forecasting_service = ForecastingService(session)
        await forecasting_service.run_cleaning_pipeline(shop_id)
        await forecasting_service.run_prediction_pipeline(shop_id)
        
        print("Generation des alertes...")
        alert_service = AlertService(session)
        await alert_service.check_for_stockouts(shop_id)

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
