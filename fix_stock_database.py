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

# Find products that have stock mismatches
cursor.execute('SELECT id, name, stock FROM products ORDER BY id')
products = cursor.fetchall()

print('🔧 FIXING DATABASE STOCK FOR MISMATCHED PRODUCTS...\n')

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

for product in products:
    product_id = product[0]
    product_name = product[1]
    current_stock = product[2]

    # Get total purchased
    cursor.execute('SELECT quantity FROM purchases WHERE product_id = %s', (product_id,))
    purchases = cursor.fetchall()
    total_purchased = sum(p[0] for p in purchases)

    # Get total sold with parsing
    cursor.execute('SELECT quantity FROM sales WHERE product_id = %s', (product_id,))
    sales = cursor.fetchall()
    total_sold = sum(parse_qty(sale[0]) for sale in sales)

    # Calculate correct stock
    correct_stock = total_purchased - total_sold

    # Check if there's a mismatch
    if abs(correct_stock - current_stock) > 0.01:
        print(f'📊 {product_name}: DB={current_stock} -> Fixed={correct_stock}')
        # Update the database stock
        cursor.execute('UPDATE products SET stock = %s WHERE id = %s', (correct_stock, product_id))
        print(f'✅ Updated {product_name} stock to {correct_stock}')
    else:
        print(f'✓ {product_name}: Stock correct ({current_stock})')

# Commit changes
conn.commit()

# Verify fixes
print('\n🔍 VERIFYING FIXES...')
cursor.execute('SELECT id, name, stock FROM products ORDER BY id')
fixed_products = cursor.fetchall()

for product in fixed_products:
    product_id = product[0]
    product_name = product[1]
    current_stock = product[2]

    # Recalculate expected stock
    cursor.execute('SELECT quantity FROM purchases WHERE product_id = %s', (product_id,))
    purchases = cursor.fetchall()
    total_purchased = sum(p[0] for p in purchases)

    cursor.execute('SELECT quantity FROM sales WHERE product_id = %s', (product_id,))
    sales = cursor.fetchall()
    total_sold = sum(parse_qty(sale[0]) for sale in sales)

    expected_stock = total_purchased - total_sold

    if abs(expected_stock - current_stock) < 0.01:
        print(f'✅ {product_name}: Stock verified - {current_stock}')
    else:
        print(f'❌ {product_name}: Still has issues - Current: {current_stock}, Expected: {expected_stock}')

conn.close()
print('\n🎉 Stock database update complete!')
