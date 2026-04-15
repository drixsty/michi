import os
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Manual env setup
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://michi:michi123@localhost:5433/michi_db")
os.environ.setdefault("SECRET_KEY", "dummy")
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

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

from modules.inventory.infrastructure.persistence.models import Store
from modules.intelligence.services.supplier_analysis import SupplierAnalysisService
from modules.auth.infrastructure.persistence.models import Invitation
from modules.forecasting.infrastructure.persistence.models import Prediction

async def run_analysis():
    print("=== Phase 2 : Analyse de l'historique Fournisseur ===")
    async with AsyncSessionLocal() as session:
        # Get the store
        stmt = select(Store).limit(1)
        store = (await session.execute(stmt)).scalar_one_or_none()
        
        if not store:
            print("Aucun store trouvé.")
            return
            
        service = SupplierAnalysisService(session)
        print(f"Lancement de l'analyse pour le store : {store.name}")
        
        results = await service.analyze_all_suppliers(store.id)
        await session.commit()
        
        for sid, m in results.items():
            print(f"Fournisseur {sid} :")
            print(f"  - Fiabilité : {m['reliability']*100:.1f}%")
            print(f"  - Retard moyen : {m['average_delay']:.2f} jours")
            print(f"  - Sigma LT : {m['lead_time_sigma']:.2f} jours")

if __name__ == "__main__":
    asyncio.run(run_analysis())
