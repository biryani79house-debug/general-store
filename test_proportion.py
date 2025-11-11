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

    # Test data - NEW FORMAT: Single product with multiple proportions
    test_products = [
        {
            'name': 'Sugar',
            'purchase_price': 40.0,
            'selling_price': 50.0,
            'unit_type': 'kgs',
            'proportions': ['1kg', '750gm', '500gm', '250gm'],
            'category': 'Groceries',
            'stock': 0
        },
        {
            'name': 'Milk',
            'purchase_price': 25.0,
            'selling_price': 30.0,
            'unit_type': 'ltr',
            'proportions': ['1ltr', '750ml', '500ml', '250ml'],
            'category': 'Dairy',
            'stock': 0
        },
        {
            'name': 'Regular Bread',
            'purchase_price': 25.0,
            'selling_price': 35.0,
            'unit_type': 'pcs',
            'proportions': None,  # No proportions for pieces
            'category': 'Bakery',
            'stock': 0
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

            if response.status_code == 201:
                result = response.json()
                created_products.append(result)
                proportions_display = f" with {len(result.get('proportions', []))} proportions" if result.get('proportions') else " (no proportions)"
                print(f"   ✅ Created: {result['name']}{proportions_display}")
                if result.get('proportions'):
                    print(f"      Proportions: {', '.join(result['proportions'])}")
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
            products_with_proportions = [p for p in products if p.get('proportions') and len(p['proportions']) > 0]
            print(f"📏 Products with proportions: {len(products_with_proportions)}")

            for product in products_with_proportions:
                print(f"   • {product['name']} ({len(product['proportions'])} proportions: {', '.join(product['proportions'])})")

            # Test proportion-specific price fetching
            if products_with_proportions:
                test_product = products_with_proportions[0]
                if test_product.get('proportions') and len(test_product['proportions']) > 0:
                    test_proportion = test_product['proportions'][0]
                    print(f"\n💰 Testing proportion price for {test_product['name']} - {test_proportion}...")
                    try:
                        price_response = requests.get(f'{base_url}/products/{test_product["id"]}/price/{test_proportion}', headers=headers)
                        if price_response.status_code == 200:
                            price_data = price_response.json()
                            print(f"   ✅ Price for {test_proportion}: ₹{price_data['price']}")
                        else:
                            print(f"   ❌ Failed to get price: {price_response.status_code}")
                    except Exception as e:
                        print(f"   ❌ Error getting price: {e}")

        else:
            print(f"❌ Failed to retrieve products: {response.status_code}")

    except Exception as e:
        print(f"❌ Error retrieving products: {e}")

    print("\n🎉 Proportion functionality test completed!")

if __name__ == "__main__":
    test_proportion_functionality()
