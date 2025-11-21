import csv
import json
import os
from datetime import datetime, timezone, timedelta

# Import the same configuration as main.py
from dotenv import load_dotenv
load_dotenv()

USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
    from sqlalchemy import create_engine
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/kirana_store")
    from sqlalchemy import create_engine
    # For PostgreSQL, set timezone to IST (Asia/Kolkata) to match stored timestamps
    engine = create_engine(DATABASE_URL, connect_args={"options": "-c timezone=Asia/Kolkata"})

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def test_import_purchase_record():
    """Test that import creates purchase records"""
    print("🧪 Testing import purchase record creation...")

    # Check current max purchase ID
    max_purchase_id = db.execute(text("SELECT MAX(id) FROM purchases")).scalar()
    print(f"Current max purchase ID: {max_purchase_id}")

    # Insert a test product and purchase record (simulating import logic)
    product_id = 104
    name = "Test Product"
    purchase_price = 100.0
    stock = 10.0

    try:
        # Insert product (this would normally be done by the import script)
        db.execute(text("""
            INSERT INTO products
            (id, name, purchase_price, selling_price, unit_type, stock, initial_stock)
            VALUES
            (:id, :name, :purchase_price, :selling_price, :unit_type, :stock, 0)
        """), {
            "id": product_id,
            "name": name,
            "purchase_price": purchase_price,
            "selling_price": 120.0,
            "unit_type": "kgs",
            "stock": stock
        })

        # Create purchase record (this is what our import script does)
        total_cost = stock * purchase_price
        next_purchase_id = (max_purchase_id or 0) + 1
        admin_user = db.execute(text("SELECT id FROM users WHERE username = 'raza123'")).fetchone()
        user_id = admin_user[0] if admin_user else 1

        db.execute(text("""
            INSERT INTO purchases (id, product_id, quantity, total_cost, purchase_date, created_by)
            VALUES (:id, :product_id, :quantity, :total_cost, CURRENT_TIMESTAMP, :created_by)
        """), {
            "id": next_purchase_id,
            "product_id": product_id,
            "quantity": stock,
            "total_cost": total_cost,
            "created_by": user_id
        })

        # Verify purchase record was created
        purchase_record = db.execute(text("""
            SELECT id, product_id, quantity, total_cost FROM purchases WHERE id = :id
        """), {"id": next_purchase_id}).fetchone()

        if purchase_record:
            print(f"✅ Purchase record created: {purchase_record}")
            print(f"   Purchase ID: {purchase_record[0]}")
            print(f"   Product ID: {purchase_record[1]}")
            print(f"   Quantity: {purchase_record[2]}")
            print(f"   Total Cost: ₹{purchase_record[3]:.2f}")
        else:
            print("❌ Purchase record not found")

        db.commit()

    except Exception as e:
        print(f"❌ Test failed: {e}")
        db.rollback()

    finally:
        db.close()

if __name__ == "__main__":
    test_import_purchase_record()
