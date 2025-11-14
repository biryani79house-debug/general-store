#!/usr/bin/env python3
import requests

try:
    response = requests.get('http://localhost:8000/ledger/stock/2')
    if response.status_code == 200:
        data = response.json()
        print('Gold Drop Oil Stock Ledger:')
        print(f'Current stock: {data["current_stock"]}')
        print(f'Opening stock: {data["opening_stock"]}')
        print(f'Total purchases: {data["total_purchases"]}')
        print(f'Total sales: {data["total_sales"]}')
        print('\nTransaction History:')
        for tx in data['history'][:5]:  # Show first 5 transactions
            print(f'Date: {tx["date"].split("T")[0]}, Transaction: {tx["transaction_type"]}, Quantity: {tx["quantity"]}, Stock after: {tx["stock_after_transaction"]}')
    else:
        print(f'Error: {response.status_code}')
        print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
