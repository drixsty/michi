import asyncio
import sys
import os

# Fix console encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Add apps/api/src and apps/api to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from core.database import engine
from core.database.connection import AsyncSessionLocal
from modules.auth.infrastructure.repositories import SQLAlchemyUserRepository
from modules.inventory.infrastructure.repositories.store_repository import SQLAlchemyStoreRepository
from modules.inventory.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
from modules.forecasting.infrastructure.repositories.prediction_repository import SQLAlchemyPredictionRepository
from modules.decisions.application.decisions_service import ApplicationDecisionsService

async def test():
    async with AsyncSessionLocal() as db:
        user_repo = SQLAlchemyUserRepository(db)
        store_repo = SQLAlchemyStoreRepository(db)
        product_repo = SQLAlchemyProductRepository(db)
        prediction_repo = SQLAlchemyPredictionRepository(db)
        
        service = ApplicationDecisionsService(
            user_repo=user_repo,
            store_repo=store_repo,
            product_repo=product_repo,
            prediction_repo=prediction_repo
        )
        
        # User dev@michi.com
        user_id = "c946f5b8-662a-4808-8acf-d58b4dab49bc"
        
        try:
            overview = await service.get_overview(user_id=user_id)
            print("=== OVERVIEW SUCCESS ===")
            print(f"Message: {overview.message}")
            print(f"Health score: {overview.health_score}")
            print(f"KPIs Cost: {overview.kpis.inventory_value_cost}")
            print(f"KPIs Sale: {overview.kpis.inventory_value_sale}")
            print(f"KPIs Risk: {overview.kpis.revenue_at_risk}")
            print(f"KPIs Coverage Days: {overview.kpis.stock_coverage_avg_days}")
            print(f"Top Risks: {len(overview.top_risks)}")
            print(f"Capital Breakdown: {overview.capital_breakdown}")
            print(f"Active platforms: {overview.active_platforms}")
        except Exception as e:
            print("=== OVERVIEW ERROR ===")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
