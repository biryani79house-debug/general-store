import sqlite3
import json

conn = sqlite3.connect('kirana_store.db')
cursor = conn.cursor()

# Check the most recent sales
print('=== RECENT SALES ===')
cursor.execute('SELECT id, bill_id, product_id, quantity, total_amount, proportion, unit_price FROM sales ORDER BY id DESC LIMIT 10')
sales = cursor.fetchall()
for sale in sales:
    print(f'ID: {sale[0]}, Bill: {sale[1]}, Product: {sale[2]}, Quantity: "{sale[3]}", Amount: {sale[4]}, Proportion: "{sale[5]}", Unit_Price: {sale[6]}')

print('\n=== PRODUCTS ===')
cursor.execute('SELECT id, name, selling_price, proportion_prices FROM products WHERE name LIKE "%gold drop%" OR name LIKE "%oil%"')
products = cursor.fetchall()
for product in products:
    print(f'ID: {product[0]}, Name: {product[1]}, Selling_Price: {product[2]}, Proportion_Prices: {product[3]}')

conn.close()
