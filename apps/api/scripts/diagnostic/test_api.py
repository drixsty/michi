import requests
import json

def test_graphql():
    url = "http://localhost:8000/graphql"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MmFhNjkyMy1mZmU5LTQ4NTktODU4OS0xZTg0YmE2YTU0YTkiLCJleHAiOjE3NzYxMDgwMTV9.rAEmqb0hCqWdlSB2xjhiYiKHxCjaUlUQG5fuFaakzCo"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Test 1: Global (Omnichannel)
    query_all = {
        "query": """
        query GetFinancialOverview($storeId: ID, $channel: String) {
          financialOverview(storeId: $storeId, channel: $channel) {
            kpis { inventoryValueCost }
            topRisks { sku sourcePlatform }
            totalStock
            message
          }
        }
        """,
        "variables": {"storeId": None, "channel": "all"}
    }
    
    print("--- Testing Global ---")
    r = requests.post(url, json=query_all, headers=headers)
    print(r.json())
    
    # Test 2: Amazon
    query_amazon = {
        "query": query_all["query"],
        "variables": {"storeId": None, "channel": "amazon"}
    }
    print("\n--- Testing Amazon ---")
    r = requests.post(url, json=query_amazon, headers=headers)
    print(r.json())

if __name__ == "__main__":
    test_graphql()
