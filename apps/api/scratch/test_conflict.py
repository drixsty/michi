import asyncio
import httpx
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_conflict():
    print("--- Testing conflict: storeId(Shopify) + channel('amazon') ---")
    
    # 1. Login
    login_query = """
    mutation Login($input: LoginInput!) { login(input: $input) { token } }
    """
    async with httpx.AsyncClient() as client:
        res = await client.post("http://localhost:8000/graphql", json={"query": login_query, "variables": {"input": {"email": "dev@michi.com", "password": "michi123"}}})
        token = res.json()["data"]["login"]["token"]
        
        # 2. Get Stores
        stores_query = "query { me { currentOrganization { stores { id name platform } } } }"
        res = await client.post("http://localhost:8000/graphql", headers={"Authorization": f"Bearer {token}"}, json={"query": stores_query})
        stores = res.json()["data"]["me"]["currentOrganization"]["stores"]
        
        shopify_id = next(s["id"] for s in stores if s["platform"] == "SHOPIFY")
        amazon_id = next(s["id"] for s in stores if s["platform"] == "AMAZON")
        
        # 3. Test Conflict
        overview_query = """
        query GetFinancialOverview($storeId: ID, $channel: String) {
          financialOverview(storeId: $storeId, channel: $channel) {
            kpis { inventoryValueCost }
            topRisks { sku }
          }
        }
        """
        
        print(f"Querying Shopify Store ({shopify_id}) with Channel 'amazon'...")
        res = await client.post(
            "http://localhost:8000/graphql",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": overview_query, "variables": {"storeId": shopify_id, "channel": "amazon"}}
        )
        print("Response:", res.json())

if __name__ == "__main__":
    asyncio.run(test_conflict())
