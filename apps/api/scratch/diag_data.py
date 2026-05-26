import asyncio
import sys
import os

# Fix console encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Add apps/api/src and apps/api to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from core.database import engine
from sqlalchemy import select
from core.database.models import User, Organization, Store, Product, Prediction

async def check():
    try:
        async with engine.connect() as conn:
            # Query users
            res_users = await conn.execute(select(User))
            users = res_users.all()
            print(f"=== USERS ({len(users)}) ===")
            for u in users:
                print(f"ID: {u.id} | Email: {u.email} | CurrentOrgID: {u.current_organization_id}")
                
            # Query organizations
            res_orgs = await conn.execute(select(Organization))
            orgs = res_orgs.all()
            print(f"\n=== ORGANIZATIONS ({len(orgs)}) ===")
            for o in orgs:
                print(f"ID: {o.id} | Name: {o.name} | Slug: {o.slug}")
                
            # Query stores
            res_stores = await conn.execute(select(Store))
            stores = res_stores.all()
            print(f"\n=== STORES ({len(stores)}) ===")
            for s in stores:
                print(f"ID: {s.id} | Name: {s.name} | OrgID: {s.organization_id} | Platform: {s.platform} | Connected: {s.connected}")
                
            # Query products count
            res_prods = await conn.execute(select(Product))
            prods = res_prods.all()
            print(f"\n=== PRODUCTS ({len(prods)}) ===")
            if prods:
                print(f"Total products: {len(prods)}")
                # Show first 5
                for p in prods[:5]:
                    print(f"  Prod ID: {p.id} | SKU: {p.sku} | Title: {p.title} | StoreID: {p.store_id} | Stock: {p.current_stock} | Cost: {p.cost_price}")
            
            # Query predictions count
            res_preds = await conn.execute(select(Prediction))
            preds = res_preds.all()
            print(f"\n=== PREDICTIONS ({len(preds)}) ===")
            if preds:
                print(f"Total predictions: {len(preds)}")
                for pr in preds[:5]:
                    print(f"  Pred ID: {pr.id} | ProdID: {pr.product_id} | RunRate: {pr.run_rate} | ReorderQty: {pr.reorder_quantity}")
                    
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check())
