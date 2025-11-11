#!/usr/bin/env python3
"""
Test creating a product with proportion
"""
import requests
import json

base_url = 'http://localhost:8000'
login_data = {'username': 'raza123', 'password': '123456'}

response = requests.post(f'{base_url}/auth/login', json=login_data)
if response.status_code == 200:
    result = response.json()
    token = result.get('access_token')

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    # Create a new product with proportion
    new_product = {
        'name': 'Test Rice 750gm',
        'purchase_price': 45.0,
        'selling_price': 55.0,
        'unit_type': 'kgs',
        'proportion': '750gm'
    }

    response = requests.post(f'{base_url}/products/', json=new_product, headers=headers)
    if response.status_code == 201:
        result = response.json()
        print('✅ Product created successfully!')
        print(f'Product: {result["name"]} (proportion: {result.get("proportion")})')
    else:
        print(f'❌ Failed to create product: {response.status_code} - {response.text}')
else:
    print(f'Login failed: {response.text}')
