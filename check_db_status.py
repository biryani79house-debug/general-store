#!/usr/bin/env python3
"""
Check PostgreSQL database status
"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
POSTGRES_URL = os.getenv('DATABASE_URL')

try:
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()

    print("✅ Connected to PostgreSQL successfully")

    # Check what tables exist
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cursor.fetchall()

    print(f"\nTables in database ({len(tables)}):")
    for table in tables:
        print(f"  - {table[0]}")

    # Check each table's record count
    for table_name in ['users', 'products', 'categories', 'sales', 'purchases']:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"{table_name}: {count} records")
        except Exception as e:
            print(f"{table_name}: Error - {e}")

    conn.close()

except Exception as e:
    print(f"❌ Database connection failed: {e}")
