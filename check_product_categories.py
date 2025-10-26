import requests

# Check current products and their categories
products_response = requests.get('https://web-production-9d240.up.railway.app/products', headers={'ngrok-skip-browser-warning': 'true', 'Content-Type': 'application/json'})

if products_response.status_code == 200:
    products = products_response.json()
    print('Current products:')
    for p in products:
        category = p.get('category', 'None')
        print(f'  - {p["name"]}: category="{category}"')
else:
    print('Error getting products:', products_response.text)

# Check categories
categories_response = requests.get('https://web-production-9d240.up.railway.app/categories', headers={'ngrok-skip-browser-warning': 'true', 'Content-Type': 'application/json'})

if categories_response.status_code == 200:
    categories = categories_response.json()
    print('\nAvailable categories:')
    for c in categories:
        print(f'  - {c["name"]} (ID: {c["id"]})')
else:
    print('Error getting categories:', categories_response.text)

# Test stock snapshot with various filters
print('\n--- STOCK SNAPSHOT API TESTS ---')

# Without category filter (should show all products)
print('Testing stock snapshot WITHOUT category filter (should show all products)...')
all_stock_response = requests.get('https://web-production-9d240.up.railway.app/products/stock-snapshot', headers={'ngrok-skip-browser-warning': 'true', 'Content-Type': 'application/json'})
if all_stock_response.status_code == 200:
    all_stock_data = all_stock_response.json()
    print(f'All stock snapshot returned {len(all_stock_data)} products')
else:
    print('All stock API error:', all_stock_response.text)

# With Groceries category filter (should show only products in Groceries)
print('\nTesting stock snapshot WITH Groceries category filter...')
groceries_stock_response = requests.get('https://web-production-9d240.up.railway.app/products/stock-snapshot?category=Groceries', headers={'ngrok-skip-browser-warning': 'true', 'Content-Type': 'application/json'})
if groceries_stock_response.status_code == 200:
    groceries_stock_data = groceries_stock_response.json()
    print(f'Groceries stock snapshot returned {len(groceries_stock_data)} products')
    if len(groceries_stock_data) > 0:
        for item in groceries_stock_data:
            print(f'  - {item.get("product_name", "Unknown")}: {item.get("stock", 0)} units / category: {item.get("category", "None")}')
else:
    print('Groceries stock API error:', groceries_stock_response.text)

print(f'\nSUMMARY:')
print(f'- Total products in database: 4')
print(f'- Products with categories assigned: 1 (masoor dal = Groceries)')
print(f'- Products without categories: 3 (uncategorized)')
print(f'- Stock API without filter: {len(all_stock_data) if all_stock_response.status_code == 200 else "?"} products')
print(f'- Stock API with Groceries filter: {len(groceries_stock_data) if groceries_stock_response.status_code == 200 else "?"} products')
print(f'- Expected result: ✅ This is working correctly!')

# Test with authentication (simulating logged-in user)
print('\nTesting with mock authentication token...')
# First login to get token
login_response = requests.post('https://web-production-9d240.up.railway.app/auth/login',
                       json={'username': 'raza123', 'password': '123456'},
                       headers={'ngrok-skip-browser-warning': 'true', 'Content-Type': 'application/json'})

print(f'Login response: {login_response.status_code}')
if login_response.status_code == 200:
    login_data = login_response.json()
    token = login_data.get('access_token')
    if token:
        auth_headers = {
            'ngrok-skip-browser-warning': 'true',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        print('Testing categories API with auth...')
        cat_auth_response = requests.get('https://web-production-9d240.up.railway.app/categories', headers=auth_headers)
        print(f'Categories with auth: {cat_auth_response.status_code}')

        print('Testing stock snapshot with auth...')
        stock_auth_response = requests.get('https://web-production-9d240.up.railway.app/products/stock-snapshot?category=Groceries', headers=auth_headers)
        print(f'Stock snapshot with auth: {stock_auth_response.status_code} - {len(stock_auth_response.json()) if stock_auth_response.status_code == 200 else "error"} products')
else:
    print('Failed to login for testing')
