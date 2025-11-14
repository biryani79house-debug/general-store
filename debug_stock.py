#!/usr/bin/env python3
"""
Debug script to check stock calculation and write to file
"""
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv('DATABASE_URL', 'sqlite:///./kirana_store.db')
if 'sqlite' in database_url:
    db_path = database_url.replace('sqlite:///./', '')

with open('stock_debug.txt', 'w') as f:
    # Redirect stdout to file
    import sys
    sys.stdout = f

    print("Checking Gold Drop Oil (product_id: 2) stock calculations..." + "\\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check product
    cursor.execute('SELECT id, name, stock FROM products WHERE id = 2')
    product = cursor.fetchone()

    if not product:
        print("Product with ID 2 not found!")
        conn.close()
        sys.stdout = sys.__stdout__
        exit(1)

    print("Product: {} (ID: {})".format(product[1], product[0]))
    print("Current stock in database: {}".format(product[2]) + "\\n")

    # Check purchases
    cursor.execute('SELECT id, quantity, total_cost, purchase_date FROM purchases WHERE product_id = 2 ORDER BY purchase_date')
    purchases = cursor.fetchall()
    total_purchases = sum(p[1] for p in purchases)

    print("Purchases for {}:".format(product[1]))
    for purchase in purchases:
        print("   Purchase ID {}: {} units at Rs.{} on {}".format(purchase[0], purchase[1], purchase[2], purchase[3]))
    print("Total purchased: {}".format(total_purchases) + "\\n")

    # Check sales
    cursor.execute('SELECT id, quantity, total_amount, sale_date FROM sales WHERE product_id = 2 ORDER BY sale_date')
    sales = cursor.fetchall()

    print("Sales for {}:".format(product[1]))
    total_sales_parsed = 0

    def parse_sale_quantity(qty_str):
        try:
            return float(qty_str)
        except ValueError:
            qty_str = qty_str.strip()
            if qty_str.endswith('ml'):
                ml_value = float(qty_str.replace('ml', ''))
                return ml_value / 1000.0
            elif qty_str.endswith('ltr'):
                return float(qty_str.replace('ltr', ''))
        return 0

    for sale in sales:
        qty_str = sale[1]
        parsed_qty = parse_sale_quantity(qty_str)
        total_sales_parsed += parsed_qty
        print("   Sale ID {}: '{}' -> {} units at Rs.{} on {}".format(sale[0], qty_str, parsed_qty, sale[2], sale[3]))

    print("Total sales volume (parsed): {}".format(total_sales_parsed))

    expected_stock = total_purchases - total_sales_parsed
    print("\\nCalculation: {} - {} = {}".format(total_purchases, total_sales_parsed, expected_stock))
    print("Expected stock: {}".format(expected_stock))
    print("Database stock: {}".format(product[2]))

    if abs(expected_stock - product[2]) < 0.01:
        print("\\nStock calculation is CORRECT!")
        if str(expected_stock).endswith('.5'):
            print("Fix verified: fractional stock (like .5) is displaying correctly!")
    else:
        print("\\nStock calculation is INCORRECT!")
        print("   Difference: {}".format(abs(expected_stock - product[2])))

    # Show fractional sales
    fraction_sales = [s for s in sales if parse_sale_quantity(s[1]) % 1 != 0]
    if fraction_sales:
        print("\\nFound {} fractional sales causing .5 in stock:".format(len(fraction_sales)))
        for sale in fraction_sales[:5]:
            parsed = parse_sale_quantity(sale[1])
            print("   Sale ID {}: '{}' = {} units".format(sale[0], sale[1], parsed))

    conn.close()

    sys.stdout = sys.__stdout__

print("Results written to stock_debug.txt")
