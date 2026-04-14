import asyncio
import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import AsyncSessionLocal, Base, engine as async_engine
from src.modules.auth.models import User
from src.modules.shopify.service import ShopifyService
from src.modules.forecasting.service import ForecastingService
from src.core.config import settings
from sqlalchemy import select, create_engine

async def run():
    # Force schema creation (Fallback si Alembic a raté)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Schéma validé (Base.metadata.create_all)")

    async with AsyncSessionLocal() as db:
        # Trouver un shop
        result = await db.execute(select(User).where(User.email == 'dev@michi.com'))
        user = result.scalars().first()
        
        if not user:
            print("❌ Aucun utilisateur 'dev@michi.com' trouvé.")
            return
            
        shop_id = str(user.shop_id)
        print(f"⚡ Lancement de la Power Sync pour le shop : {shop_id}")
        
        # 1. Sync Shopify (Mock Data)
        print("🔗 1/3 Synchronisation Shopify...")
        shopify_service = ShopifyService(db)
        sync_res = await shopify_service.trigger_mock_sync(shop_id)
        print(f"   ✅ {sync_res.message}")
        
        # 2. Pipeline de nettoyage
        print("🧹 2/3 Nettoyage des données (OOS + IQR)...")
        forecast_service = ForecastingService(db)
        cleaning_res = await forecast_service.run_cleaning_pipeline(shop_id)
        print(f"   ✅ {cleaning_res.message}")
        
        # 3. Pipeline de prédiction
        print("📈 3/3 Calcul des prédictions (Run Rate + Stockout)...")
        prediction_res = await forecast_service.run_prediction_pipeline(shop_id)
        print(f"   ✅ {prediction_res.message}")
        
        await db.commit()
        print("\n✨ Power Sync terminée avec succès ! ✨")

if __name__ == "__main__":
    asyncio.run(run())
