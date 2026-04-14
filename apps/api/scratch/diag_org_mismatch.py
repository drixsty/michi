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
            res = await conn.execute(text('SELECT email, current_organization_id FROM users'))
            users = res.fetchall()
            print(f"Users in DB: {len(users)}")
            for user in users:
                print(f"Email: {user.email} | Org: {user.current_organization_id}")
            
            res_inv = await conn.execute(text('SELECT email, organization_id, status FROM invitations'))
            invs = res_inv.fetchall()
            print(f"\nInvitations in DB: {len(invs)}")
            for inv in invs:
                print(f"Invite to: {inv.email} | Org: {inv.organization_id} | Status: {inv.status}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
