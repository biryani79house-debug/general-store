#!/usr/bin/env python3
"""
Script to grant admin permissions to user 'raza123'
"""

import requests
import json
import sys

# Railway URL
BASE_URL = "https://web-production-9d240.up.railway.app"

def main():
    print("🔧 Granting admin permissions to user 'raza123'")

    # Login first to get token
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "raza123",
        "password": "123456"
    })

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print("Response:", login_response.text)
        return

    token = login_response.json().get("access_token")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Get user ID for 'raza123'
    users_response = requests.get(f"{BASE_URL}/users", headers=headers)

    if users_response.status_code != 200:
        print(f"❌ Failed to get users: {users_response.status_code}")
        print("Response:", users_response.text)
        return

    users = users_response.json()
    admin_user = None

    for user in users:
        if user["username"] == "raza123":
            admin_user = user
            break

    if not admin_user:
        print("❌ Admin user 'raza123' not found")
        return

    admin_user_id = admin_user["id"]
    print(f"👤 Found admin user: ID {admin_user_id}, Username: {admin_user['username']}")

    # Grant all admin permissions
    admin_permissions = {
        "sales": True,
        "purchase": True,
        "create_product": True,
        "delete_product": True,
        "sales_ledger": True,
        "purchase_ledger": True,
        "stock_ledger": True,
        "profit_loss": True,
        "opening_stock": True,
        "user_management": True
    }

    update_response = requests.put(f"{BASE_URL}/users/{admin_user_id}",
                                   json=admin_permissions,
                                   headers=headers)

    if update_response.status_code == 200:
        updated_user = update_response.json()
        print("✅ Admin permissions granted successfully!")
        print(f"   User: {updated_user['username']}")
        print(f"   Permissions: {updated_user.get('permissions', [])}")
    else:
        print(f"❌ Failed to update permissions: {update_response.status_code}")
        print("Response:", update_response.text)

if __name__ == "__main__":
    main()
