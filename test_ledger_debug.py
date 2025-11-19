#!/usr/bin/env python3
import sqlite3
import requests
import json

# Login as admin to get token
login_data = {'username': 'raza123', 'password': '123456'}
login_response = requests.post('http://localhost:8001/auth/login', json=login_data)
token = login_response.json().get('access_token')

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print('📊 Checking latest sales ledger...')

ledger_response = requests.get('http://localhost:8001/ledger/sales?limit=5', headers=headers)
if ledger_response.status_code == 200:
    sales = ledger_response.json()
    print(f'Found {len(sales)} sales in ledger:')
    for i, sale in enumerate(sales, 1):
        print(f'  {i}. {sale["product_name"]}: Qty="{sale["quantity"]}", Total=₹{sale["total_amount"]:.2f}, Unit=₹{sale["unit_price"]:.2f}')

    # Also check database directly
    conn = sqlite3.connect('kirana_store.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, quantity, total_amount, proportion FROM sales ORDER BY id DESC LIMIT 5')
    db_sales = cursor.fetchall()
    print(f'\n📊 Database check (latest 5 sales):')
    for sale in db_sales:
        print(f'  ID={sale[0]}: Qty="{sale[1]}", Total=₹{sale[2]}, Proportion="{sale[3]}"')
    conn.close()
else:
    print(f'❌ Ledger request failed: {ledger_response.status_code}')
    print(f'Error: {ledger_response.text}')
