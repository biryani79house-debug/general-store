#!/usr/bin/env python3
import os
import sqlite3

# Direct database check
db_path = "./kirana_store.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check product
    cursor.execute('SELECT id, name, stock FROM products WHERE id = 2')
    product = cursor.fetchone()
    if product:
        print("Gold Drop Oil (ID: {}): Current stock = {}".format(product[0], product[2]))

        # Check sales
        cursor.execute('SELECT quantity FROM sales WHERE product_id = 2')
        sales = [s[0] for s in cursor.fetchall()]
        print("Sales entries: {}".format(len(sales)))
        for qty in sales:
            print("  Quantity: '{}'".format(qty))
    else:
        print("Product not found")

    conn.close()
else:
    print("Database file not found")
