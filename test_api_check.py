import requests
import json

# Login as admin to get token
login_data = {'username': 'raza123', 'password': '123456'}
login_response = requests.post('http://localhost:8001/auth/login', json=login_data)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

login_result = login_response.json()
token = login_result.get('access_token')

if not token:
    print('❌ Login failed, cannot get token')
    exit(1)

print('✅ Login successful, got token')

# Set authorization header
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Test products endpoint
print('\n=== PRODUCTS ===')
products_response = requests.get('http://localhost:8001/products', headers=headers)
if products_response.status_code == 200:
    products = products_response.json()
    print(f"Found {len(products)} products")
    for product in products[:5]:  # First 5
        props = product.get('proportion_prices', {})
        print(f"ID: {product['id']}, Name: '{product['name']}', Price: ₹{product['price']:.0f}, Proportions: {product.get('proportions', [])}")
        print(f"  Proportion prices: {props}")
else:
    print(f"❌ Failed to get products: {products_response.status_code}")
    print(products_response.text)

# Test sales ledger
print('\n=== RECENT SALES ===')
ledger_response = requests.get('http://localhost:8001/ledger/sales', headers=headers)
if ledger_response.status_code == 200:
    sales = ledger_response.json()
    print(f"Found {len(sales)} sales entries")
    for sale in sales[:3]:  # First 3
        print(f"ID: {sale['sale_id']}, Date: {sale['date']}, Product: {sale['product_name']}, Quantity: {sale['quantity']}, Amount: ₹{sale['total_amount']:.2f}")
else:
    print(f"❌ Failed to get sales ledger: {ledger_response.status_code}")
    print(ledger_response.text)
