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
            # Check Organizations
            res_orgs = await conn.execute(text('SELECT id, name FROM organizations'))
            orgs = res_orgs.fetchall()
            print(f"Organizations in DB: {len(orgs)}")
            for org in orgs:
                print(f"  ID: {org.id} | Name: {org.name}")
            
            # Check Users
            res_users = await conn.execute(text('SELECT email, current_organization_id FROM users'))
            users = res_users.fetchall()
            print(f"\nUsers and their CURRENT org:")
            for user in users:
                print(f"  {user.email} -> {user.current_organization_id}")
            
            # Check Memberships
            res_members = await conn.execute(text('SELECT organization_id, user_id, role FROM organization_members'))
            members = res_members.fetchall()
            print(f"\nMemberships in DB: {len(members)}")
            for m in members:
                print(f"  User: {m.user_id} | Org: {m.organization_id} | Role: {m.role}")

            # Check Invitations for those orgs
            res_inv = await conn.execute(text('SELECT email, organization_id, status FROM invitations'))
            invs = res_inv.fetchall()
            print(f"\nInvitations in DB: {len(invs)}")
            for i in invs:
                print(f"  Invite: {i.email} | Org: {i.organization_id} | Status: {i.status}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
