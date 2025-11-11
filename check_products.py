#!/usr/bin/env python3
"""
Check current products in database
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

    response = requests.get(f'{base_url}/products', headers=headers)
    if response.status_code == 200:
        products = response.json()
        print(f'Found {len(products)} products:')
        for p in products:
            proportion = p.get('proportion', 'None')
            print(f'  - {p["name"]}: proportion={proportion}')
    else:
        print(f'Failed to get products: {response.status_code}')
else:
    print(f'Login failed: {response.text}')
