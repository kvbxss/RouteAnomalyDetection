#!/usr/bin/env python3
"""
Test authentication endpoint
"""
import requests
import json

API_BASE = "http://127.0.0.1:8000"

def test_login():
    """Test login with admin credentials"""
    url = f"{API_BASE}/auth/token/"
    data = {
        "username": "admin",
        "password": "admin123"
    }

    print(f"Testing POST to: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"}
        )

        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))

        if response.status_code == 200:
            print("\n✅ Login successful!")
            return response.json()
        else:
            print(f"\n❌ Login failed with status {response.status_code}")
            return None

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

def test_with_wrong_credentials():
    """Test login with wrong credentials"""
    url = f"{API_BASE}/auth/token/"
    data = {
        "username": "admin",
        "password": "wrongpassword"
    }

    print(f"\n{'='*60}")
    print("Testing with WRONG credentials:")
    print(f"Data: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Authentication Test")
    print("=" * 60)

    # Test with correct credentials
    tokens = test_login()

    # Test with wrong credentials
    test_with_wrong_credentials()

    if tokens:
        print(f"\n{'='*60}")
        print("Testing protected endpoint with token:")

        response = requests.get(
            f"{API_BASE}/api/flights/",
            headers={
                "Authorization": f"Bearer {tokens['access']}",
                "Content-Type": "application/json"
            }
        )

        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got {data.get('count', 0)} flights")
        else:
            print(f"Response: {response.text[:200]}")
