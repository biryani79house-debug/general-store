import requests
import json

# Login as admin to get token
login_data = {'username': 'raza123', 'password': '123456'}
login_response = requests.post('http://localhost:8001/auth/login', json=login_data)
token = login_response.json().get('access_token')

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print('🛒 Testing PROPORTION sales...')

# Test selling gold drop oil (500ml - should cost ₹62.50)
print('Selling gold drop oil 500ml...')
sale_response = requests.post('http://localhost:8001/sales/', json={
    'items': [{'product_id': 2, 'quantity': '500ml'}]  # gold drop oil product_id=2
}, headers=headers)

if sale_response.status_code == 201:
    result = sale_response.json()
    print(f'✅ Gold drop oil 500ml: Bill ID: {result["bill_id"]}, Total: ₹{result["total_amount"]:.2f}')
    print('Expected: ₹62.50')
else:
    print(f'❌ Failed: {sale_response.text}')

# Test selling milk (500ml - should cost ₹30.00)
print('Selling milk 500ml...')
sale_response2 = requests.post('http://localhost:8001/sales/', json={
    'items': [{'product_id': 4, 'quantity': '500ml'}]  # milk product_id=4
}, headers=headers)

if sale_response2.status_code == 201:
    result = sale_response2.json()
    print(f'✅ Milk 500ml: Bill ID: {result["bill_id"]}, Total: ₹{result["total_amount"]:.2f}')
    print('Expected: ₹30.00')
else:
    print(f'❌ Failed: {sale_response2.text}')

print('\n📊 Checking sales ledger...')
ledger_response = requests.get('http://localhost:8001/ledger/sales', headers=headers)
if ledger_response.status_code == 200:
    sales = ledger_response.json()[:4]  # Most recent 4 sales
    for sale in sales:
        print(f'  {sale["product_name"]}: Qty={sale["quantity"]}, Amount=₹{sale["total_amount"]:.2f}, Unit=₹{sale["unit_price"]:.2f}')
else:
    print(f'❌ Failed to get ledger: {ledger_response.text}')
