import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL connection
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("DATABASE_URL not found!")
    exit()

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Get all products
cursor.execute('SELECT id, name, stock FROM products ORDER BY name')
products = cursor.fetchall()

print('=== ALL PRODUCTS ===')
for product in products:
    print(f'{product[0]}: {product[1]} (stock: {product[2]})')

# Find milk and dal products
products_to_check = []
for product in products:
    name = product[1].lower()
    if 'milk' in name or 'masoor' in name or 'dal' in name or 'lentil' in name:
        products_to_check.append(product[0])

print(f'\n🔍 Products to analyze: {products_to_check}')

# Analyze each product
for product_id in products_to_check:
    cursor.execute('SELECT id, name, stock FROM products WHERE id = %s', (product_id,))
    product = cursor.fetchone()

    print(f'\n=== {product[1].upper()} (ID: {product_id}) ===')
    print(f'DB Stock: {product[2]}')

    # Purchases
    cursor.execute('SELECT quantity FROM purchases WHERE product_id = %s', (product_id,))
    purchases = cursor.fetchall()
    total_purchased = sum(p[0] for p in purchases)
    print(f'Total Purchased: {total_purchased}')

    # Sales with parsing
    cursor.execute('SELECT quantity FROM sales WHERE product_id = %s', (product_id,))
    sales = cursor.fetchall()

    def parse_qty(qty):
        try:
            return float(qty)
        except:
            qty = qty.strip().lower()
            if 'ml' in qty:
                return float(qty.replace('ml', '').strip()) / 1000
            elif 'ltr' in qty:
                return float(qty.replace('ltr', '').strip())
            elif 'kg' in qty:
                return float(qty.replace('kg', '').strip())
            elif 'gm' in qty:
                return float(qty.replace('gm', '').strip()) / 1000
            else:
                return 0

    total_sold = 0
    print('Sale details:')
    for sale in sales:
        qty = sale[0]
        parsed = parse_qty(qty)
        total_sold += parsed
        print(f'  "{qty}" -> {parsed} units')

    print(f'Total Sold: {total_sold}')
    expected = total_purchased - total_sold
    print(f'Expected Stock: {expected}')
    match = "YES" if abs(expected - product[2]) < 0.01 else "NO - MISMATCH!"
    print(f'Stock Matches: {match}')

conn.close()
