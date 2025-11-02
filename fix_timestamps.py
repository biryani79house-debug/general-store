#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, update
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta

# Load environment variables
load_dotenv()

# Use SQLite for local development, PostgreSQL for production
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if USE_SQLITE else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fix_timestamps():
    db = SessionLocal()
    try:
        print("🔧 Starting timestamp fix...")

        # For SQLite, we need to handle timestamps differently
        if USE_SQLITE:
            print("📱 Using SQLite - timestamps are stored as text, need manual conversion")

            # Get all sales and add 5.5 hours
            sales = db.execute(text("SELECT id, sale_date FROM sales")).fetchall()
            for sale in sales:
                sale_id, sale_date = sale
                if sale_date:
                    # Parse the datetime string and add 5.5 hours
                    try:
                        dt = datetime.fromisoformat(str(sale_date))
                        fixed_dt = dt + timedelta(hours=5, minutes=30)
                        db.execute(text("UPDATE sales SET sale_date = ? WHERE id = ?"), (fixed_dt, sale_id))
                    except Exception as e:
                        print(f"❌ Error fixing sale {sale_id}: {e}")

            # Get all purchases and add 5.5 hours
            purchases = db.execute(text("SELECT id, purchase_date FROM purchases")).fetchall()
            for purchase in purchases:
                purchase_id, purchase_date = purchase
                if purchase_date:
                    try:
                        dt = datetime.fromisoformat(str(purchase_date))
                        fixed_dt = dt + timedelta(hours=5, minutes=30)
                        db.execute(text("UPDATE purchases SET purchase_date = ? WHERE id = ?"), (fixed_dt, purchase_id))
                    except Exception as e:
                        print(f"❌ Error fixing purchase {purchase_id}: {e}")

            # Get all products created_at and add 5.5 hours
            products = db.execute(text("SELECT id, created_at FROM products")).fetchall()
            for product in products:
                product_id, created_at = product
                if created_at:
                    try:
                        dt = datetime.fromisoformat(str(created_at))
                        fixed_dt = dt + timedelta(hours=5, minutes=30)
                        db.execute(text("UPDATE products SET created_at = ? WHERE id = ?"), (fixed_dt, product_id))
                    except Exception as e:
                        print(f"❌ Error fixing product {product_id}: {e}")

            # Get all categories created_at and add 5.5 hours
            categories = db.execute(text("SELECT id, created_at FROM categories")).fetchall()
            for category in categories:
                category_id, created_at = category
                if created_at:
                    try:
                        dt = datetime.fromisoformat(str(created_at))
                        fixed_dt = dt + timedelta(hours=5, minutes=30)
                        db.execute(text("UPDATE categories SET created_at = ? WHERE id = ?"), (fixed_dt, category_id))
                    except Exception as e:
                        print(f"❌ Error fixing category {category_id}: {e}")

            # Get all users created_at and add 5.5 hours
            users = db.execute(text("SELECT id, created_at FROM users")).fetchall()
            for user in users:
                user_id, created_at = user
                if created_at:
                    try:
                        dt = datetime.fromisoformat(str(created_at))
                        fixed_dt = dt + timedelta(hours=5, minutes=30)
                        db.execute(text("UPDATE users SET created_at = ? WHERE id = ?"), (fixed_dt, user_id))
                    except Exception as e:
                        print(f"❌ Error fixing user {user_id}: {e}")

        else:
            print("🐘 Using PostgreSQL - using INTERVAL to add 5.5 hours")

            # For PostgreSQL, we can use INTERVAL
            db.execute(text("UPDATE sales SET sale_date = sale_date + INTERVAL '5 hours 30 minutes'"))
            db.execute(text("UPDATE purchases SET purchase_date = purchase_date + INTERVAL '5 hours 30 minutes'"))
            db.execute(text("UPDATE products SET created_at = created_at + INTERVAL '5 hours 30 minutes'"))
            db.execute(text("UPDATE categories SET created_at = created_at + INTERVAL '5 hours 30 minutes'"))
            db.execute(text("UPDATE users SET created_at = created_at + INTERVAL '5 hours 30 minutes'"))

        db.commit()
        print("✅ Timestamp fix completed successfully!")

        # Verify the fix
        print("\n=== VERIFICATION ===")
        purchase_4 = db.execute(text("SELECT id, purchase_date FROM purchases WHERE id = 4")).fetchone()
        if purchase_4:
            print(f"Purchase ID 4 after fix: {purchase_4[1]}")

    except Exception as e:
        print(f"❌ Error during timestamp fix: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_timestamps()
