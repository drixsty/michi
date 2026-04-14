import asyncio
import httpx
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_conflict_robust():
    print("--- Testing conflict: storeId(Shopify) + channel('amazon') ---")
    
    async with httpx.AsyncClient() as client:
        # 1. Login
        res = await client.post("http://localhost:8000/graphql", json={"query": "mutation Login($input: LoginInput!) { login(input: $input) { token } }", "variables": {"input": {"email": "dev@michi.com", "password": "michi123"}}})
        token = res.json()["data"]["login"]["token"]
        
        # 2. Get User/Org/Stores
        me_query = """
        query {
          me {
            id
            currentOrganization {
              id
              stores { id name platform }
            }
          }
        }
        """
        res = await client.post("http://localhost:8000/graphql", headers={"Authorization": f"Bearer {token}"}, json={"query": me_query})
        me_data = res.json()["data"]["me"]
        if not me_data or not me_data["currentOrganization"]:
            print("ERROR: User has no organization context!")
            return
            
        stores = me_data["currentOrganization"]["stores"]
        shopify_id = next((s["id"] for s in stores if s["platform"] == "SHOPIFY"), None)
        amazon_id = next((s["id"] for s in stores if s["platform"] == "AMAZON"), None)
        
        if not shopify_id or not amazon_id:
            print("ERROR: Missing required stores in Michi Corp")
            return

        # 3. Test Conflict
        # Case: Selected Store is Shopify, but user filters by Amazon channel
        overview_query = """
        query GetFinancialOverview($storeId: ID, $channel: String) {
          financialOverview(storeId: $storeId, channel: $channel) {
            kpis { inventoryValueCost }
            topRisks { sku }
            message
          }
        }
        """
        
        print(f"Querying Shopify Store ({shopify_id}) with Channel 'amazon'...")
        res = await client.post(
            "http://localhost:8000/graphql",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": overview_query, "variables": {"storeId": shopify_id, "channel": "amazon"}}
        )
        data = res.json()
        print("Response:", data)
        kpis = data["data"]["financialOverview"]["kpis"]
        print(f"KPIs Cost: {kpis['inventoryValueCost']}")
        print(f"Message: {data['data']['financialOverview']['message']}")

if __name__ == "__main__":
    asyncio.run(test_conflict_robust())
