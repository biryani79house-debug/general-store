import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not set in environment variables!")
    sys.exit(1)

print("📡 Connecting to PostgreSQL database:", DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Remote database')

# Create engine
engine = create_engine(DATABASE_URL)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Get session
db = SessionLocal()

try:
    # First, check current products
    print("\n🔍 Checking current products...")
    products = db.execute(text("SELECT id, name, stock FROM products ORDER BY id")).fetchall()
    print("Current products:")
    for product in products:
        print(f"ID: {product[0]}, Name: {product[1]}, Stock: {product[2]}")

    # Check foreign keys
    print("\n📋 Checking sales and purchases referencing these products...")
    sales_refs = db.execute(text("SELECT product_id, COUNT(*) FROM sales GROUP BY product_id")).fetchall()
    purchase_refs = db.execute(text("SELECT product_id, COUNT(*) FROM purchases GROUP BY product_id")).fetchall()
    print("Sales references:", sales_refs)
    print("Purchase references:", purchase_refs)

    # Now renumber - Create new products and migrate references
    print("\n⚡ Starting renumbering...")

    # First, get data for current products
    product_data = {}
    old_to_new = {10: 1, 11: 2, 12: 3}

    for old_id in old_to_new.keys():
        product = db.execute(text("SELECT name, purchase_price, selling_price, unit_type, stock, initial_stock, created_at FROM products WHERE id = :id"), {"id": old_id}).first()
        if product:
            product_data[old_id] = product

    print("Found product data for:", list(product_data.keys()))

    # Temporarily disable foreign key checks by dropping them
    db.execute(text("ALTER TABLE purchases DROP CONSTRAINT purchases_product_id_fkey;"))
    db.execute(text("ALTER TABLE sales DROP CONSTRAINT sales_product_id_fkey;"))
    print("✅ Foreign key constraints dropped")

    # Update foreign keys first (from old to new ids)
    for old_id, new_id in old_to_new.items():
        # Update sales
        db.execute(text("UPDATE sales SET product_id = :new_id WHERE product_id = :old_id"), {"new_id": new_id, "old_id": old_id})
        # Update purchases
        db.execute(text("UPDATE purchases SET product_id = :new_id WHERE product_id = :old_id"), {"new_id": new_id, "old_id": old_id})
        print(f"✅ Updated foreign keys from product ID {old_id} to {new_id}")

    # Now update product IDs
    for old_id, new_id in old_to_new.items():
        db.execute(text("UPDATE products SET id = :new_id WHERE id = :old_id"), {"new_id": new_id, "old_id": old_id})
        print(f"✅ Updated product ID from {old_id} to {new_id}")

    # Reset sequence to start from 4
    db.execute(text("ALTER SEQUENCE products_id_seq RESTART WITH 4;"))
    print("✅ PostgreSQL sequence reset to 4")

    # Recreate foreign key constraints
    db.execute(text("ALTER TABLE purchases ADD CONSTRAINT purchases_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id);"))
    db.execute(text("ALTER TABLE sales ADD CONSTRAINT sales_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id);"))
    print("✅ Foreign key constraints recreated")

    db.commit()
    print("✅ Renumbering completed successfully!")

    # Verify changes
    print("\n🔍 Verifying changes...")
    products = db.execute(text("SELECT id, name, stock FROM products ORDER BY id")).fetchall()
    print("Updated products:")
    for product in products:
        print(f"ID: {product[0]}, Name: {product[1]}, Stock: {product[2]}")

    # Check sales and purchases
    sales_count = db.execute(text("SELECT COUNT(*) FROM sales")).scalar()
    purchase_count = db.execute(text("SELECT COUNT(*) FROM purchases")).scalar()
    print(f"Sales records: {sales_count}, Purchase records: {purchase_count}")

except Exception as e:
    print(f"❌ Error during renumbering: {e}")
    db.rollback()
    import traceback
    traceback.print_exc()
finally:
    db.close()
