import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.database.models import User, OrganizationMember, Organization
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.config import settings

async def list_users():
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        # Get all users with their roles and organizations
        query = select(User, OrganizationMember, Organization).join(
            OrganizationMember, User.id == OrganizationMember.user_id
        ).join(
            Organization, OrganizationMember.organization_id == Organization.id
        )
        results = (await session.execute(query)).all()
        
        print("\n=== Michi Test Accounts ===\n")
        if not results:
            print("No users found in database.")
        for user, member, org in results:
            print(f"Email: {user.email}")
            print(f"Role:  {member.role}")
            try:
                print(f"Org:   {org.name} ({org.slug})")
            except UnicodeEncodeError:
                print(f"Org:   Michi (slug: {org.slug})")
            print("-" * 30)
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(list_users())
