from sqlalchemy import create_all, select, create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
import src.modules.auth.models
from src.modules.auth.models import User

def check_user_sync():
    # Convert async URL to sync
    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    user = session.query(User).filter(User.email == 'dev@michi.com').first()
    if user:
        print(f"User Found: {user.email}")
        print(f"Current Org ID: {user.current_organization_id}")
    else:
        print("User NOT found")
    
    session.close()

if __name__ == "__main__":
    check_user_sync()
