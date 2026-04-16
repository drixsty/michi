import asyncio
import httpx
import json

GRAPHQL_URL = "http://localhost:8000/graphql"

LOGIN_MUTATION = """
mutation Login($input: LoginInput!) {
  login(input: $input) {
    token
    user {
      id
      email
      currentOrganizationId
    }
  }
}
"""

SOURCES_QUERY = """
query GetSources {
  sources {
    id
    name
    platform
  }
}
"""

async def verify_auth_fix():
    print("Connecting to Michi API...")
    
    # 1. Login
    async with httpx.AsyncClient() as client:
        print(f"Attempting login for dev@michi.com...")
        login_vars = {
            "input": {
                "email": "dev@michi.com",
                "password": "password123"
            }
        }
        
        try:
            resp = await client.post(
                GRAPHQL_URL, 
                json={"query": LOGIN_MUTATION, "variables": login_vars},
                timeout=10.0
            )
            
            if resp.status_code != 200:
                print(f"FAILED: Login request returned {resp.status_code}")
                print(resp.text)
                return

            data = resp.json()
            if "errors" in data:
                print("FAILED: Login mutation returned errors:")
                print(json.dumps(data["errors"], indent=2))
                return
            
            token = data["data"]["login"]["token"]
            user = data["data"]["login"]["user"]
            print("SUCCESS: Logged in!")
            print(f"  User ID: {user['id']}")
            print(f"  Current Org ID: {user['currentOrganizationId']}")
            
            # 2. Query Sources (Protected)
            print("\nAttempting to query protected 'sources' field...")
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.post(
                GRAPHQL_URL,
                json={"query": SOURCES_QUERY},
                headers=headers,
                timeout=10.0
            )
            
            if resp.status_code != 200:
                print(f"FAILED: Sources request returned {resp.status_code}")
                return

            data = resp.json()
            if "errors" in data:
                print("FAILED: Sources query returned errors:")
                print(json.dumps(data["errors"], indent=2))
                return
            
            sources = data["data"]["sources"]
            print(f"SUCCESS: Found {len(sources)} sources!")
            for s in sources:
                print(f"  - {s['name']} ({s['platform']}) [ID: {s['id']}]")
            
            print("\nALL AUTH CHECKS PASSED ✅")

        except Exception as e:
            print(f"ERROR connecting to API: {e}")
            print("Is the API running? (Check terminal with ID: api)")

if __name__ == "__main__":
    asyncio.run(verify_auth_fix())
