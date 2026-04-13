import httpx
import asyncio

async def test_login():
    url = "http://localhost:8000/graphql"
    query = """
    mutation Login($input: LoginInput!) {
      login(input: $input) {
        token
      }
    }
    """
    variables = {
        "input": {
            "email": "dev@michi.com",
            "password": "password123"
        }
    }
    
    print(f"Testing login at {url}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                json={"query": query, "variables": variables},
                timeout=5.0
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())
