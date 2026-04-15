import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.core.security import hash_password
from src.modules.auth.models import User, Organization, OrganizationMember, UserRole

async def check_and_fix_user():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == "dev@michi.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("User dev@michi.com not found!")
            return
            
        print(f"User ID: {user.id}")
        print(f"Current Password Hash: {user.hashed_password[:10]}...")
        
        # Update password to michi123 to match user request
        user.hashed_password = hash_password("michi123")
        print("Updated password to 'michi123'")
        
        # Check organizations
        from sqlalchemy.orm import selectinload
        result = await session.execute(
            select(User).where(User.id == user.id)
            .options(selectinload(User.organizations).selectinload(OrganizationMember.organization))
        )
        user = result.scalar_one()
        
        print(f"Organizations: {len(user.organizations)}")
        
        if len(user.organizations) == 0:
            print("Fixing: Adding default organization...")
            org = Organization(name="Default Org", slug=f"default-{uuid.uuid4().hex[:6]}")
            session.add(org)
            await session.flush()
            
            member = OrganizationMember(user_id=user.id, organization_id=org.id, role=UserRole.ADMIN)
            session.add(member)
            user.current_organization_id = org.id
            print(f"Added Org: {org.name} (ID: {org.id})")
        else:
            if not user.current_organization_id:
                user.current_organization_id = user.organizations[0].organization_id
                print(f"Set current_organization_id to {user.current_organization_id}")
        
        await session.commit()
        print("Changes committed successfully.")

if __name__ == "__main__":
    asyncio.run(check_and_fix_user())
