#!/usr/bin/env python3
"""
Test login specifically for raza123 user
"""

import requests
import json

# Configuration
BASE_URL = "https://web-production-9d240.up.railway.app"

def test_raza123_login():
    print("🔐 Testing login for user 'raza123' with password '123456'")
    print("=" * 60)

    session = requests.Session()

    try:
        # Test basic health first
        print("1. Testing health endpoint...")
        response = session.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        print("✅ Health check passed")

        # Try to login
        print("\n2. Attempting login...")
        login_data = {
            "username": "raza123",
            "password": "123456"
        }

        response = session.post(f"{BASE_URL}/auth/login", json=login_data)

        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")

        if response.status_code == 200:
            login_result = response.json()
            print("✅ Login successful!")
            print(f"   User: {login_result.get('user', {}).get('username')}")
            permissions = login_result.get('user', {}).get('permissions', [])
            print(f"   Permissions: {permissions}")
            return True
        else:
            print("❌ Login failed!")
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"   Error: {error_detail}")
            return False

    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_raza123_login()
    if success:
        print("\n🎉 Login test passed!")
    else:
        print("\n💥 Login test failed!")
