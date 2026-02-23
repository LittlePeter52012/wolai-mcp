import requests
import json
import sys

# Credentials via environment variables (never hardcode secrets!)
import os
APP_ID = os.environ.get("WOLAI_APP_ID", "")
APP_SECRET = os.environ.get("WOLAI_APP_SECRET", "")
BASE_URL = "https://openapi.wolai.com/v1"
ROOT_ID = os.environ.get("WOLAI_ROOT_ID", "")

if not APP_ID or not APP_SECRET:
    print("Error: WOLAI_APP_ID and WOLAI_APP_SECRET must be set as environment variables.")
    print("Example: export WOLAI_APP_ID=your_id && export WOLAI_APP_SECRET=your_secret")
    sys.exit(1)

def get_token():
    url = f"{BASE_URL}/token"
    payload = {"appId": APP_ID, "appSecret": APP_SECRET}
    response = requests.post(url, json=payload)
    return response.json()["data"]["app_token"]

def test_workflow():
    print("--- 1. Testing Authentication ---")
    token = get_token()
    headers = {"Authorization": token, "Content-Type": "application/json"}
    print(f"Token acquired: {token[:10]}...")

    print(f"\n--- 2. Testing Root Page Info ({ROOT_ID}) ---")
    res = requests.get(f"{BASE_URL}/blocks/{ROOT_ID}", headers=headers)
    if res.status_code == 200:
        root_data = res.json().get("data", {})
        print(f"Root Title: {root_data.get('content', 'No Content')}")
    else:
        print(f"Error fetching root: {res.text}")
        return

    print("\n--- 3. Testing Child Listing ---")
    res = requests.get(f"{BASE_URL}/blocks/{ROOT_ID}/children", headers=headers)
    if res.status_code == 200:
        children = res.json().get("data", [])
        print(f"Found {len(children)} children:")
        for child in children[:5]:
            print(f"- [{child.get('type')}] {child.get('content', '(No Title)')} (ID: {child.get('id')})")
        
        if not children:
            print("No children found. Is the ID correct or does the app have permission to read this page?")
    else:
        print(f"Error listing children: {res.text}")

if __name__ == "__main__":
    try:
        test_workflow()
    except Exception as e:
        print(f"Test failed with error: {e}")
