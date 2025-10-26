#!/usr/bin/env python3
"""
Simple test to verify Groceries category filtering fix
"""

import requests
import json
import sys

def test_groceries_fix():
    print('🧪 Testing Groceries Category Filtering Fix\n')

    # Use port 8001 since 8000 is in use
    base_url = 'http://localhost:8001'

    # Login first
    print('🔐 Logging in as user...')
    login_data = {'username': 'raza123', 'password': '123456'}
    login_response = requests.post(f'{base_url}/auth/login', json=login_data)

    if login_response.status_code != 200:
        print(f'❌ Login failed: {login_response.status_code}')
        print(f'Response: {login_response.text}')
        return False

    token = login_response.json()['access_token']
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    print('✅ Login successful')

    # Test each scenario
    print('\n📋 Testing Product Categories:')

    # Test 1: Fruits category (should be empty)
    print('🍎 Testing Fruits category...')
    fruits_response = requests.get(f'{base_url}/products?category=fruits', headers=headers)
    if fruits_response.status_code == 200:
        fruits_products = fruits_response.json()
        print(f'   Fruits: {len(fruits_products)} products')
        if len(fruits_products) == 0:
            print('   ✅ CORRECT: No products in Fruits category')
        else:
            print('   ⚠️  UNEXPECTED: Products found in empty Fruits category')
    else:
        print(f'   ❌ Request failed: {fruits_response.status_code}')

    # Test 2: Groceries category (should have products)
    print('🥫 Testing Groceries category...')
    groceries_response = requests.get(f'{base_url}/products?category=groceries', headers=headers)
    if groceries_response.status_code == 200:
        groceries_products = groceries_response.json()
        print(f'   Groceries: {len(groceries_products)} products')
        if len(groceries_products) > 0:
            print('   ✅ SUCCESS: Products found in Groceries category!')
            for prod in groceries_products:
                print(f'   - {prod["name"]} ✅')
        else:
            print('   ❌ FAILURE: No products found in Groceries category')
            return False
    else:
        print(f'   ❌ Request failed: {groceries_response.status_code}')
        return False

    # Test 3: Test other variations to ensure case-insensitive
    print('\n🔄 Testing case variations...')
    variations = ['Groceries', 'groceries', 'GROCERIES']

    for variation in variations:
        print(f'   Testing "{variation}"...')
        resp = requests.get(f'{base_url}/products?category={variation}', headers=headers)
        if resp.status_code == 200:
            prods = resp.json()
            if len(prods) > 0:
                print(f'   ✅ "{variation}" found {len(prods)} products')
            else:
                print(f'   ❌ "{variation}" found no products')
        else:
            print(f'   ⚠️  "{variation}" request failed')

    print('\n🎉 Fix Verification Complete!')
    print('If you see "SUCCESS: Products found in Groceries category!" with your masoor dal listed,')
    print('then the case-sensitive filtering bug has been resolved!')

    return True

if __name__ == "__main__":
    success = test_groceries_fix()
    sys.exit(0 if success else 1)
