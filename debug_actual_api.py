#!/usr/bin/env python3
"""
Check what the actual API endpoints are returning for stock
"""
import requests
import json
import time

def check_api_responses():
    base_url = "http://localhost:8000"

    print("🔍 Checking API endpoints for Gold Drop Oil (ID: 2)")
    print("=" * 60)

    # Check products endpoint directly
    print("\n1. /products endpoint:")
    try:
        response = requests.get(f"{base_url}/products")
        if response.status_code == 200:
            products = response.json()
            gold_drop = next((p for p in products if p.get('id') == 2), None)
            if gold_drop:
                print(f"   Gold Drop Oil stock: {gold_drop['stock']}")
                print(f"   All product data: {json.dumps(gold_drop, indent=2)}")
            else:
                print("   Gold Drop Oil not found")
        else:
            print(f"   Error: {response.status_code}")
    except Exception as e:
        print(f"   Request failed: {e}")

    # Check stock-snapshot endpoint
    print("\n2. /products/stock-snapshot endpoint:")
    try:
        response = requests.get(f"{base_url}/products/stock-snapshot")
        if response.status_code == 200:
            stock_data = response.json()
            gold_drop_stock = next((p for p in stock_data if p.get('product_id') == 2), None)
            if gold_drop_stock:
                print(f"   Gold Drop Oil stock: {gold_drop_stock['stock']}")
                print(f"   Stock value: ₹{gold_drop_stock['stock_value']}")
                print(f"   All stock data: {json.dumps(gold_drop_stock, indent=2)}")
            else:
                print("   Gold Drop Oil not found in stock snapshot")
        else:
            print(f"   Error: {response.status_code}")
    except Exception as e:
        print(f"   Request failed: {e}")

    # Check individual product ledger
    print("\n3. /ledger/stock/2 endpoint:")
    try:
        response = requests.get(f"{base_url}/ledger/stock/2")
        if response.status_code == 200:
            ledger_data = response.json()
            print(f"   Current stock: {ledger_data['current_stock']}")
            print(f"   Opening stock: {ledger_data['opening_stock']}")
            print(f"   Total purchases: {ledger_data['total_purchases']}")
            print(f"   Total sales: {ledger_data['total_sales']}")

            if ledger_data.get('history') and len(ledger_data['history']) > 0:
                print(f"   Recent history:")
                for tx in ledger_data['history'][:3]:
                    print(f"     {tx['date'][:10]}: {tx['transaction_type']} {abs(tx['quantity'])} -> Stock: {tx['stock_after_transaction']}")
        else:
            print(f"   Error: {response.status_code}")
    except Exception as e:
        print(f"   Request failed: {e}")

if __name__ == "__main__":
    # Wait a bit for server to be ready
    time.sleep(2)
    check_api_responses()
