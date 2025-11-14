import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv('DATABASE_URL', 'sqlite:///./kirana_store.db')
if 'sqlite' in database_url:
    db_path = database_url.replace('sqlite:///./', '')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all products
cursor.execute('SELECT id, name, stock FROM products ORDER BY name')
products = cursor.fetchall()

print('=== ALL PRODUCTS ===')
for product in products:
    print(f'{product[0]}: {product[1]} (stock: {product[2]})')

print('\n=== LOOKING FOR MILK PRODUCTS ===')
for product in products:
    if 'milk' in product[1].lower():
        print(f'Milk candidate: {product[0]}: {product[1]} (stock: {product[2]})')

print('\n=== LOOKING FOR MASOOR/DAL PRODUCTS ===')
for product in products:
    name_lower = product[1].lower()
    if 'masoor' in name_lower or 'dal' in name_lower or 'lentil' in name_lower:
        print(f'Dal candidate: {product[0]}: {product[1]} (stock: {product[2]})')

# Check specific products - let's look for the most likely candidates
# Usually ID 1 is Milk, ID 3 or 4 might be Masoor Dal
likely_candidates = [1, 3, 4]  # Common IDs

for product_id in likely_candidates:
    print(f'\n=== ANALYZING PRODUCT ID {product_id} ===')
    cursor.execute('SELECT id, name, stock FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()

    if not product:
        print(f'Product ID {product_id} not found!')
        continue

    print(f'Product: {product[1]} (Current DB stock: {product[2]})')

    # Check purchases
    cursor.execute('SELECT quantity, total_cost FROM purchases WHERE product_id = ?', (product_id,))
    purchases = cursor.fetchall()
    total_purchases = sum(p[0] for p in purchases)
    print(f'Total purchased: {total_purchases}')

    # Check sales with parsing
    cursor.execute('SELECT quantity FROM sales WHERE product_id = ?', (product_id,))
    sales = cursor.fetchall()

    def parse_sale_quantity(qty_str):
        try:
            return float(qty_str)
        except ValueError:
            qty_str = qty_str.strip().lower()
            if qty_str.endswith('ml'):
                ml_value = float(qty_str.replace('ml', ''))
                return ml_value / 1000.0
            elif qty_str.endswith('ltr'):
                return float(qty_str.replace('ltr', ''))
            elif qty_str.endswith('kg'):
                return float(qty_str.replace('kg', ''))
            elif qty_str.endswith('gm'):
                return float(qty_str.replace('gm', '')) / 1000.0
        return 0

    total_sales_parsed = 0
    print('Sale quantities:')
    for sale in sales:
        qty = sale[0]
        parsed_qty = parse_sale_quantity(qty)
        total_sales_parsed += parsed_qty
        print(f'  \"{qty}\" -> {parsed_qty} units')

    print(f'Total sales volume: {total_sales_parsed}')
    expected_stock = total_purchases - total_sales_parsed
    print(f'Expected stock (purchased - sold): {expected_stock}')
    print(f'Database stock: {product[2]}')

    if abs(expected_stock - float(product[2])) > 0.01:
        print('⚠️ STOCK MISMATCH - Database stock does not match calculation!')
    else:
        print('✅ Stock calculation appears correct')

conn.close()
