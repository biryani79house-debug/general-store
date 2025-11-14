#!/usr/bin/env python3
"""
Check the sales ledger API to see if times are displayed correctly.
"""
import requests
import json

def check_sales_ledger():
    """Check the sales ledger API endpoint"""
    print('=== CHECKING SALES LEDGER API ===\n')

    try:
        # Try to get sales ledger data
        response = requests.get('http://localhost:8000/ledger/sales', timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f'✅ API responded with {len(data)} sales records')

            if data:
                # Show first few sales
                print('\nFirst 3 sales from API:')
                for i, sale in enumerate(data[:3]):
                    sale_id = sale.get('sale_id')
                    date = sale.get('date')
                    print(f'Sale {i+1}: ID {sale_id}, Date: {date}')
            else:
                print('⚠️ No sales data returned')

        elif response.status_code == 401:
            print('🔒 API requires authentication - this is expected')
            print('The application is running but needs login credentials')

        else:
            print(f'❌ API returned status {response.status_code}: {response.text}')

    except requests.exceptions.ConnectionError:
        print('❌ Cannot connect to application server')
        print('The FastAPI server is not running')
        print('You need to start the server with: python main.py')
        print('\nIf the server is running elsewhere, update the URL in this script')

    except Exception as e:
        print(f'❌ Error checking API: {e}')

if __name__ == "__main__":
    check_sales_ledger()
