import asyncio
from src.core.database import AsyncSessionLocal
from src.modules.auth.models import User
from src.core.security import create_access_token
from sqlalchemy import select
import src.modules.auth.models
import src.modules.inventory.models
import src.modules.forecasting.models

async def get_token():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.email == 'dev@michi.com'))
        u = res.scalars().first()
        if not u:
            print("User not found")
            return
        
        token = create_access_token(data={"sub": str(u.id)})
        print(f"TOKEN:{token}")

if __name__ == "__main__":
    asyncio.run(get_token())
