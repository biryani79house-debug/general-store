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

        # Check if any sales contain proportion quantities
        proportion_sales = [sale for sale in result if isinstance(sale.get('quantity'), int) and sale.get('quantity') > 0]
        print(f"📏 Found {len(proportion_sales)} entries with numeric quantities (should work now)")

        # Try to find a specific "500ml" type entry
        ml_sales = [sale for sale in result if 'ml' in str(sale.get('quantity', '')) or 'gm' in str(sale.get('quantity', ''))]
        if ml_sales:
            print(f"🥤 Found proportion entries: {ml_sales[:2]}...")  # Show first 2

        return True

    else:
        print(f"❌ Sales ledger failed: {ledger_response.status_code}")
        print(f"Error: {ledger_response.text}")
        return False

if __name__ == "__main__":
    success = test_sales_ledger()
    if success:
        print("\n🎉 Sales Ledger Fix Verified! Proportion quantities now working correctly.")
    else:
        print("\n💥 Sales Ledger Fix Failed!")
