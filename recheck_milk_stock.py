import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

print("🧪 DOUBLE-CHECKING MILK STOCK CALCULATION")

# Get milk product details
cursor.execute('SELECT id, name, stock FROM products WHERE LOWER(name) LIKE %s', ('%milk%',))
milk_product = cursor.fetchone()

if not milk_product:
    print("❌ Milk product not found")
    exit()

milk_id = milk_product[0]
milk_name = milk_product[1]
current_stock = milk_product[2]

print(f"\n🍶 Product: {milk_name} (ID: {milk_id})")
print(f"📊 Current DB Stock: {current_stock}")

# Get ALL purchases for milk with details
cursor.execute('''
    SELECT date, quantity, unit_cost, total_cost
    FROM purchases
    WHERE product_id = %s
    ORDER BY date DESC
''', (milk_id,))
purchases = cursor.fetchall()

print("
🛒 PURCHASES:"    total_purchased = 0
    for purchase in purchases:
        date, quantity, unit_cost, total_cost = purchase
        total_purchased += quantity
        print(f"  {date.strftime('%d/%m/%Y')} - {quantity} units - ₹{total_cost:.2f}")

    print(f"  Total Purchased: {total_purchased}")

    # Get ALL sales for milk with details
    cursor.execute('''
        SELECT date, quantity, total_amount
        FROM sales
        WHERE product_id = %s
        ORDER BY date DESC LIMIT 10
    ''', (milk_id,))
    sales = cursor.fetchall()

    print("
🛍️ SALES:")
    total_sold_litres = 0
    unit_conversion_needed = False

    for sale in sales:
        date, quantity, total_amount = sale

        # Check if quantity contains units
        qty_str = str(quantity).strip()
        if 'ml' in qty_str.lower() or 'ltr' in qty_str.lower():
            unit_conversion_needed = True
            # Parse the quantity properly
            if 'ml' in qty_str.lower():
                ml_value = float(qty_str.replace('ml', '').replace('ML', '').strip())
                litres_value = ml_value / 1000.0
                print(".3f"
            elif 'ltr' in qty_str.lower():
                litres_value = float(qty_str.replace('ltr', '').replace('LTR', '').strip())
                print(".3f"
        else:
            # Assume it's already in litres or unit quantity
            litres_value = float(qty_str)
            print(f"  {date.strftime('%d/%m/%Y')} - {quantity} units - ₹{total_amount:.2f}")

        total_sold_litres += litres_value

    print(f"  Total Sales: {total_sold_litres} litres")
    print(f"  (Unit conversion needed: {unit_conversion_needed})")

    # Calculate expected stock
    expected_stock = total_purchased - total_sold_litres
    print("
🎯 CALCULATION:"    print(f"  Purchased: {total_purchased} litres")
    print(f"  Sold: {total_sold_litres} litres")
    print(f"  Expected Stock: {expected_stock} litres")
    print(f"  Current DB Stock: {current_stock} litres")

    if abs(expected_stock - current_stock) < 0.01:
        print("✅ STOCK MATCHES!"    else:
        print(f"❌ STOCK MISMATCH! Should be {expected_stock}, is {current_stock}")

        # Update if needed
        if input(f"Update milk stock to {expected_stock}? (y/n): ").lower() == 'y':
            cursor.execute('UPDATE products SET stock = %s WHERE id = %s', (expected_stock, milk_id))
            conn.commit()
            print("✅ Updated!")

conn.close()
