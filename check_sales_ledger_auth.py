#!/usr/bin/env python3
"""
Check the sales ledger API with authentication to verify timezone fix.
"""
import requests
import json

def login_and_check_sales():
    """Login to get token, then check sales ledger"""
    print('=== AUTHENTICATED SALES LEDGER CHECK ===\n')

    # Login credentials
    login_data = {
        "username": "raza123",
        "password": "123456"
    }

    try:
        # First, login to get token
        print('1. Logging in...')
        login_response = requests.post('http://localhost:8000/auth/login', json=login_data, timeout=5)

        if login_response.status_code != 200:
            print(f'❌ Login failed: {login_response.status_code} - {login_response.text}')
            return

        login_result = login_response.json()
        token = login_result.get('access_token')

        if not token:
            print('❌ No token received from login')
            return

        print('✅ Login successful, got token')

        # Now check sales ledger with authentication
        print('\n2. Checking sales ledger with authentication...')
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get('http://localhost:8000/ledger/sales', headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f'✅ Sales ledger API responded with {len(data)} records')

            if data:
                print('\nFirst 3 sales from ledger:')
                for i, sale in enumerate(data[:3]):
                    sale_id = sale.get('sale_id')
                    date = sale.get('date')
                    print(f'Sale {i+1}: ID {sale_id}, Date: {date}')

                # Check if times look correct (should be IST)
                first_sale_date = data[0].get('date')
                if first_sale_date:
                    print(f'\n✅ First sale date: {first_sale_date}')
                    print('This should now show correct IST time (not 5.5 hours behind)')
            else:
                print('⚠️ No sales data returned')

        else:
            print(f'❌ Sales ledger API failed: {response.status_code} - {response.text}')

    except requests.exceptions.ConnectionError:
        print('❌ Cannot connect to application server')
        print('Make sure the FastAPI server is running with: python main.py')

    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    login_and_check_sales()
