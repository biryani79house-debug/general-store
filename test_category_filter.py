import requests
import json

# Test script to verify category filtering in sales ledger

# Backend URL
base_url = "http://localhost:8000"

# Login to get token
login_data = {
    "username": "raza123",
    "password": "123456"
}

print("🔐 Logging in...")
login_response = requests.post(f"{base_url}/auth/login", json=login_data)
if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
else:
    print(f"❌ Login failed: {login_response.status_code}")
    exit(1)

# Test sales ledger with vegetables category filter
print("\n📊 Testing sales ledger with vegetables category filter...")
params = {"category": "Vegetables"}
response = requests.get(f"{base_url}/ledger/sales", headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    print(f"✅ Filter request successful. Returned {len(data)} records")

    if len(data) == 0:
        print("✅ CORRECT: No sales found for vegetables category (expected empty)")
    else:
        print(f"❌ UNEXPECTED: Found {len(data)} sales records for vegetables category")
        for sale in data:
            print(f"  - Product: {sale['product_name']}, Category: {sale.get('product_category', 'N/A')}")

else:
    print(f"❌ Request failed: {response.status_code}")
    try:
        error_data = response.json()
        print(f"Error details: {error_data}")
    except:
        print(f"Response: {response.text}")

# Test sales ledger without category filter (should show existing sales)
print("\n📊 Testing sales ledger without category filter...")
response = requests.get(f"{base_url}/ledger/sales", headers=headers)

if response.status_code == 200:
    data = response.json()
    print(f"✅ Request successful. Returned {len(data)} total sales records")

    # Check if any records have vegetables category
    vegetables_sales = [s for s in data if s.get('product_category') == 'Vegetables']
    print(f"✅ Records with vegetables category: {len(vegetables_sales)}")

    if len(data) > 0:
        print("✅ Sample existing sales:")
        for i, sale in enumerate(data[:3]):  # Show first 3 records
            print(f"  - {sale['product_name']} ({sale.get('product_category', 'N/A')})")

else:
    print(f"❌ Request failed: {response.status_code}")

print("\n🧪 Test completed!")
