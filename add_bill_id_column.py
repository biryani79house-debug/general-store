#!/usr/bin/env python3
"""
Add bill_id column to sales table to group multiple products under one bill.
Each bill (transaction) will have a unique bill_id, regardless of number of products.
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

engine = create_engine(DATABASE_URL)

def add_bill_id_column():
    """Add bill_id column to sales table"""
    try:
        with engine.connect() as conn:
            # Check if bill_id column already exists
            if USE_SQLITE:
                # SQLite way to check columns
                result = conn.execute(text("PRAGMA table_info(sales)"))
                columns = [row[1] for row in result.fetchall()]
            else:
                # PostgreSQL way
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name='sales' AND column_name='bill_id'
                """))
                columns = [row[0] for row in result.fetchall()]

            if 'bill_id' in columns:
                print('✅ bill_id column already exists')
                return

            print('📝 Adding bill_id column to sales table...')

            # Add the bill_id column
            if USE_SQLITE:
                # SQLite doesn't support DEFAULT with expressions easily, so we'll add it without default first
                conn.execute(text('ALTER TABLE sales ADD COLUMN bill_id INTEGER'))
                # Then set bill_id = id for existing records (each existing sale becomes its own bill)
                conn.execute(text('UPDATE sales SET bill_id = id'))
            else:
                # PostgreSQL can add with default
                conn.execute(text('ALTER TABLE sales ADD COLUMN bill_id INTEGER DEFAULT 0'))
                # Then set bill_id = id for existing records
                conn.execute(text('UPDATE sales SET bill_id = id WHERE bill_id = 0'))

            conn.commit()
            print('✅ bill_id column added successfully')

            # Create index on bill_id for better performance
            try:
                conn.execute(text('CREATE INDEX idx_sales_bill_id ON sales(bill_id)'))
                conn.commit()
                print('✅ Index created on bill_id column')
            except Exception as idx_error:
                print(f'⚠️ Could not create index: {idx_error}')

            # Verify the changes
            result = conn.execute(text('SELECT COUNT(*) FROM sales WHERE bill_id IS NULL'))
            null_count = result.fetchone()[0]
            if null_count > 0:
                print(f'⚠️ WARNING: {null_count} sales records have NULL bill_id')
            else:
                print('✅ All sales records have bill_id assigned')

    except Exception as e:
        print(f'❌ Error adding bill_id column: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_bill_id_column()
