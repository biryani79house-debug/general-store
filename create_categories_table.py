#!/usr/bin/env python3
"""
Migration script to create the categories table for the PostgreSQL database.
This table is referenced by the frontend for managing product categories.
"""

import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, DateTime, text
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
import bcrypt

# Load environment variables
load_dotenv()

# Use environment variable for database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not set. Please set DATABASE_URL environment variable.")
    print("Example: postgresql://username:password@host:port/database")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

# Base class for tables
Base = declarative_base()

# IST timezone import
from datetime import datetime, timezone, timedelta
IST = timezone(timedelta(hours=5, minutes=30))

class Category(Base):
    """Category table for organizing products"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(IST))

def main():
    """Create the categories table"""
    print("🏗️  Creating categories table...")

    try:
        # Create the categories table
        Base.metadata.create_all(bind=engine, tables=[Category.__table__])
        print("✅ Categories table created successfully!")

        # Test connection and get access to a session
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Check if table was created and insert default categories
        try:
            # Verify table exists by trying to query it
            result = db.execute(text("SELECT COUNT(*) FROM categories"))
            count = result.fetchone()[0]
            print(f"📊 Categories table verified - current count: {count}")

            # Insert some default categories if the table is empty
            if count == 0:
                print("🌱 Inserting default categories...")

                default_categories = [
                    "Groceries",
                    "Vegetables",
                    "Fruits",
                    "Dairy",
                    "Beverages",
                    "Snacks",
                    "Household",
                    "Personal Care",
                    "Bakery",
                    "Meat & Fish"
                ]

                for category_name in default_categories:
                    insert_sql = text("INSERT INTO categories (name, created_at) VALUES (:name, :created_at)")
                    db.execute(insert_sql, {
                        "name": category_name,
                        "created_at": datetime.now(IST)
                    })
                    print(f"✅ Added category: {category_name}")

                # Commit the transaction
                db.commit()
                print("🎉 All default categories inserted successfully!")
            else:
                print("ℹ️  Categories table already has data - skipping default insertion")

        except Exception as table_error:
            print(f"⚠️  Error during category insertion: {table_error}")
            db.rollback()

        finally:
            db.close()

        print("✅ Migration completed successfully!")
        print("\n📋 Summary:")
        print("  - Categories table created in PostgreSQL")
        print("  - Default categories added (if table was empty)")
        print("  - Frontend category management is now supported")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
