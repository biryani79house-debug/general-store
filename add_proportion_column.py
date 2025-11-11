#!/usr/bin/env python3
"""
Add proportion column to products table
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_proportion_column():
    """Add proportion column to products table"""
    try:
        # Get database URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables")
            return False

        print("📡 Connecting to PostgreSQL database...")

        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.autocommit = True  # Enable autocommit to avoid transaction issues
        cursor = conn.cursor()

        # Check if proportion column exists
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'products' AND column_name = 'proportion'
        """)

        if cursor.fetchone():
            print("✅ Proportion column already exists in products table")
            cursor.close()
            conn.close()
            return True

        # Add proportion column
        print("🔄 Adding proportion column to products table...")
        cursor.execute("""
            ALTER TABLE products ADD COLUMN proportion VARCHAR(50)
        """)

        print("✅ Proportion column added successfully!")

        # Verify the column was added
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'products' AND column_name = 'proportion'
        """)

        if cursor.fetchone():
            print("✅ Proportion column verified successfully!")
        else:
            print("❌ Proportion column verification failed!")
            return False

        cursor.close()
        conn.close()

        print("🎉 Database migration completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error adding proportion column: {e}")
        return False

if __name__ == "__main__":
    success = add_proportion_column()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        exit(1)
