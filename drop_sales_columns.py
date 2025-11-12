#!/usr/bin/env python3
"""
Script to drop proportion and unit_price columns from the sales table.
Run this script to remove the unwanted columns from the PostgreSQL database.
"""

import os
import sys
sys.path.append('.')
from main import SessionLocal
from sqlalchemy import text

def drop_sales_columns():
    """Drop proportion and unit_price columns from sales table"""
    db = SessionLocal()
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        print("✅ Database connected successfully")

        # Check if columns exist before dropping them
        try:
            # Try to select from the columns to see if they exist
            result = db.execute(text("SELECT proportion, unit_price FROM sales LIMIT 1"))
            print("📋 Found proportion and unit_price columns - proceeding with drop")
        except Exception as e:
            print(f"⚠️ Columns may not exist: {e}")
            print("🔄 Continuing with drop operation...")

        # Drop the proportion column
        try:
            db.execute(text("ALTER TABLE sales DROP COLUMN IF EXISTS proportion"))
            print("✅ Dropped proportion column from sales table")
        except Exception as e:
            print(f"❌ Error dropping proportion column: {e}")

        # Drop the unit_price column
        try:
            db.execute(text("ALTER TABLE sales DROP COLUMN IF EXISTS unit_price"))
            print("✅ Dropped unit_price column from sales table")
        except Exception as e:
            print(f"❌ Error dropping unit_price column: {e}")

        # Commit the changes
        db.commit()
        print("✅ All changes committed successfully")

        # Verify the columns are gone
        try:
            result = db.execute(text("SELECT id, bill_id, product_id, quantity, total_amount, sale_date, created_by, customer_name, customer_phone, customer_address FROM sales LIMIT 1"))
            columns = result.keys()
            print(f"📋 Remaining columns in sales table: {list(columns)}")
        except Exception as e:
            print(f"❌ Error verifying columns: {e}")

    except Exception as e:
        db.rollback()
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🗑️ Starting column drop operation...")
    print("⚠️ This will permanently remove proportion and unit_price columns from the sales table")
    print("Press Enter to continue or Ctrl+C to cancel...")

    try:
        input()
        drop_sales_columns()
        print("✅ Column drop operation completed!")
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
