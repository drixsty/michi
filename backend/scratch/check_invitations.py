import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.core.database import engine
from sqlalchemy import text

async def check():
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text('SELECT * FROM invitations'))
            rows = res.fetchall()
            print(f"Invitations in DB: {len(rows)}")
            for row in rows:
                print(row)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
