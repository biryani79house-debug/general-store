#!/usr/bin/env python3
"""
Add missing columns to PostgreSQL database
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

print("🔄 Adding missing columns to users table...")

with engine.connect() as connection:
    try:
        # Add create_category column
        try:
            connection.execute(text("ALTER TABLE users ADD COLUMN create_category BOOLEAN DEFAULT TRUE"))
            print("✅ Added create_category column")
        except Exception as e:
            print(f"⚠️ create_category column may already exist: {e}")

        # Add delete_category column
        try:
            connection.execute(text("ALTER TABLE users ADD COLUMN delete_category BOOLEAN DEFAULT TRUE"))
            print("✅ Added delete_category column")
        except Exception as e:
            print(f"⚠️ delete_category column may already exist: {e}")

        # Update existing users to have these permissions if they don't already
        try:
            connection.execute(text("UPDATE users SET create_category = TRUE WHERE create_category IS NULL"))
            connection.execute(text("UPDATE users SET delete_category = TRUE WHERE delete_category IS NULL"))
            print("✅ Updated existing users with default permissions")
        except Exception as e:
            print(f"⚠️ Could not update existing users: {e}")

        # Commit the changes
        connection.commit()

        print("✅ Migration completed successfully!")

        # Verify the columns were added
        result = connection.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users' AND column_name IN ('create_category', 'delete_category')
            ORDER BY column_name
        """)).fetchall()

        added_columns = [row[0] for row in result]
        print(f"🔍 Verification: Columns now present: {added_columns}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        connection.rollback()
        raise

print("🎉 Database migration completed!")
