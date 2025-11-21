import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
load_dotenv()

USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
    from sqlalchemy import create_engine
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    DATABASE_URL = os.getenv("DATABASE_URL")
    from sqlalchemy import create_engine
    engine = create_engine(DATABASE_URL, connect_args={"options": "-c timezone=Asia/Kolkata"})

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def migrate_existing_imported_products():
    """
    Migrate all existing imported products that have initial_stock > 0
    to create purchase records and set initial_stock to 0
    """
    print("🛠️  Starting migration of existing imported products...")

    try:
        # Find all products that have initial_stock > 0 (these are the imported ones)
        products_with_initial_stock = db.execute(text("""
            SELECT id, name, stock, initial_stock, purchase_price
            FROM products
            WHERE initial_stock > 0
            ORDER BY id
        """)).fetchall()

        print(f"📊 Found {len(products_with_initial_stock)} products with initial stock to migrate")

        # Get current max purchase ID
        max_purchase_id = db.execute(text("SELECT MAX(id) FROM purchases")).scalar()
        next_purchase_id = (max_purchase_id or 0) + 1

        # Get admin user for created_by
        admin_user = db.execute(text("SELECT id FROM users WHERE username = 'raza123'")).fetchone()
        user_id = admin_user[0] if admin_user else 1

        migrated_count = 0

        for product in products_with_initial_stock:
            product_id, product_name, stock, initial_stock, purchase_price = product

            print(f"🔄 Migrating: {product_name} (ID: {product_id})")
            print(f"   Current: initial_stock={initial_stock}, stock={stock}")

            # Create purchase record for the initial stock
            total_cost = initial_stock * purchase_price

            db.execute(text("""
                INSERT INTO purchases (id, product_id, quantity, total_cost, purchase_date, created_by)
                VALUES (:id, :product_id, :quantity, :total_cost, CURRENT_TIMESTAMP, :created_by)
            """), {
                "id": next_purchase_id,
                "product_id": product_id,
                "quantity": initial_stock,
                "total_cost": total_cost,
                "created_by": user_id
            })

            print(f"   ✅ Created purchase record #{next_purchase_id} for ₹{total_cost:.2f}")

            # Set initial_stock to 0
            db.execute(text("""
                UPDATE products SET initial_stock = 0 WHERE id = :product_id
            """), {"product_id": product_id})

            print(f"   ✅ Set initial_stock to 0")

            next_purchase_id += 1
            migrated_count += 1

        db.commit()
        print(f"\n🎉 Migration completed! Migrated {migrated_count} products.")
        print("All imported products now have proper purchase records!")

    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    print(f"📊 Using database: {'SQLite (dev)' if USE_SQLITE else 'PostgreSQL (prod)'}")
    migrate_existing_imported_products()
