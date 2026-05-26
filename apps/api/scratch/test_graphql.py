import asyncio
import sys
import os
import httpx

async def test():
    # Query GET_FINANCIAL_OVERVIEW
    query = """
    query GetFinancialOverview($storeId: ID, $channel: String) {
      financialOverview(storeId: $storeId, channel: $channel) {
        kpis {
          inventoryValueCost
          inventoryValueSale
          revenueAtRisk
          stockCoverageAvgDays
          currency
          isMutualized
        }
        topRisks {
          productId
          sku
          title
          riskValue
          stockoutDate
          reorderQuantity
          daysOfStock
          runRate
          supplierId
          sourcePlatform
          costPrice
          salePrice
        }
        totalRunRate
        totalStock
        healthScore
        activePlatforms
        capitalBreakdown {
          platform
          value
        }
        message
      }
    }
    """
    
    url = "http://localhost:8000/graphql"
    
    # We need a valid JWT token of dev@michi.com!
    # Let's call the login mutation first to get a token!
    login_mutation = """
    mutation {
      login(input: {
        email: "dev@michi.com"
        password: "password123"
      }) {
        token
      }
    }
    """
    
    async with httpx.AsyncClient() as client:
        try:
            # Login
            resp = await client.post(url, json={"query": login_mutation})
            login_data = resp.json()
            if "errors" in login_data:
                print("Login failed:", login_data["errors"])
                return
            
            token = login_data["data"]["login"]["token"]
            print("Successfully logged in, got token.")
            
            # Run query
            headers = {"Authorization": f"Bearer {token}"}
            resp_query = await client.post(url, json={"query": query, "variables": {}}, headers=headers)
            print("GraphQL status:", resp_query.status_code)
            result = resp_query.json()
            if "errors" in result:
                print("Query returned errors:")
                for err in result["errors"]:
                    print("  -", err.get("message"))
            else:
                print("Query Succeeded!")
                print("Result keys:", result["data"]["financialOverview"].keys())
                print("Overview:", result["data"]["financialOverview"])
                
        except Exception as e:
            print("HTTP request failed:", e)

if __name__ == "__main__":
    asyncio.run(test())
