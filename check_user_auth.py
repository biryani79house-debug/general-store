#!/usr/bin/env python3
"""
Check user authentication in the database
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import bcrypt

# Load environment variables
load_dotenv()

USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

print(f"Database URL: {DATABASE_URL}")
print(f"Using SQLite: {USE_SQLITE}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if USE_SQLITE else {})
session = Session(engine)

print("\n🔍 Checking users in database...")

users = session.execute(text("SELECT id, username, email, password_hash, sales, purchase, create_product, delete_product, create_category, delete_category, sales_ledger, purchase_ledger, stock_ledger, profit_loss, opening_stock, user_management, is_active FROM users")).fetchall()

if not users:
    print("❌ No users found in database")
else:
    print(f"✅ Found {len(users)} users:")
    for user in users:
        print(f"   ID: {user[0]}")
        print(f"   Username: {user[1]}")
        print(f"   Email: {user[2]}")
        print("   Permissions:")
        print(f"     sales: {user[4]}, purchase: {user[5]}, create_product: {user[6]}, delete_product: {user[7]}")
        print(f"     create_category: {user[8]}, delete_category: {user[9]}")
        print(f"     sales_ledger: {user[10]}, purchase_ledger: {user[11]}, stock_ledger: {user[12]}")
        print(f"     profit_loss: {user[13]}, opening_stock: {user[14]}, user_management: {user[15]}")
        print(f"   Is active: {user[16]}")

        # Test password authentication
        test_password = "123456"
        try:
            if bcrypt.checkpw(test_password.encode('utf-8'), user[3].encode('utf-8') if user[3] else b""):
                print(f"   ✅ Password '123456' matches for {user[1]}")
            else:
                print(f"   ❌ Password '123456' does not match for {user[1]}")
        except:
            print(f"   ⚠️ Password verification failed for {user[1]}")
            # Check if plain text
            if user[3] == test_password:
                print(f"   ✅ Password '123456' matches plain text for {user[1]}")

        test_password2 = "admin123"
        try:
            if bcrypt.checkpw(test_password2.encode('utf-8'), user[3].encode('utf-8') if user[3] else b""):
                print(f"   ✅ Password 'admin123' matches for {user[1]}")
            else:
                print(f"   ❌ Password 'admin123' does not match for {user[1]}")
        except:
            print(f"   ⚠️ Password verification failed for {user[1]}")
            if user[3] == test_password2:
                print(f"   ✅ Password 'admin123' matches plain text for {user[1]}")

        print("   ---")

session.close()
