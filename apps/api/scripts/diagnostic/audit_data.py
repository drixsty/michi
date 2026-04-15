import asyncio
import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import AsyncSessionLocal
from modules.auth.models import User
from modules.shopify.models import Product
from modules.forecasting.models import Prediction
from sqlalchemy import select, func

async def run():
    async with AsyncSessionLocal() as db:
        # Trouver un shop
        result = await db.execute(select(User).where(User.email == 'dev@michi.com'))
        user = result.scalars().first()
        
        if not user:
            print("❌ Aucun utilisateur 'dev@michi.com' trouvé.")
            return
            
        shop_id = str(user.shop_id)
        print(f"🔍 Audit des données pour le shop : {shop_id}")
        
        # 1. Compte produits
        p_count = (await db.execute(select(func.count(Product.id)).where(Product.shop_id == shop_id))).scalar()
        print(f"📦 Produits : {p_count}")
        
        # 2. Compte prédictions
        pred_count = (await db.execute(select(func.count(Prediction.id)).where(Prediction.product_id.in_(
            select(Product.id).where(Product.shop_id == shop_id)
        )))).scalar()
        print(f"📈 Prédictions : {pred_count}")
        
        if p_count > 0 and pred_count == 0:
            print("\n💡 Analyse : Les produits sont synchronisés (Sync Shopify OK),")
            print("   MAIS la pipeline de prédiction n'a pas encore été lancée.")
        elif p_count == 0:
            print("\n❌ Analyse : La synchronisation a échoué (0 produits).")
        else:
            print("\n✅ Analyse : Toutes les données sont présentes en base.")

if __name__ == "__main__":
    asyncio.run(run())
