#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"DATABASE_URL found: {DATABASE_URL is not None}")

if DATABASE_URL:
    print(f"Connecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")

    engine = create_engine(DATABASE_URL, echo=False)
    session = Session(engine)

    try:
        print("\n=== DATABASE STATUS CHECK ===")

        # Test connection
        session.execute(text("SELECT 1"))
        print("✅ Database connection successful")

        # Check categories table exists and count
        try:
            result = session.execute(text('SELECT COUNT(*) FROM categories'))
            category_count = result.fetchone()[0]
            print(f"Categories count: {category_count}")
        except Exception as e:
            print(f"❌ Error checking categories: {e}")

        # Check products table exists and count
        try:
            result = session.execute(text('SELECT COUNT(*) FROM products'))
            product_count = result.fetchone()[0]
            print(f"Products count: {product_count}")
        except Exception as e:
            print(f"❌ Error checking products: {e}")

        # Check users table exists and count
        try:
            result = session.execute(text('SELECT COUNT(*) FROM users'))
            user_count = result.fetchone()[0]
            print(f"Users count: {user_count}")
        except Exception as e:
            print(f"❌ Error checking users: {e}")

        print("=== CHECK COMPLETE ===")

    finally:
        session.close()
else:
    print("❌ No DATABASE_URL found")
