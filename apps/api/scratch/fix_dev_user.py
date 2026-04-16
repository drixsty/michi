import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
SRC_PATH = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))

# Load .env explicitly for Pydantic to pick up (if needed, although Pydantic does it too)
load_dotenv(Path(__file__).parent.parent / ".env")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from core.config import settings
from core.database.models import User, OrganizationMember, Organization
from core.security.hashing import hash_password
from core.database.constants import UserRole

DEMO_EMAIL = "dev@michi.com"
NEW_PASSWORD = "password123"

async def fix_dev_user():
    print(f"Connecting to database: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # 1. Find the user
        result = await session.execute(select(User).where(User.email == DEMO_EMAIL))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User {DEMO_EMAIL} not found. Creating...")
            user = User(
                email=DEMO_EMAIL,
                first_name="Dev",
                last_name="Michi",
                hashed_password=hash_password(NEW_PASSWORD),
                is_active=True
            )
            session.add(user)
            await session.flush()
        else:
            print(f"User {DEMO_EMAIL} found. Resetting password...")
            user.hashed_password = hash_password(NEW_PASSWORD)
            user.is_active = True
        
        # 2. Check organizations
        member_res = await session.execute(
            select(OrganizationMember).where(OrganizationMember.user_id == user.id)
        )
        member = member_res.scalar_one_or_none()
        
        if not member:
            print("No organization membership found for dev user. Creating demo organization...")
            # Find or create a demo org
            org_res = await session.execute(select(Organization).limit(1))
            org = org_res.scalar_one_or_none()
            
            if not org:
                org = Organization(name="Michi Development", slug="dev-org")
                session.add(org)
                await session.flush()
            
            member = OrganizationMember(
                organization_id=org.id,
                user_id=user.id,
                role=UserRole.ADMIN
            )
            session.add(member)
            user.current_organization_id = org.id
            print(f"Linked to organization: {org.name} ({org.id})")
        else:
            print(f"Found existing membership for organization ID: {member.organization_id}")
            if not user.current_organization_id:
                user.current_organization_id = member.organization_id
                print("Set current_organization_id to existing membership.")

        await session.commit()
        print("Final state:")
        print(f"  User ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Current Org ID: {user.current_organization_id}")
        print("Successfully fixed dev user.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_dev_user())
