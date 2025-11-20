import requests
import json

# Test products endpoint
print("Testing /products endpoint...")
response = requests.get('http://localhost:8000/products')

if response.status_code == 200:
    products = response.json()
    print(f"Found {len(products)} products total")

    # Show first 10 products with stock info
    out_of_stock_count = sum(1 for p in products if p['stock'] <= 0)
    print(f"Out of stock products: {out_of_stock_count}/{len(products)}")
    for i, product in enumerate(products[:10]):
        stock_status = "OUT OF STOCK" if product['stock'] <= 0 else f"In stock: {product['stock']}"
        print(f"{i+1}. {product['name']}: {stock_status} ({product['unit_type']}) | Category: {product.get('category', 'None')}")

    # Check grocery category specifically (test both cases)
    print("\n--- GROCERY CATEGORY ---")
    # Test with lowercase "grocery"
    grocery_response = requests.get('http://localhost:8000/products?category=grocery')
    if grocery_response.status_code == 200:
        grocery_products = grocery_response.json()
        print(f"Found {len(grocery_products)} 'grocery' (lowercase) products")

    # Test with "Groceries" (proper case)
    groceries_response = requests.get('http://localhost:8000/products?category=Groceries')
    if groceries_response.status_code == 200:
        groceries_products = groceries_response.json()
        print(f"Found {len(groceries_products)} 'Groceries' (capital G) products")
        for product in groceries_products:
            stock_status = "OUT OF STOCK" if product['stock'] <= 0 else f"In stock: {product['stock']}"
            print(f"  {product['name']}: {stock_status} ({product['unit_type']})")

    # Show product with most negative stock if any
    negative_stock = [p for p in products if p['stock'] < 0]
    if negative_stock:
        print(f"\n⚠️ FOUND {len(negative_stock)} PRODUCTS WITH NEGATIVE STOCK:")
        for p in negative_stock:
            print(f"  {p['name']}: {p['stock']} {p['unit_type']}")
else:
    print(f"API Error: {response.status_code} - {response.text}")
