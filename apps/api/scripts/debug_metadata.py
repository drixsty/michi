import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from michi_core.database import Base
# Imports explicit
from src.modules.auth.models import User, Organization, OrganizationMember
from src.modules.inventory.models import Product, Store

print("Tables in Base.metadata:")
for table in Base.metadata.tables.keys():
    print(f" - {table}")

if 'users' in Base.metadata.tables and 'organization_members' in Base.metadata.tables:
    print("SUCCESS: Both tables are registered.")
else:
    print("FAILURE: Missing tables.")
