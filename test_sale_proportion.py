#!/usr/bin/env python3
import requests
import json

# Login as admin to get token
login_data = {'username': 'raza123', 'password': '123456'}
login_response = requests.post('http://localhost:8001/auth/login', json=login_data)
token = login_response.json().get('access_token')

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# First, get Products to see what's available
print('🔍 Getting available products...')
products_response = requests.get('http://localhost:8001/products', headers=headers)
if products_response.status_code == 200:
    products = products_response.json()
    print(f'Found {len(products)} products')
    for i, product in enumerate(products[:3]):  # Show first 3 products
        print(f'  {i+1}. {product["name"]} (ID: {product["id"]}) - Proportions: {product.get("proportions", [])}')
        if product.get('proportion_prices'):
            print(f'    Prices: {product.get("proportion_prices")}')
else:
    print('❌ Failed to get products')
    exit(1)

print()

# Record a sale with proportion quantity
print('🛒 Recording sale with proportion quantity...')
# Using product ID 1 assuming it exists and has proportion prices
sale_data = {
    'items': [
        {
            'product_id': 1,  # First product
            'quantity': '500ml'  # Proportion quantity
        }
    ]
}

sales_response = requests.post('http://localhost:8001/sales/', json=sale_data, headers=headers)
if sales_response.status_code == 201:
    result = sales_response.json()
    print(f'✅ Sale recorded successfully!')
    print(f'   Bill ID: {result["bill_id"]}')
    print(f'   Total: ₹{result["total_amount"]:.2f}')
    print(f'   Items: {len(result["sales"])}')

    # Now check the sales ledger
    print()
    print('📊 Checking sales ledger...')
    ledger_response = requests.get('http://localhost:8001/ledger/sales?limit=5', headers=headers)
    if ledger_response.status_code == 200:
        sales = ledger_response.json()
        print(f'Found {len(sales)} sales in ledger:')
        for i, sale in enumerate(sales, 1):
            print(f'  {i}. {sale["product_name"]}: Qty="{sale["quantity"]}", Total=₹{sale["total_amount"]:.2f}, Unit=₹{sale["unit_price"]:.2f}')

        # Check if the latest sale shows proportion correctly
        if sales and sales[0]['quantity'] == '500ml':
            print('✅ SUCCESS: Sales ledger shows proportion quantity correctly!')
        else:
            print(f'❌ ISSUE: Expected quantity "500ml", got "{sales[0]["quantity"] if sales else "none"}"' )
    else:
        print(f'❌ Failed to get ledger: {ledger_response.status_code}')
else:
    print(f'❌ Sale failed: {sales_response.status_code} - {sales_response.text}')
