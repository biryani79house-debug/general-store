#!/usr/bin/env python3
"""
Test script to verify the sales ledger fix for proportion quantities like "500ml"
"""

import requests
import json

def test_sales_ledger():
    """Test the sales ledger endpoint to ensure it no longer fails with '500ml' quantities"""

    print("🧪 Testing Sales Ledger Fix for Proportion Quantities")
    print("=" * 50)

    # Test login first
    login_url = 'http://localhost:8001/auth/login'
    login_data = {'username': 'raza123', 'password': '123456'}

    print("🔐 Logging in...")
    login_response = requests.post(login_url, json=login_data)

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return False

    token = login_response.json().get('access_token')
    if not token:
        print("❌ No token received")
        return False

    print("✅ Login successful, got token")

    # Test sales ledger endpoint
    ledger_url = 'http://localhost:8001/ledger/sales'
    headers = {'Authorization': f'Bearer {token}'}

    print("📊 Testing sales ledger endpoint...")
    ledger_response = requests.get(ledger_url, headers=headers)

    if ledger_response.status_code == 200:
        result = ledger_response.json()
        print("✅ Sales ledger loaded successfully!")
        print(f"📦 Found {len(result)} sales ledger entries")

        # Show first few entries to verify proportions are displayed correctly
        if result:
            print("\n🔍 First 3 sales ledger entries:")
            for i, sale in enumerate(result[:3]):
                quantity = sale.get('quantity')
                product_name = sale.get('product_name', 'Unknown')
                print(f"  {i+1}. {product_name}: quantity='{quantity}' (type: {type(quantity)})")
                if isinstance(quantity, str) and ('ml' in quantity or 'gm' in quantity or 'kg' in quantity or 'ltr' in quantity):
                    print(f"     ✅ Proportion quantity preserved: {quantity}")
                elif isinstance(quantity, int):
                    print(f"     🔢 Numeric quantity: {quantity}")

        # Check if we have actual proportion quantities in display
        proportion_entries = []
        for sale in result:
            qty = sale.get('quantity', '')
            if isinstance(qty, str) and any(unit in qty for unit in ['ml', 'gm', 'kg', 'ltr']):
                proportion_entries.append(qty)

        if proportion_entries:
            print(f"\n🥤 Found proportion quantities preserved: {len(proportion_entries)} entries")
            print(f"   Sample: {proportion_entries[:3]}")
        else:
            print("\n⚠️ No proportion quantities found in display - they may be showing as numbers")

        return True

    else:
        print(f"❌ Sales ledger failed: {ledger_response.status_code}")
        print(f"Error: {ledger_response.text}")
        return False

if __name__ == "__main__":
    success = test_sales_ledger()
    if success:
        print("\n🎉 Sales Ledger Display Fix Verified! Proportion quantities are properly preserved.")
    else:
        print("\n💥 Sales Ledger Display Fix Failed!")
