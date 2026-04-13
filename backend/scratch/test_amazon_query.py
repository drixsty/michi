import asyncio
import httpx
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_amazon_query():
    print("--- Testing financialOverview(channel='amazon') ---")
    
    # 1. Login to get token
    login_query = """
    mutation Login($input: LoginInput!) {
      login(input: $input) { token }
    }
    """
    
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "http://localhost:8000/graphql",
            json={"query": login_query, "variables": {"input": {"email": "dev@michi.com", "password": "michi123"}}}
        )
        token = res.json()["data"]["login"]["token"]
        
        # 2. Query Financial Overview
        overview_query = """
        query GetFinancialOverview($channel: String) {
          financialOverview(channel: $channel) {
            kpis { inventoryValueCost revenueAtRisk }
            topRisks { sku title riskValue sourcePlatform }
            activePlatforms
            capitalBreakdown { platform value }
          }
        }
        """
        
        res = await client.post(
            "http://localhost:8000/graphql",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": overview_query, "variables": {"channel": "amazon"}}
        )
        
        data = res.json()
        if "errors" in data:
            print("GraphQL Errors:", data["errors"])
            return

        overview = data["data"]["financialOverview"]
        print(f"KPIs: {overview['kpis']}")
        print(f"Top Risks found: {len(overview['topRisks'])}")
        print(f"Active Platforms in response: {overview['activePlatforms']}")
        print(f"Capital Breakdown: {overview['capitalBreakdown']}")
        
        if len(overview['topRisks']) > 0:
            print(f"First Risk: {overview['topRisks'][0]['title']} (Platform: {overview['topRisks'][0]['sourcePlatform']})")

if __name__ == "__main__":
    asyncio.run(test_amazon_query())
