import requests
import uuid

endpoint = "http://localhost:8001/graphql"

# Token simulation (needs to be a valid one from main API if verification is on,
# but we aligned the secret so we can sign one here if needed)
# For now, let's just try to call without token to see if it fails (as expected)
# OR we can just bypass it by mocking the request context in a unit test,
# but a real integration test is better.

def get_token():
    from jose import jwt
    payload = {"sub": "test_user", "org_id": "test_org", "email": "test@test.com"}
    return jwt.encode(payload, "secret", algorithm="HS256")

token = get_token()
headers = {"Authorization": f"Bearer {token}"}

def run_query(query, variables=None):
    response = requests.post(endpoint, json={'query': query, 'variables': variables}, headers=headers)
    return response.json()

print("--- Testing Michi Assistant History ---")

# 1. Send Message
send_mutation = """
mutation Send($c: String!) {
  sendMessage(content: $c) {
    reply
    sessionId
  }
}
"""
print("1. Sending message...")
res = run_query(send_mutation, {"c": "Test message for history"})
print(f"Response: {res}")

if "data" in res and res["data"]["sendMessage"]:
    session_id = res["data"]["sendMessage"]["sessionId"]
    print(f"Session ID created: {session_id}")

    # 2. List Sessions
    list_query = """
    query {
      listSessions {
        sessionId
        lastMessage
      }
    }
    """
    print("\n2. Listing sessions...")
    res = run_query(list_query)
    print(f"Sessions: {res}")

    # 3. Get History
    history_query = """
    query History($sid: String!) {
      getChatHistory(sessionId: $sid) {
        role
        content
      }
    }
    """
    print("\n3. Getting history for session...")
    res = run_query(history_query, {"sid": session_id})
    print(f"History: {res}")

    # 4. Truncate (Edit)
    # We should have 2 messages (user + assistant)
    truncate_mutation = """
    mutation Truncate($sid: String!, $idx: Int!) {
      truncateSession(sessionId: $sid, index: $idx)
    }
    """
    print("\n4. Truncating session at index 0 (deletes everything and restarts)...")
    res = run_query(truncate_mutation, {"sid": session_id, "idx": 0})
    print(f"Truncate result: {res}")

    # 5. Delete
    delete_mutation = """
    mutation Delete($sid: String!) {
      deleteSession(sessionId: $sid)
    }
    """
    print("\n5. Deleting session...")
    res = run_query(delete_mutation, {"sid": session_id})
    print(f"Delete result: {res}")

else:
    print("Failed to start session. Check if assistant is running at :8001")
