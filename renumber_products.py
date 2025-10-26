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

    # Now renumber - Make all product IDs consecutive starting from 1
    print("\n⚡ Starting consecutive renumbering...")

    # Get all current products ordered by ID
    all_products = db.execute(text("SELECT id, name, stock FROM products ORDER BY id")).fetchall()
    old_ids = [product[0] for product in all_products]

    # Create mapping from old ID to new consecutive ID
    old_to_new = {}
    for new_id, old_id in enumerate(old_ids, start=1):
        old_to_new[old_id] = new_id

    print(f"📋 Renumbering mapping: {old_to_new}")

    if len(old_to_new) == 0:
        print("❌ No products found to renumber!")
        sys.exit(1)

    # Get data for all current products
    product_data = {}
    for old_id in old_ids:
        product = db.execute(text("SELECT name, purchase_price, selling_price, unit_type, stock, initial_stock, created_at, category FROM products WHERE id = :id"), {"id": old_id}).first()
        if product:
            product_data[old_id] = product

    print(f"Found product data for {len(product_data)} products")

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

    # Reset sequence to start from max_id + 1
    max_id = max(old_to_new.values())
    next_id = max_id + 1
    db.execute(text("ALTER SEQUENCE products_id_seq RESTART WITH :next_id"), {"next_id": next_id})
    print(f"✅ PostgreSQL sequence reset to {next_id}")

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
