#!/usr/bin/env python3
"""
Final comprehensive test for proportion functionality
"""
import requests
import json

def test_proportion_functionality():
    """Comprehensive test of proportion functionality"""
    base_url = 'http://localhost:8000'

    # Get authentication token
    login_data = {'username': 'raza123', 'password': '123456'}
    response = requests.post(f'{base_url}/auth/login', json=login_data)

    if response.status_code != 200:
        print("❌ Authentication failed")
        return

    token = response.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    print("🧪 Testing Proportion Functionality")
    print("=" * 50)

    # Test 1: Create products with different proportions
    test_products = [
        {'name': 'Premium Rice 750gm', 'purchase_price': 45.0, 'selling_price': 55.0, 'unit_type': 'kgs', 'proportion': '750gm'},
        {'name': 'Fresh Milk 500ml', 'purchase_price': 25.0, 'selling_price': 30.0, 'unit_type': 'ltr', 'proportion': '500ml'},
        {'name': 'Regular Sugar', 'purchase_price': 40.0, 'selling_price': 50.0, 'unit_type': 'kgs', 'proportion': None}
    ]

    created_products = []
    for product_data in test_products:
        response = requests.post(f'{base_url}/products/', json=product_data, headers=headers)
        if response.status_code == 201:
            result = response.json()
            proportion_display = f" ({result.get('proportion')})" if result.get('proportion') else ""
            print(f"✅ Created: {result['name']}{proportion_display}")
            created_products.append(result)
        else:
            print(f"❌ Failed to create {product_data['name']}: {response.status_code}")

    print("\n" + "=" * 50)

    # Test 2: Retrieve all products and check proportions
    response = requests.get(f'{base_url}/products', headers=headers)
    if response.status_code == 200:
        products = response.json()
        print(f"📦 Retrieved {len(products)} products from API:")

        products_with_proportions = []
        for product in products:
            proportion = product.get('proportion')
            if proportion:
                products_with_proportions.append(product)
                print(f"   • {product['name']} ({proportion}) - ₹{product['price']}")
            else:
                print(f"   • {product['name']} - ₹{product['price']}")

        print(f"\n📊 Products with proportions: {len(products_with_proportions)}")

        # Test 3: Verify specific products have correct proportions
        expected_proportions = {
            'Premium Rice 750gm': '750gm',
            'Fresh Milk 500ml': '500ml',
            'Regular Sugar': None
        }

        print("\n🔍 Verification Results:")
        all_correct = True
        for product in products:
            name = product['name']
            if name in expected_proportions:
                expected = expected_proportions[name]
                actual = product.get('proportion')
                if actual == expected:
                    status = "✅"
                else:
                    status = "❌"
                    all_correct = False
                print(f"   {status} {name}: expected={expected}, actual={actual}")

        print("\n" + "=" * 50)
        if all_correct:
            print("🎉 SUCCESS: Proportion functionality is working correctly!")
            print("   • Products can be created with proportions")
            print("   • Proportions are correctly stored and retrieved")
            print("   • API returns proportion data properly")
        else:
            print("❌ FAILURE: Proportion functionality has issues")

    else:
        print(f"❌ Failed to retrieve products: {response.status_code}")

if __name__ == "__main__":
    test_proportion_functionality()
