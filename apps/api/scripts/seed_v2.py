#!/usr/bin/env python3
"""
Seed script v2 — Compatible architecture hexagonale.
Crée un utilisateur demo + organisation par défaut.
Usage: python scripts/seed_v2.py
"""
import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from core.config import settings
from core.database import Base
import core.database.models  # noqa: F401
from core.database.models import User, Organization, OrganizationMember
from core.database.constants import UserRole
from core.security.hashing import hash_password

DEMO_EMAIL = "dev@michi.com"
DEMO_PASSWORD = "password123"
DEMO_ORG = "Michi Demo"
DEMO_SLUG = "michi-demo"


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Vérifier si l'user existe déjà
        result = await session.execute(select(User).where(User.email == DEMO_EMAIL))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"[SKIP] Utilisateur {DEMO_EMAIL} déjà présent.")
            await engine.dispose()
            return

        # Créer l'organisation
        org = Organization(
            id=uuid.uuid4(),
            name=DEMO_ORG,
            slug=DEMO_SLUG,
            plan="PRO",
            subscription_status="ACTIVE",
            settings={"currency": "EUR"},
        )
        session.add(org)
        await session.flush()

        # Créer l'utilisateur
        user = User(
            id=uuid.uuid4(),
            email=DEMO_EMAIL,
            first_name="Demo",
            last_name="User",
            hashed_password=hash_password(DEMO_PASSWORD),
            current_organization_id=org.id,
            preferences={},
        )
        session.add(user)
        await session.flush()

        # Créer le membership
        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=UserRole.ADMIN,
            permissions={},
        )
        session.add(member)
        await session.commit()

        print(f"[OK] Utilisateur créé : {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"[OK] Organisation     : {DEMO_ORG} (slug: {DEMO_SLUG})")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
