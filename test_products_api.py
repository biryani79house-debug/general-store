import requests
import json

# Test the products API to see if categories exist
BASE_URL = "https://web-production-9d240.up.railway.app"

print("🔍 Testing products API for categories...")

# First login to get token
login_data = {
    "username": "raza123",
    "password": "123456"
}

login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get products
    products_response = requests.get(f"{BASE_URL}/products", headers=headers)
    if products_response.status_code == 200:
        products = products_response.json()
        print(f"📊 Found {len(products)} products:")
        for product in products:
            print(f"  - ID: {product['id']}, Name: '{product['name']}', Category: '{product.get('category', 'None')}'")
    else:
        print(f"❌ Error getting products: {products_response.status_code}")
        print(products_response.text)
else:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
