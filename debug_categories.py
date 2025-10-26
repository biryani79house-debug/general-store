#!/usr/bin/env python3
import requests

# Debug script to check what products are in each category
def debug_categories():
    print('🔍 Checking what products are in each category...\n')

    # Login
    data = {'username': 'raza123', 'password': '123456'}
    resp = requests.post('http://localhost:8001/auth/login', json=data)
    if resp.status_code != 200:
        print('Login failed!')
        return

    token = resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # Test different categories
    categories = ['fruits', 'Fruits', 'groceries', 'Groceries']

    print('Category testing:')
    for cat in categories:
        r = requests.get(f'http://localhost:8001/products?category={cat}', headers=headers)
        if r.status_code == 200:
            products = r.json()
            print(f'{cat.upper()}: {len(products) if isinstance(products, list) else " -"}')
            for p in products:
                name = p.get('name', 'unknown')
                print(f'  - {name} ! FOUND IN {cat.upper()}')
            print()

    # Also check all categories from the database
    print('Available categories in system:')
    cat_resp = requests.get('http://localhost:8001/categories')
    if cat_resp.status_code == 200:
        db_categories = cat_resp.json()
        for cat in db_categories:
            print(f'  - {cat["name"]} (ID: {cat["id"]})')

if __name__ == "__main__":
    debug_categories()
