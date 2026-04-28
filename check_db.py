import sqlite3
import os

db_path = "apps/api/michi.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT title, sku, store_id FROM products LIMIT 10;")
    rows = cursor.fetchall()
    print("Products found:")
    for row in rows:
        print(f"Title: {row[0]}, SKU: {row[1]}, StoreID: {row[2]}")
    
    cursor.execute("SELECT id, organization_id, platform FROM stores;")
    stores = cursor.fetchall()
    print("\nStores found:")
    for s in stores:
        print(f"ID: {s[0]}, OrgID: {s[1]}, Platform: {s[2]}")
    conn.close()
else:
    print(f"Database not found at {db_path}")
