import sys
import os
import asyncio
from datetime import date, timedelta
from uuid import UUID

# Add the API src to path
sys.path.append(os.path.abspath('apps/api/src'))

from core.database import SessionLocal
from modules.forecasting.application.service import ForecastingService
from modules.forecasting.infrastructure.repositories.cleaned_demand_repository import SQLAlchemyCleanedDemandRepository
from modules.forecasting.infrastructure.repositories.prediction_repository import SQLAlchemyPredictionRepository
from modules.inventory.infrastructure.repositories.product_repository import SQLAlchemyProductRepository

async def debug_product_forecast(product_id_str):
    pid = UUID(product_id_str)
    print(f"--- Debugging Forecast for Product: {pid} ---")
    
    async with SessionLocal() as db:
        # Repositories
        cd_repo = SQLAlchemyCleanedDemandRepository(db)
        p_repo = SQLAlchemyPredictionRepository(db)
        prod_repo = SQLAlchemyProductRepository(db)
        
        # Service
        service = ForecastingService(cd_repo, p_repo)
        
        # 1. Check product data
        product = await prod_repo.get_by_id(pid)
        if not product:
            print("Product not found!")
            return
        print(f"Product: {product.title} (SKU: {product.sku})")
        print(f"Current Stock: {product.current_stock}")
        print(f"Lead Time: {product.lead_time}, MOQ: {product.moq}")
        
        # 2. Check Cleaned Demand
        demands = await cd_repo.list_by_product(pid, limit=90)
        print(f"Cleaned Demand points: {len(demands)}")
        if demands:
            avg_sold = sum(d.corrected_units_sold for d in demands) / len(demands)
            print(f"Average corrected units sold (last {len(demands)} pts): {avg_sold:.4f}")
        
        # 3. Simulate Run Rate Calculation
        # Assuming the service uses the last 30 days for run rate
        recent_demands = demands[:30]
        if recent_demands:
            run_rate = sum(d.corrected_units_sold for d in recent_demands) / len(recent_demands)
            print(f"Calculated Run Rate (30d): {run_rate:.4f}")
            
            if run_rate > 0:
                days_of_stock = product.current_stock / run_rate
                stockout_date = date.today() + timedelta(days=days_of_stock)
                print(f"Manually Estimated Stockout: {stockout_date} (in {days_of_stock:.1f} days)")
            else:
                print("Run rate is 0! No stockout can be predicted.")
        else:
            print("No demand data found to calculate run rate.")

        # 4. Check existing prediction in DB
        pred = await p_repo.get_by_product(pid)
        if pred:
            print(f"Database Prediction:")
            print(f"  Run Rate: {pred.run_rate}")
            print(f"  Stockout Date: {pred.predicted_stockout_date}")
            print(f"  Reorder Qty: {pred.reorder_quantity}")
        else:
            print("No prediction record found in database.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_forecast.py <product_id>")
        # Example from logs
        target = "7b8d51d2-b1b7-496c-8ead-4af266047305"
    else:
        target = sys.argv[1]
        
    asyncio.run(debug_product_forecast(target))
