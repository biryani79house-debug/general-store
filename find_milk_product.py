#!/usr/bin/env python3
import sqlite3

# Find the product with stock around 19 or 19.5
conn = sqlite3.connect('./kirana_store.db')
cursor = conn.cursor()

# Check all products for stock values
cursor.execute('SELECT id, name, stock FROM products WHERE stock >= 15 AND stock <= 25 ORDER BY stock DESC')
products = cursor.fetchall()

print("Products with stock between 15 and 25:")
for product in products:
    print("ID: {}, Name: '{}', Stock: {}".format(product[0], product[1], product[2]))

# Check if any contain 'milk' in name
cursor.execute("SELECT id, name, stock FROM products WHERE name LIKE '%milk%'")
milk_products = cursor.fetchall()

if milk_products:
    print("\\nMilk-related products:")
    for product in milk_products:
        print("ID: {}, Name: '{}', Stock: {}".format(product[0], product[1], product[2]))
else:
    print("\\nNo milk products found")

conn.close()
