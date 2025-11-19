#!/usr/bin/env python3
import requests
import json

# Login as admin to get token
login_data = {'username': 'raza123', 'password': '123456'}
login_response = requests.post('http://localhost:8001/auth/login', json=login_data)
token = login_response.json().get('access_token')

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Record a sale with proportion quantity for MILK
print('🛒 Recording sale: MILK 500ml...')

sale_data = {
    'items': [
        {
            'product_id': 4,  # Milk product ID
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

        # Check if the latest milk sale shows proportion correctly
        latest_sale = sales[0] if sales else None
        if latest_sale and latest_sale['product_name'] == 'milk':
            if latest_sale['quantity'] == '500ml':
                print()
                print('✅ SUCCESS: Milk sales ledger shows "500ml" in quantity correctly!')
                print(f'   Expected: "500ml"')
                print(f'   Found: "{latest_sale["quantity"]}"')
            else:
                print()
                print(f'❌ ISSUE: Expected quantity "500ml", got "{latest_sale["quantity"]}"')
        else:
            print('❌ Latest sale is not for milk')
    else:
        print(f'❌ Failed to get ledger: {ledger_response.status_code}')
else:
    print(f'❌ Sale failed: {sales_response.status_code} - {sales_response.text}')
