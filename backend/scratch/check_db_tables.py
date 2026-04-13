import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.core.database import engine
from sqlalchemy import inspect

async def check():
    try:
        async with engine.connect() as conn:
            tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
            print(f"Tables in DB: {tables}")
            
            from src.modules.auth.models import Base
            print(f"Models in metadata: {Base.metadata.tables.keys()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
