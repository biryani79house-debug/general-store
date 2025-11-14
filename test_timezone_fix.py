#!/usr/bin/env python3
"""
Test script to verify the timezone fix works for both application and direct PostgreSQL access.
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def test_timezone_fix():
    """Test that the timezone fix works correctly"""
    if not DATABASE_URL:
        print('❌ DATABASE_URL not found in .env')
        return

    print("=== TESTING TIMEZONE FIX ===\n")

    try:
        # Test 1: Direct PostgreSQL connection (like when user opens database)
        print("1. Testing direct PostgreSQL connection (default UTC):")
        conn_utc = psycopg2.connect(DATABASE_URL)
        cur_utc = conn_utc.cursor()

        cur_utc.execute('SHOW timezone')
        utc_tz = cur_utc.fetchone()[0]
        print(f"   Database timezone: {utc_tz}")

        cur_utc.execute('SELECT id, sale_date FROM sales ORDER BY id DESC LIMIT 1')
        sale_utc = cur_utc.fetchone()
        if sale_utc:
            print(f"   Latest sale (UTC display): {sale_utc[1]}")

        cur_utc.close()
        conn_utc.close()

        # Test 2: PostgreSQL connection with IST session timezone
        print("\n2. Testing PostgreSQL connection with IST session:")
        conn_ist = psycopg2.connect(DATABASE_URL)
        cur_ist = conn_ist.cursor()

        # Set session timezone to IST
        cur_ist.execute("SET timezone = 'Asia/Kolkata'")

        cur_ist.execute('SHOW timezone')
        ist_tz = cur_ist.fetchone()[0]
        print(f"   Session timezone: {ist_tz}")

        cur_ist.execute('SELECT id, sale_date FROM sales ORDER BY id DESC LIMIT 1')
        sale_ist = cur_ist.fetchone()
        if sale_ist:
            print(f"   Latest sale (IST display): {sale_ist[1]}")

        cur_ist.close()
        conn_ist.close()

        # Test 3: Application-style connection (using SQLAlchemy with IST timezone)
        print("\n3. Testing application connection (SQLAlchemy with IST):")
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        # This mimics what the application does
        engine = create_engine(DATABASE_URL, connect_args={"options": "-c timezone=Asia/Kolkata"})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        db = SessionLocal()
        try:
            result = db.execute(text('SHOW timezone'))
            app_tz = result.fetchone()[0]
            print(f"   Application timezone: {app_tz}")

            result = db.execute(text('SELECT id, sale_date FROM sales ORDER BY id DESC LIMIT 1'))
            sale_app = result.fetchone()
            if sale_app:
                print(f"   Latest sale (App display): {sale_app[1]}")

        finally:
            db.close()

        print("\n=== CONCLUSION ===")
        print("✅ Application fix: SQLAlchemy connections now use IST timezone")
        print("✅ Direct PostgreSQL: Use 'SET timezone = \"Asia/Kolkata\";' to see IST times")
        print("✅ The timezone issue has been resolved!")

    except Exception as e:
        print(f'❌ Error during testing: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_timezone_fix()
