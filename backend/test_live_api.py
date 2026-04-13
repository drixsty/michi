import http.client
import json

def test_graphql():
    conn = http.client.HTTPConnection("localhost", 8000)
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MmFhNjkyMy1mZmU5LTQ4NTktODU4OS0xZTg0YmE2YTU0YTkiLCJleHAiOjE3NzYxMDgwMTV9.rAEmqb0hCqWdlSB2xjhiYiKHxCjaUlUQG5fuFaakzCo"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Global (Omnichannel)
    payload_all = {
        "query": "query { financialOverview(storeId: null, channel: null) { totalStock kpis { inventoryValueCost } activePlatforms message } }",
    }
    
    print("--- Testing Global ---")
    conn.request("POST", "/graphql", json.dumps(payload_all), headers)
    r1 = conn.getresponse()
    print(r1.status, r1.reason)
    print(r1.read().decode())
    
    # Amazon
    payload_amazon = {
        "query": "query { financialOverview(storeId: null, channel: \"amazon\") { totalStock kpis { inventoryValueCost } activePlatforms message } }",
    }
    print("\n--- Testing Amazon ---")
    conn.request("POST", "/graphql", json.dumps(payload_amazon), headers)
    r2 = conn.getresponse()
    print(r2.status, r2.reason)
    print(r2.read().decode())

if __name__ == "__main__":
    test_graphql()
