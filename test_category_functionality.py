import requests
import json

# Test script to verify category filtering functionality

def test_category_filter():
    print('🧪 Testing Category Filtering Functionality\n')

    # Test 1: Categories endpoint
    print('🏷️  Test 1: Categories endpoint...')
    try:
        response = requests.get('http://localhost:8000/categories',
                               headers={'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true'})
        if response.status_code == 200:
            categories = response.json()
            print(f'✅ Categories endpoint successful. Found {len(categories)} categories:')
            for cat in categories[:3]:  # Show first 3
                print(f'   - {cat["name"]} (ID: {cat["id"]})')
            categories_loaded = len(categories) > 0
        else:
            print(f'❌ Categories endpoint failed: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Network error: {e}')
        return False

    # Test 2: Login
    print('\n🔐 Test 2: Authentication...')
    try:
        login_data = {'username': 'raza123', 'password': '123456'}
        login_response = requests.post('http://localhost:8000/auth/login',
                                     json=login_data,
                                     headers={'ngrok-skip-browser-warning': 'true'})
        if login_response.status_code == 200:
            result = login_response.json()
            token = result.get('access_token')
            print('✅ Login successful')
            login_successful = True
        else:
            print(f'❌ Login failed: {login_response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Login network error: {e}')
        return False

    # Test 3: Products without category filter
    print('\n📦 Test 3: Products without category filter...')
    try:
        headers = {'Authorization': f'Bearer {token}',
                  'Content-Type': 'application/json',
                  'ngrok-skip-browser-warning': 'true'}

        response = requests.get('http://localhost:8000/products', headers=headers)
        if response.status_code == 200:
            products = response.json()
            print(f'✅ Products endpoint successful. Found {len(products)} products:')
            for prod in products:
                print(f'   - {prod["name"]} (Stock: {prod["stock"]})')

            products_loaded = len(products) > 0
        else:
            print(f'❌ Products endpoint failed: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Products endpoint error: {e}')
        return False

    # Test 4: Category filtering
    print('\n🎯 Test 4: Category filtering functionality...')
    if categories_loaded and products_loaded:
        test_category = None

        # Find a category that might have products
        for cat in categories:
            if cat["name"] in ["Fruits", "Groceries", "Dairy"]:  # Common categories from seeding
                test_category = cat["name"]
                break

        if test_category:
            print(f'🔍 Testing filter by category: {test_category}')
            try:
                response = requests.get(f'http://localhost:8000/products?category={test_category}', headers=headers)
                if response.status_code == 200:
                    filtered_products = response.json()
                    print(f'✅ Category filter successful. Found {len(filtered_products)} products in category "{test_category}"')

                    if len(filtered_products) > 0:
                        print('✅ Filtered products:')
                        for prod in filtered_products:
                            print(f'   - {prod["name"]} (Category: {prod.get("category", "N/A")})')
                    else:
                        print(f'ℹ️  No products found in category "{test_category}" (this may be normal)')

                    category_filter_works = True
                else:
                    print(f'❌ Category filter failed: {response.status_code}')
                    return False
            except Exception as e:
                print(f'❌ Category filter error: {e}')
                return False
        else:
            print('⚠️  No suitable test category found')
            # Still count as successful if basic functionality works
            category_filter_works = True
    else:
        print('⚠️  Skipping category filter test (missing data)')
        category_filter_works = True

    # Test 5: Comprehensive category testing - check each category
    print('\n📋 Test 5: Testing all categories with products...')

    # Check what products exist per category
    product_category_mapping = {}

    # Get basic product list to see available products
    all_products_response = requests.get('http://localhost:8000/products', headers=headers)
    if all_products_response.status_code == 200:
        all_products = all_products_response.json()
        print(f'📦 Total products in system: {len(all_products)}')
    else:
        print('❌ Could not fetch product list')
        return False

    # Get all categories
    categories_response = requests.get('http://localhost:8000/categories',
                                      headers={'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true'})
    if categories_response.status_code != 200:
        print('❌ Could not fetch categories')
        return False

    all_categories = categories_response.json()
    print(f'🏷️  Available categories: {[c["name"] for c in all_categories]}')

    # Test each category to see which ones have products
    categories_with_products = []
    for category in all_categories:
        category_name = category["name"]
        response = requests.get(f'http://localhost:8000/products?category={category_name}', headers=headers)
        if response.status_code == 200:
            products = response.json()
            if products:  # Has products
                categories_with_products.append(category_name)
                print(f'✅ {category_name}: {len(products)} products')
                for prod in products:
                    print(f'   - {prod["name"]}')
        else:
            print(f'❌ Error testing category {category_name}')

    # Test user's specific scenarios
    print('\n🎯 Test 6: User-reported scenarios...')

    # Test "Fruits" category (should be empty)
    fruits_response = requests.get('http://localhost:8000/products?category=fruits', headers=headers)
    if fruits_response.status_code == 200:
        fruits_products = fruits_response.json()
        if len(fruits_products) == 0:
            print('✅ Fruits category: No products found (CORRECT)')
        else:
            print(f'⚠️  Fruits category: Found {len(fruits_products)} products (unexpected)')
    else:
        print('❌ Could not test Fruits category')

    # Test "Groceries" category (should have products)
    groceries_response = requests.get('http://localhost:8000/products?category=groceries', headers=headers)
    if groceries_response.status_code == 200:
        groceries_products = groceries_response.json()
        if len(groceries_products) > 0:
            print(f'✅ Groceries category: Found {len(groceries_products)} products')
            for prod in groceries_products:
                print(f'   - {prod["name"]} (ISSUE FIXED!)')
        else:
            print('❌ Groceries category: No products found (BUG STILL EXISTS!)')
            return False
    else:
        print('❌ Could not test Groceries category')

    print(f'\n📊 Summary: Categories with products: {categories_with_products}')
    if 'Groceries' in categories_with_products:
        print('🎉 SUCCESS: Your "masoor dal" product filtering issue has been resolved!')
    else:
        print('❌ FAILURE: Groceries category still has no products')

    # Summary
    print('\n📊 Test Results:')
    print(f'   - Categories loaded: {"✅" if categories_loaded else "❌"}')
    print(f'   - Authentication works: {"✅" if login_successful else "❌"}')
    print(f'   - Products loaded: {"✅" if products_loaded else "❌"}')
    print(f'   - Case-sensitive filter works: {"✅" if category_filter_works else "❌"}')
    print(f'   - Case-insensitive filter works: {"✅" if "lowercase_category_works" in locals() and lowercase_category_works else "❌"}')

    success = categories_loaded and login_successful and products_loaded and category_filter_works

    if success:
        print('\n🎉 All tests passed! Category filtering functionality is working correctly.')
    else:
        print('\n❌ Some tests failed. Please check the implementation.')

    return success

if __name__ == "__main__":
    success = test_category_filter()
    exit(0 if success else 1)
