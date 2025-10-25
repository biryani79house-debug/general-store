#!/usr/bin/env python3
"""
Check user table schema in PostgreSQL
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Load environment variables
load_dotenv()

USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

print(f"Database URL: {DATABASE_URL}")
print(f"Using SQLite: {USE_SQLITE}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if USE_SQLITE else {})
session = Session(engine)

print("\n🔍 Checking users table schema...")

# Get column information
if USE_SQLITE:
    result = session.execute(text("PRAGMA table_info(users)")).fetchall()
    print("SQLite schema:")
    for col in result:
        print(f"  {col[1]} ({col[2]}) - default: {col[4]}")
else:
    try:
        result = session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)).fetchall()
        print("PostgreSQL schema:")
        for col in result:
            print(f"  {col[0]} ({col[1]}) - nullable: {col[2]}, default: {col[3]}")
    except Exception as e:
        print(f"❌ Error getting schema: {e}")
        result = []

print("\nExpected columns from User model:")
expected_columns = [
    'id', 'username', 'email', 'password_hash',
    'sales', 'purchase', 'create_product', 'delete_product',
    'create_category', 'delete_category',
    'sales_ledger', 'purchase_ledger', 'stock_ledger', 'profit_loss',
    'opening_stock', 'user_management', 'is_active', 'created_at'
]

for col in expected_columns:
    print(f"  {col}")

if not USE_SQLITE:
    actual_columns = [col[0] for col in result] if result else []
    print(f"\nActual columns in PostgreSQL: {actual_columns}")
    missing_columns = [col for col in expected_columns if col not in actual_columns]
    if missing_columns:
        print(f"❌ Missing columns: {missing_columns}")
    else:
        print("✅ All expected columns present")

session.close()
