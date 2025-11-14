import requests
print('Testing API stock data...')
response = requests.get('http://localhost:8001/products/stock-snapshot')
print(f'Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    print(f'Received {len(data)} products')
    for item in data:
        if item.get('product_id') == 2:
            print(f'Gold Drop stock: {item.get("stock")} ltr')
            break
    else:
        print('Gold Drop not found')
        if data:
            print(f'First product ID: {data[0]["product_id"]}')
else:
    print(f'Request failed: {response.text[:100]}')
