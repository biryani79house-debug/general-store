#!/usr/bin/env python3
"""Test script to debug purchase ledger category filtering issue."""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_category_filtering():
    try:
        # Get authentication token
        login_response = requests.post('http://localhost:8000/auth/login', json={
            'username': 'raza123',
            'password': '123456'
        })

        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code} - {login_response.text}")
            return

        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        # Test categories
        categories_to_test = ['Groceries', 'Fruits', 'Dairy']

        for category in categories_to_test:
            print(f"\n=== Testing category: {category} ===")

            # Test purchase ledger with category filter
            response = requests.get(
                f'http://localhost:8000/ledger/purchases?category={category}',
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Records returned: {len(data)}")
                if data:
                    for item in data:
                        print(f"   - {item['product_name']}: qty={item['quantity']}, total=₹{item['total_cost']}")
                else:
                    print("   No records found")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")

        # Also test without category filter to see all purchases
        print("\n=== Testing without category filter (all purchases) ===")
        response = requests.get('http://localhost:8000/ledger/purchases', headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total records returned: {len(data)}")
            if data:
                for item in data:
                    print(f"   - {item['product_name']} ({item.get('product_category', 'No category')}): qty={item['quantity']}, total=₹{item['total_cost']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    test_category_filtering()
