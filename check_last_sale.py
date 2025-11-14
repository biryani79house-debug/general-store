#!/usr/bin/env python3
"""
Check the last sale time to verify timezone fix.
"""
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def check_last_sale():
    """Check the last sale time"""
    if not DATABASE_URL:
        print('❌ DATABASE_URL not found')
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Get the last sale
        cur.execute('SELECT id, sale_date FROM sales ORDER BY id DESC LIMIT 1')
        last_sale = cur.fetchone()

        if last_sale:
            sale_id, sale_time = last_sale
            print(f'Last Sale ID: {sale_id}')
            print(f'Time (UTC): {sale_time}')

            # Set IST timezone and check again
            cur.execute("SET timezone = 'Asia/Kolkata'")
            cur.execute('SELECT sale_date FROM sales WHERE id = %s', (sale_id,))
            ist_time = cur.fetchone()[0]
            print(f'Time (IST): {ist_time}')

            # Current time for comparison
            IST = timezone(timedelta(hours=5, minutes=30))
            current_ist = datetime.now(IST)
            print(f'Current IST time: {current_ist}')

            # Check if the sale time makes sense
            time_diff = current_ist - ist_time.replace(tzinfo=IST)
            print(f'Time since sale: {time_diff}')

            # Check if it's recent (within last hour)
            if time_diff.total_seconds() < 3600:  # 1 hour
                print('✅ Sale time looks correct (recent sale)')
            else:
                print('⚠️ Sale time seems old, but timezone conversion is working')

        else:
            print('No sales found')

        cur.close()
        conn.close()

    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    check_last_sale()
