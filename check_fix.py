#!/usr/bin/env python3
"""
Test script to verify the stock calculation fix works correctly.
"""
import os
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to database
database_url = os.getenv('DATABASE_URL', 'sqlite:///./kirana_store.db')
if 'sqlite' in database_url:
    db_path = database_url.replace('sqlite:///./', '')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔍 Checking Gold Drop Oil (product_id: 2) stock calculations...")

    # Get product info
    cursor.execute('SELECT id, name, stock FROM products WHERE id = 2')
    product = cursor.fetchone()
    if not product:
        print("❌ Product with ID 2 not found!")
        conn.close()
        exit(1)

    print(f"📦 Product: {product[1]} (ID: {product[0]})")
    print(f"🗄️  Current stock in database: {product[2]}")

    # Get all purchases
    cursor.execute('SELECT id, quantity, total_cost, purchase_date FROM purchases WHERE product_id = 2 ORDER BY purchase_date')
    purchases = cursor.fetchall()
    total_purchases = sum(p[1] for p in purchases)

    print(f"\\n🛒 Purchases for {product[1]}:")
    for purchase in purchases:
        print("2d")
    print(f"📊 Total purchased: {total_purchases}")

    # Get all sales
    cursor.execute('SELECT id, quantity, total_amount, sale_date FROM sales WHERE product_id = 2 ORDER BY sale_date')
    sales = cursor.fetchall()

    print(f"\\n💰 Sales for {product[1]}:")
    total_sales_parsed = 0

    def parse_sale_quantity(qty_str):
        """Parse sale quantity from string to numeric value"""
        try:
            # Try to parse as float first (for cases like "2")
            return float(qty_str)
        except ValueError:
            # If it's a proportion string like "500gm", "500ml", etc.
            # We need to find which proportion it matches and calculate the quantity
            qty_str = qty_str.strip()

            # Handle ml amounts (convert to liters)
            if qty_str.endswith('ml'):
                ml_value = float(qty_str.replace('ml', ''))
                return ml_value / 1000.0  # Convert to liters
            elif qty_str.endswith('ltr'):
                return float(qty_str.replace('ltr', ''))
            elif qty_str.endswith('gm') or qty_str.endswith('g'):
                gram_value = float(qty_str.replace('gm', '').replace('g', ''))
                return gram_value / 1000.0  # Convert to kg
            elif qty_str.endswith('kg'):
                return float(qty_str.replace('kg', ''))

        return 0  # fallback

    for sale in sales:
        qty_str = sale[1]
        parsed_qty = parse_sale_quantity(qty_str)
        total_sales_parsed += parsed_qty
        print("2d")

    print(f"📊 Total sales volume (parsed): {total_sales_parsed}")

    # Calculate expected current stock
    expected_stock = total_purchases - total_sales_parsed
    print(f"\\n🧮 Calculation: {total_purchases} - {total_sales_parsed} = {expected_stock}")

    print(f"📈 Expected stock: {expected_stock}")
    print(f"💾 Database stock: {product[2]}")

    if abs(expected_stock - product[2]) < 0.01:  # Allow small floating point differences
        print("✅ Stock calculation is CORRECT!")
    else:
        print("❌ Stock calculation is INCORRECT!")
        print(f"   Difference: {abs(expected_stock - product[2])}")

    # Check if there are any fraction sales that contributed to the .5
    fraction_sales = [s for s in sales if '.' in str(parse_sale_quantity(s[1])) or parse_sale_quantity(s[1]) % 1 != 0]
    if fraction_sales:
        print(f"\\n📊 Found {len(fraction_sales)} fractional sales:")
        for sale in fraction_sales[:3]:  # Show first 3
            parsed = parse_sale_quantity(sale[1])
            print(f"   Sale ID {sale[0]}: '{sale[1]}' → {parsed}")

    conn.close()
