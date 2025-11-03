#!/usr/bin/env python3
"""
Script to renumber sales IDs in serial order (1, 2, 3, ...) without gaps.
This will update the sales table to have consecutive IDs starting from 1.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import sessionmaker

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

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def renumber_sales_ids():
    """Renumber all sales IDs to be consecutive starting from 1"""
    try:
        with SessionLocal() as db:
            # Get all sales records ordered by current ID
            sales = db.execute(text("SELECT id FROM sales ORDER BY id")).fetchall()
            print(f"📊 Found {len(sales)} sales records")

            if not sales:
                print("ℹ️ No sales records to renumber")
                return

            # Show current IDs
            current_ids = [row[0] for row in sales]
            print(f"📋 Current sales IDs: {current_ids}")

            # Create a mapping of old_id -> new_id
            id_mapping = {}
            for new_id, (old_id,) in enumerate(sales, start=1):
                id_mapping[old_id] = new_id

            print(f"🔄 ID mapping: {id_mapping}")

            # Temporarily disable foreign key constraints
            print("🔧 Disabling foreign key constraints...")
            db.execute(text("SET CONSTRAINTS ALL DEFERRED"))

            # Update sales records with new consecutive IDs
            print("📝 Renumbering sales records...")
            for old_id, new_id in id_mapping.items():
                if old_id != new_id:
                    # Update the sales record
                    db.execute(
                        text("UPDATE sales SET id = :new_id WHERE id = :old_id"),
                        {"new_id": new_id, "old_id": old_id}
                    )
                    print(f"  Updated sale ID: {old_id} → {new_id}")

            # Reset the sequence to start from the next available ID
            max_id = len(sales)
            print(f"🔢 Resetting sequence to start from {max_id + 1}")

            if USE_SQLITE:
                # For SQLite, reset the autoincrement
                db.execute(text("DELETE FROM sqlite_sequence WHERE name='sales'"))
                db.execute(text("INSERT INTO sqlite_sequence (name, seq) VALUES ('sales', :max_id)"), {"max_id": max_id})
            else:
                # For PostgreSQL, reset the sequence
                db.execute(text("SELECT setval('sales_id_seq', :max_id)"), {"max_id": max_id})

            # Re-enable constraints
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))

            # Cluster the table to reorder physically by ID
            print("🔄 Clustering table to reorder rows physically by ID...")
            db.execute(text("CLUSTER sales USING sales_pkey"))

            # Commit all changes
            db.commit()

            print("✅ Sales IDs renumbered successfully!")
            print(f"📋 New sales IDs: {list(range(1, len(sales) + 1))}")

            # Verify the changes
            print("\n🔍 Verification:")
            result = db.execute(text("SELECT id FROM sales ORDER BY id")).fetchall()
            final_ids = [row[0] for row in result]
            print(f"✅ Final sales IDs: {final_ids}")

            # Check if they're consecutive
            expected_ids = list(range(1, len(final_ids) + 1))
            if final_ids == expected_ids:
                print("🎉 SUCCESS: All sales IDs are now in perfect serial order!")
            else:
                print(f"⚠️ WARNING: IDs are not perfectly consecutive. Expected: {expected_ids}, Got: {final_ids}")

    except Exception as e:
        print(f"❌ Renumbering failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()

if __name__ == "__main__":
    renumber_sales_ids()
