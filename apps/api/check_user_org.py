import asyncio
from src.core.database import AsyncSessionLocal
from src.modules.auth.models import User
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.email == 'dev@michi.com'))
        u = res.scalars().first()
        print(f"User Org ID: {u.current_organization_id}")

if __name__ == "__main__":
    asyncio.run(run())
