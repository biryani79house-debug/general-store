import requests
import json

# Test sales functionality
url = 'http://localhost:8001/sales/'

# Login as admin to get token
login_data = {'username': 'raza123', 'password': '123456'}
login_response = requests.post('http://localhost:8001/auth/login', json=login_data)
login_result = login_response.json()
token = login_result.get('access_token')

if not token:
    print('❌ Login failed, cannot test sales')
    exit(1)

print('✅ Login successful, got token')

# Prepare sale data for product with proportion quantity
sale_data = {
    'items': [{
        'product_id': 1,
        'quantity': '500ml'
    }]
}

# Set authorization header
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Make sales request
print('🛒 Testing sales endpoint with proportion quantity...')
sales_response = requests.post(url, json=sale_data, headers=headers)

print(f'Status Code: {sales_response.status_code}')
print(f'Response: {sales_response.text}')

if sales_response.status_code == 201:
    result = sales_response.json()
    print('✅ Sales successful!')
    print(f'Bill ID: {result["bill_id"]}, Total: ₹{result["total_amount"]:.2f}')
    print('✅ 422 error is fixed!')
else:
    print(f'❌ Sales failed: {sales_response.status_code}')
    print(f'Error response: {sales_response.text}')
