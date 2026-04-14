import requests
import json

def test_cors():
    url = "http://localhost:8000/graphql"
    origin = "http://localhost:3000"
    
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, Authorization"
    }
    
    print(f"Testing OPTIONS {url} with Origin: {origin}")
    try:
        response = requests.options(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Response Headers:")
        for k, v in response.headers.items():
            if "access-control" in k.lower():
                print(f"  {k}: {v}")
        
        if "Access-Control-Allow-Origin" not in response.headers:
            print("\n!!! MISSING Access-Control-Allow-Origin !!!")
        else:
            print(f"\nAllowed Origin: {response.headers.get('Access-Control-Allow-Origin')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cors()
