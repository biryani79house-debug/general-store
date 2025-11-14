#!/usr/bin/env python3
"""
Check what sales data exists for Gold Drop Oil and what proportions it's using
"""
import requests
import json

def check_sales_data():
    base_url = "http://localhost:8000"

    # Check sales data
    print("🔍 Checking sales data for Gold Drop Oil (product_id: 2)")
    print("=" * 60)

    try:
        response = requests.get(f"{base_url}/ledger/sales?product_id=2")
        if response.status_code == 200:
            sales_data = response.json()
            print(f"✅ Found {len(sales_data)} sales records for Gold Drop Oil")

            total_quantity_sold = 0
            for sale in sales_data:
                print(f"  Sale ID {sale['sale_id']}: {sale['quantity']} at ₹{sale['unit_price']} each")
                total_quantity_sold += sale['quantity']

            print(f"\n  Total quantity sold: {total_quantity_sold}")
        else:
            print(f"❌ Could not fetch sales data: {response.status_code}")

    except Exception as e:
        print(f"❌ Could not fetch sales data: {e}")

    # Check product data to see proportion prices
    print("\n🔍 Checking proportion prices for Gold Drop Oil")
    print("-" * 60)

    try:
        response = requests.get(f"{base_url}/products")
        if response.status_code == 200:
            products = response.json()
            gold_drop = next((p for p in products if p.get('id') == 2), None)
            if gold_drop:
                print("Gold Drop Oil proportions:")
                print(f"  '1ltr': ₹{gold_drop.get('proportion_prices', {}).get('1ltr', 'N/A')}")
                print(f"  '500ml': ₹{gold_drop.get('proportion_prices', {}).get('500ml', 'N/A')}")
                print(f"Available proportions: {gold_drop.get('proportions', [])}")
                print(f"Current stock: {gold_drop['stock']}")
            else:
                print("Gold Drop Oil not found")
        else:
            print(f"Could not fetch products: {response.status_code}")

    except Exception as e:
        print(f"Could not fetch products: {e}")

if __name__ == "__main__":
    check_sales_data()
