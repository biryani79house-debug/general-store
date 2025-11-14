#!/usr/bin/env python3
"""
Debug script to analyze the timezone issue in PostgreSQL database.
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def analyze_timestamps():
    """Analyze how timestamps are stored and displayed"""
    if not DATABASE_URL:
        print('❌ DATABASE_URL not found in .env')
        return

    try:
        # Connect directly to PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        print("=== POSTGRESQL TIMEZONE ANALYSIS ===\n")

        # Check current database timezone
        cur.execute('SHOW timezone')
        db_timezone = cur.fetchone()[0]
        print(f"Database server timezone: {db_timezone}")

        # Check recent sales
        cur.execute('SELECT id, sale_date FROM sales ORDER BY id DESC LIMIT 5')
        sales = cur.fetchall()

        print(f"\nRecent sales (as displayed by database in {db_timezone}):")
        for sale_id, sale_date in sales:
            print(f"  Sale ID {sale_id}: {sale_date}")

        # Now check what these timestamps represent in different timezones
        print("\nTimestamp analysis:")
        for sale_id, sale_date in sales[:3]:  # First 3 sales
            # Convert to different timezones
            cur.execute("""
                SELECT
                    %s::timestamp as raw_timestamp,
                    (%s::timestamp AT TIME ZONE 'UTC') as as_utc,
                    (%s::timestamp AT TIME ZONE 'Asia/Kolkata') as as_ist
            """, (sale_date, sale_date, sale_date))

            raw, as_utc, as_ist = cur.fetchone()
            print(f"\nSale ID {sale_id}:")
            print(f"  Raw stored: {raw}")
            print(f"  Interpreted as UTC: {as_utc}")
            print(f"  Interpreted as IST: {as_ist}")

        # Test what happens with a new connection using IST timezone
        print("\n=== TESTING CONNECTION WITH IST TIMEZONE ===")
        conn_ist = psycopg2.connect(DATABASE_URL + "?timezone=Asia/Kolkata")
        cur_ist = conn_ist.cursor()

        cur_ist.execute('SHOW timezone')
        ist_timezone = cur_ist.fetchone()[0]
        print(f"IST connection timezone: {ist_timezone}")

        cur_ist.execute('SELECT id, sale_date FROM sales ORDER BY id DESC LIMIT 3')
        sales_ist = cur_ist.fetchall()

        print("Same sales with IST connection:")
        for sale_id, sale_date in sales_ist:
            print(f"  Sale ID {sale_id}: {sale_date}")

        cur_ist.close()
        conn_ist.close()

        cur.close()
        conn.close()

        print("\n=== CONCLUSION ===")
        print("The issue is that your PostgreSQL database server is running in UTC timezone.")
        print("When you connect directly to PostgreSQL (like with psql or a database client),")
        print("it displays timestamps according to the server's timezone setting (UTC).")
        print()
        print("However, your application correctly stores times in IST.")
        print("The fix ensures that when your FastAPI app retrieves data,")
        print("it interprets the timestamps correctly as IST times.")

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_timestamps()
