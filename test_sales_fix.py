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

# Prepare sale data
sale_data = {
    'items': [
        {
            'product_id': 1,  # Using product ID 1 (should be available)
            'quantity': '500ml'  # Proportion quantity
        }
    ]
}

# Set authorization header
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Make sales request
print('🛒 Testing sales endpoint with proportion quantity...')
sales_response = requests.post(url, json=sale_data, headers=headers)

if sales_response.status_code == 201:
    print('✅ Sales successful!')
    result = sales_response.json()
    print(f'Success details: Bill ID: {result["bill_id"]}, Total: ₹{result["total_amount"]:.2f}')
else:
    print(f'❌ Sales failed: {sales_response.status_code}')
    print(f'Error: {sales_response.text}')
