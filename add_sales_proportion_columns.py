#!/usr/bin/env python3
"""
Add proportion and unit_price columns to sales table
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
    print("📱 Using SQLite - no migration needed")
    exit(0)
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

print(f"📡 Connecting to PostgreSQL: {DATABASE_URL.replace(DATABASE_URL.split('@')[0], '***') if '@' in DATABASE_URL else '***'}")

engine = create_engine(DATABASE_URL)

print("🔄 Adding proportion and unit_price columns to sales table...")

with engine.connect() as connection:
    try:
        # Add proportion column
        try:
            connection.execute(text("ALTER TABLE sales ADD COLUMN proportion VARCHAR(50)"))
            print("✅ Added proportion column")
        except Exception as e:
            print(f"⚠️ proportion column may already exist: {e}")

        # Add unit_price column
        try:
            connection.execute(text("ALTER TABLE sales ADD COLUMN unit_price FLOAT"))
            print("✅ Added unit_price column")
        except Exception as e:
            print(f"⚠️ unit_price column may already exist: {e}")

        # Commit the changes
        connection.commit()

        print("✅ Migration completed successfully!")

        # Verify the columns were added
        result = connection.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'sales' AND column_name IN ('proportion', 'unit_price')
            ORDER BY column_name
        """)).fetchall()

        added_columns = [row[0] for row in result]
        print(f"🔍 Verification: Columns now present: {added_columns}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        connection.rollback()
        raise

print("🎉 Database migration completed!")
