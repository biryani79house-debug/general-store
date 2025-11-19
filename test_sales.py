#!/usr/bin/env python3
"""Test script to simulate sales transaction from index.html"""

import requests
import json

# Local server URL (update based on which server is running)
BASE_URL = "http://127.0.0.1:8001"  # Local development

def get_auth_token():
    """Authenticate and get token for a test user"""
    # Try different common usernames/passwords
    users_to_try = [
        {"username": "raza123", "password": "123456"},
        {"username": "testuser", "password": "testpass"},
        {"username": "admin", "password": "admin"}
    ]

    for user in users_to_try:
        auth_url = f"{BASE_URL}/auth/login"
        payload = user

        try:
            response = requests.post(auth_url, json=payload, headers={'Content-Type': 'application/json'})
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Authentication successful for user: {data['user']['username']}")
                return data['access_token']
            else:
                print(f"❌ Authentication failed for {user['username']}: {response.status_code}")
                continue
        except Exception as e:
            print(f"❌ Authentication error for {user['username']}: {e}")
            continue

    print("❌ All login attempts failed. Please create a user first or check valid credentials.")
    return None

def get_products(token):
    """Fetch available products to see what we can sell"""
    products_url = f"{BASE_URL}/products"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(products_url, headers=headers)
        if response.status_code == 200:
            products = response.json()
            print(f"✅ Found {len(products)} products:")
            for product in products[:3]:  # Show first 3 products
                print(f"   - {product['name']} (ID: {product['id']}, Stock: {product['stock']})")
            return products
        else:
            print(f"❌ Failed to fetch products: {response.status_code}")
            print(f"Response: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error fetching products: {e}")
        return []

def record_sale(token, products):
    """Record a sale with test products"""
    sales_url = f"{BASE_URL}/sales/"

    # Create sale items - pick the first available product
    sale_items = []
    if products:
        first_product = products[0]
        if first_product['stock'] > 0 and first_product['id']:  # Check product has stock
            sale_items = [
                {
                    "product_id": first_product['id'],
                    "quantity": 1.0  # Sell 1 unit (converted to float as expected by backend)
                }
            ]
            print(f"📦 Preparing to sell: {first_product['name']} (ID: {first_product['id']}, Quantity: 1.0)")
        else:
            print(f"❌ Selected product has no stock: {first_product}")
            return False

    if not sale_items:
        print("❌ No valid products available for sale")
        return False

    # Prepare the exact payload structure that the JavaScript sends
    request_body = {
        "items": sale_items
    }

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true'
    }

    print(f"📡 Sending sale request to: {sales_url}")
    print(f"📨 Request payload: {json.dumps(request_body, indent=2)}")

    try:
        response = requests.post(sales_url, json=request_body, headers=headers)

        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response body: {response.text}")

        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print("✅ Sale recorded successfully!")
            print(f"📋 Sale details: {json.dumps(result, indent=2)}")
            return True
        else:
            print("❌ Sale recording failed!")
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"🚫 Error details: {error_data}")
            except:
                print(f"🚫 Raw response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Request error: {e}")
        return False

def main():
    """Main test function"""
    print("🛒 Testing sales functionality from index.html equivalent")
    print("=" * 60)

    # Try to authenticate
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication")
        return

    print("-" * 40)

    # Get available products
    products = get_products(token)
    if not products:
        print("❌ Cannot proceed without products")
        return

    print("-" * 40)

    # Attempt to record a sale
    success = record_sale(token, products)

    print("-" * 40)
    if success:
        print("🎉 Sales functionality test PASSED! The issue is likely frontend-only.")
        print("🔍 The production server issue may be due to CORS or network configuration.")
    else:
        print("❌ Sales functionality test FAILED!")
        print("🔧 The issue is with the backend sales endpoint.")

if __name__ == "__main__":
    main()
