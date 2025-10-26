import requests

# First check what products exist
products_response = requests.get('https://web-production-9d240.up.railway.app/products', headers={'ngrok-skip-browser-warning': 'true', 'Content-Type': 'application/json'})

if products_response.status_code == 200:
    products = products_response.json()
    print('Current products:')
    for p in products[:10]:  # Show first 10 products
        category = p.get('category', 'None')
        print(f'  - {p["name"]}: category="{category}"')
else:
    print('Error getting products:', products_response.text)

# Check categories
categories_response = requests.get('https://web-production-9d240.up.railway.app/categories', headers={'ngrok-skip-browser-warning': 'true', 'Content-Type': 'application/json'})

if categories_response.status_code == 200:
    categories = categories_response.json()
    print(f'\nAvailable categories ({len(categories)}):')
    for c in categories:
        print(f'  - {c["name"]} (ID: {c["id"]})')
else:
    print('Error getting categories:', categories_response.text)
