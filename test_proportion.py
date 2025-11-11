#!/usr/bin/env python3
"""
Test the proportion functionality
"""
import requests
import json

def get_auth_token():
    """Get authentication token by logging in"""
    base_url = 'http://localhost:8000'
    login_data = {
        'username': 'raza123',
        'password': '123456'
    }

    try:
        response = requests.post(f'{base_url}/auth/login', json=login_data)
        if response.status_code == 200:
            result = response.json()
            return result.get('access_token')
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_proportion_functionality():
    """Test creating and retrieving products with proportions"""
    base_url = 'http://localhost:8000'

    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication")
        return

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Test data
    test_products = [
        {
            'name': 'Rice 750gm Pack',
            'purchase_price': 45.0,
            'selling_price': 55.0,
            'unit_type': 'kgs',
            'proportion': '750gm'
        },
        {
            'name': 'Milk 500ml Pack',
            'purchase_price': 25.0,
            'selling_price': 30.0,
            'unit_type': 'ltr',
            'proportion': '500ml'
        },
        {
            'name': 'Regular Bread',
            'purchase_price': 25.0,
            'selling_price': 35.0,
            'unit_type': 'pcs',
            'proportion': None
        }
    ]

    print("🧪 Testing proportion functionality...")

    # Test creating products
    created_products = []
    for product_data in test_products:
        try:
            response = requests.post(f'{base_url}/products/', json=product_data, headers=headers)
            print(f"📦 Creating product: {product_data['name']}")
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                created_products.append(result)
                proportion_display = f" ({result.get('proportion')})" if result.get('proportion') else ""
                print(f"   ✅ Created: {result['name']}{proportion_display}")
            else:
                print(f"   ❌ Failed: {response.text}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Test retrieving products
    try:
        print("\n📋 Retrieving all products...")
        response = requests.get(f'{base_url}/products', headers=headers)
        if response.status_code == 200:
            products = response.json()
            print(f"✅ Retrieved {len(products)} products")

            # Check if proportions are included
            products_with_proportions = [p for p in products if p.get('proportion')]
            print(f"📏 Products with proportions: {len(products_with_proportions)}")

            for product in products_with_proportions:
                proportion_display = f" ({product['proportion']})" if product.get('proportion') else ""
                print(f"   • {product['name']}{proportion_display}")

        else:
            print(f"❌ Failed to retrieve products: {response.status_code}")

    except Exception as e:
        print(f"❌ Error retrieving products: {e}")

    print("\n🎉 Proportion functionality test completed!")

if __name__ == "__main__":
    test_proportion_functionality()
