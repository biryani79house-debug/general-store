#!/usr/bin/env python3
"""
Script to add the missing 'proportion' and 'unit_price' columns to the sales table.
This handles the schema migration without losing existing data.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import text, create_engine

load_dotenv()

USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set in environment variables!")
        exit(1)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)

def add_missing_columns():
    """Add the proportion and unit_price columns to the sales table"""
    try:
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()

            try:
                # Add proportion column (nullable string)
                try:
                    conn.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS proportion VARCHAR"))
                    print("✅ Added 'proportion' column to sales table")
                except Exception as e:
                    print(f"⚠️ Could not add proportion column: {e}")
                    # Continue with other columns

                # Add unit_price column (nullable float)
                try:
                    conn.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS unit_price FLOAT"))
                    print("✅ Added 'unit_price' column to sales table")
                except Exception as e:
                    print(f"⚠️ Could not add unit_price column: {e}")

                # Commit the transaction
                trans.commit()
                print("✅ Database migration completed successfully")

            except Exception as e:
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                raise

    except Exception as e:
        print(f"❌ Database connection error: {e}")

if __name__ == "__main__":
    add_missing_columns()
