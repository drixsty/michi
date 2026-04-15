import sys
import os
import asyncio
from sqlalchemy import text

# Add the API src to path
sys.path.append(os.path.abspath('apps/api/src'))

from core.database import SessionLocal

async def check_db():
    print("Connecting to database...")
    try:
        async with SessionLocal() as db:
            # Check products
            res_p = await db.execute(text('SELECT count(*) FROM products'))
            count_p = res_p.scalar()
            print(f"Products count: {count_p}")
            
            # Check predictions
            res_pr = await db.execute(text('SELECT count(*) FROM predictions'))
            count_pr = res_pr.scalar()
            print(f"Predictions count: {count_pr}")
            
            if count_pr > 0:
                res_sample = await db.execute(text('SELECT product_id, predicted_stockout_date FROM predictions LIMIT 5'))
                print("Sample predictions:")
                for row in res_sample.all():
                    print(f"  Product: {row[0]}, Date: {row[1]}")
            else:
                print("No predictions found. Intelligence worker might not have run or failed.")
                
    except Exception as e:
        print(f"Error checking DB: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())
