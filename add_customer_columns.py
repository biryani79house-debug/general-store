#!/usr/bin/env python3
"""
Migration script to add customer_name and customer_phone columns to the sales table.
Run this script once to update the database schema.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Use SQLite for local development, PostgreSQL for production
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
    print("📱 Using SQLite database for local development")
else:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL not set in environment variables!")
        exit(1)
    else:
        print(f"📡 Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Local database'}")

# Create engine
engine = create_engine(DATABASE_URL)

def add_customer_columns():
    """Add customer_name and customer_phone columns to sales table"""
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'sales' AND column_name IN ('customer_name', 'customer_phone')"))
            existing_columns = [row[0] for row in result.fetchall()]

            if 'customer_name' not in existing_columns:
                print("📝 Adding customer_name column to sales table...")
                conn.execute(text("ALTER TABLE sales ADD COLUMN customer_name VARCHAR"))
                print("✅ customer_name column added successfully")
            else:
                print("✅ customer_name column already exists")

            if 'customer_phone' not in existing_columns:
                print("📝 Adding customer_phone column to sales table...")
                conn.execute(text("ALTER TABLE sales ADD COLUMN customer_phone VARCHAR"))
                print("✅ customer_phone column added successfully")
            else:
                print("✅ customer_phone column already exists")

            conn.commit()
            print("🎉 Database migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_customer_columns()
