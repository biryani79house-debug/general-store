#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()
import os
import sqlite3

# Connect to SQLite database
database_url = os.getenv('DATABASE_URL', 'sqlite:///./kirana_store.db')
if 'sqlite' in database_url:
    db_path = database_url.replace('sqlite:///./', '')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check sales for product_id 2 (Gold Drop Oil)
    cursor.execute('SELECT id, product_id, quantity, total_amount, sale_date FROM sales WHERE product_id = 2')
    sales = cursor.fetchall()

    print('Sales for Gold Drop Oil (product_id: 2):')
    total_sales_qty = 0
    for sale in sales:
        print(f'ID: {sale[0]}, Quantity: {sale[2]}, Amount: ₹{sale[3]}, Date: {sale[4]}')
        # Parse quantity
        qty_str = sale[2]
        try:
            qty = float(qty_str)
        except:
            # Parse proportion
            if qty_str.endswith('ml'):
                qty = float(qty_str.replace('ml', '')) / 1000.0
            elif qty_str.endswith('ltr'):
                qty = float(qty_str.replace('ltr', ''))
            else:
                try:
                    qty = float(qty_str)
                except:
                    qty = 0
        total_sales_qty += qty
        print(f'  Parsed quantity: {qty}')

    print(f'\nTotal sales quantity: {total_sales_qty}')

    # Check purchases for product_id 2
    cursor.execute('SELECT id, quantity, total_cost, purchase_date FROM purchases WHERE product_id = 2')
    purchases = cursor.fetchall()

    print('\nPurchases for Gold Drop Oil (product_id: 2):')
    total_purchase_qty = 0
    for purchase in purchases:
        print(f'ID: {purchase[0]}, Quantity: {purchase[1]}, Cost: ₹{purchase[2]}, Date: {purchase[3]}')
        total_purchase_qty += purchase[1]

    print(f'\nTotal purchase quantity: {total_purchase_qty}')
    print(f'Current stock should be: {total_purchase_qty - total_sales_qty}')

    # Check current stock in products table
    cursor.execute('SELECT stock FROM products WHERE id = 2')
    current_stock = cursor.fetchone()
    print(f'Current stock in database: {current_stock[0] if current_stock else "None"}')

    conn.close()
