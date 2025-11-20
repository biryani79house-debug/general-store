import requests
import json

def login_and_get_token():
    """Login and get authentication token"""
    login_data = {
        "username": "raza123",
        "password": "123456"
    }

    login_response = requests.post('http://localhost:8000/auth/login', json=login_data)
    print(f"Login status: {login_response.status_code}")

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return None

    login_result = login_response.json()
    token = login_result['access_token']
    print(f"✅ Login successful, token obtained")
    return token

def test_sale():
    print("\n🔐 Logging in to get authentication token...")
    token = login_and_get_token()
    if not token:
        print("Cannot proceed without authentication")
        return

    headers = {'Authorization': f'Bearer {token}'}

    print("\n🔍 Finding almonds product...")

    # Get all products (no auth required)
    products_response = requests.get('http://localhost:8000/products')
    print(f"Products API status: {products_response.status_code}")

    if products_response.status_code != 200:
        print(f"Failed to get products: {products_response.text}")
        return

    products = products_response.json()
    almonds = None

    # Find almonds product
    for product in products:
        if 'almonds' in product['name'].lower():
            almonds = product
            break

    if not almonds:
        print("❌ Almonds product not found!")
        return

    print(f"✅ Found almonds: ID={almonds['id']}, Name='{almonds['name']}', Stock={almonds['stock']}")
    print(f"   Proportions: {almonds['proportions']}")
    print(f"   Prices: {json.dumps(almonds['proportion_prices'], indent=2)[:200]}...")

    # Test a sale of 750gm almonds
    sale_data = {
        'items': [
            {
                'product_id': almonds['id'],
                'quantity': '750gm'  # Using proportion format
            }
        ]
    }

    print(f"\n💰 Attempting sale of 750gm almonds...")
    print(f"   Request data: {json.dumps(sale_data, indent=2)}")

    sale_response = requests.post('http://localhost:8000/sales/', json=sale_data, headers=headers)
    print(f"   Sale API status: {sale_response.status_code}")

    if sale_response.status_code == 201:
        sale_result = sale_response.json()
        print("✅ Sale successful!")
        print(f"   Bill ID: {sale_result['bill_id']}")
        print(f"   Total amount: ₹{sale_result['total_amount']}")
        print(f"   Items: {len(sale_result['sales'])}")

        for item in sale_result['sales']:
            print(f"   - Product ID {item['product_id']}: {item['quantity']} = ₹{item['total_amount']}")
    else:
        print(f"❌ Sale failed: {sale_response.text}")

if __name__ == "__main__":
    test_sale()
