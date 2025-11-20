import sqlite3

conn = sqlite3.connect('kirana_store.db')
cursor = conn.cursor()

# Check distinct categories
cursor.execute('SELECT DISTINCT category FROM products WHERE category IS NOT NULL')
categories = cursor.fetchall()
print('Categories found:', [c[0] for c in categories])

# Check case sensitivity
cursor.execute('SELECT COUNT(*) FROM products WHERE category LIKE "%rocer%"')
count = cursor.fetchone()[0]
print(f'Products with "rocer" in category: {count}')

# Check exact grocery matches case insensitive
cursor.execute('SELECT COUNT(*) FROM products WHERE LOWER(category) = "groceries"')
groceries_count = cursor.fetchone()[0]
print(f'Products with category "groceries" (case insensitive): {groceries_count}')

# Check what the filter is actually doing
cursor.execute('SELECT category, COUNT(*) FROM products GROUP BY category')
category_counts = cursor.fetchall()
print('Category counts:', category_counts)

conn.close()
