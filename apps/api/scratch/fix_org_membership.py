import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.core.database import engine
from sqlalchemy import text

async def fix():
    target_org_id = "b5295741-d3d5-4517-91ce-73279ce7aeca" # Michi
    email = "dev@michi.com"
    
    try:
        async with engine.begin() as conn:
            # 1. Get user_id
            res = await conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email})
            user = res.fetchone()
            if not user:
                print(f"Error: User {email} not found")
                return
            
            user_id = user.id
            print(f"User {email} found with ID: {user_id}")
            
            # 2. Update current_organization_id in users table
            await conn.execute(
                text("UPDATE users SET current_organization_id = :org_id WHERE id = :user_id"),
                {"org_id": target_org_id, "user_id": user_id}
            )
            print(f"Updated current_organization_id for {email} to {target_org_id}")
            
            # 3. Check if membership exists, otherwise create it
            res_mem = await conn.execute(
                text("SELECT role FROM organization_members WHERE user_id = :user_id AND organization_id = :org_id"),
                {"user_id": user_id, "org_id": target_org_id}
            )
            member = res_mem.fetchone()
            
            if not member:
                print(f"Creating membership for {email} in organization {target_org_id}")
                await conn.execute(
                    text("INSERT INTO organization_members (user_id, organization_id, role, permissions) VALUES (:user_id, :org_id, 'ADMIN', '{}')"),
                    {"user_id": user_id, "org_id": target_org_id}
                )
            else:
                print(f"Membership already exists for {email} (Role: {member.role})")
            
            # 4. Cleanup other org memberships for dev@michi.com if they are causing confusion?
            # Better not touch them, just ensure the current one is correct.
            
            print("\nSUCCESS: Data synchronization complete!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix())
