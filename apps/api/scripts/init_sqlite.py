import asyncio
import sys
from pathlib import Path

# Add src/ to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from core.config.settings import settings
from core.database import Base
import core.database.models  # Ensures all models register on Base.metadata

async def init_sqlite():
    if not settings.DATABASE_URL.startswith("sqlite"):
        print(f"Skipping SQLite initialization since DATABASE_URL is: {settings.DATABASE_URL}")
        return

    print(f"Initializing SQLite database at: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        print("Creating all tables from metadata...")
        await conn.run_sync(Base.metadata.create_all)
        
        print("Creating alembic_version table...")
        await conn.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)"))
        
        print("Setting schema version to head (5f8a9c8f0d5b)...")
        # Clear any existing version
        await conn.execute(text("DELETE FROM alembic_version"))
        # Insert current head revision
        await conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('5f8a9c8f0d5b')"))

        # Create triggers for SQLite immutability
        print("Creating support_audit_logs immutability triggers...")
        await conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS prevent_update_audit_logs
            BEFORE UPDATE ON support_audit_logs
            BEGIN
                SELECT RAISE(FAIL, 'Updates not allowed on support_audit_logs');
            END;
        """))
        await conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS prevent_delete_audit_logs
            BEFORE DELETE ON support_audit_logs
            BEGIN
                SELECT RAISE(FAIL, 'Deletes not allowed on support_audit_logs');
            END;
        """))
        
    await engine.dispose()
    print("SQLite Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_sqlite())
