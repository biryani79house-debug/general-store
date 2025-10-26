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
    # Step 1: Check current product categories
    print("\n🔍 Checking current product categories...")
    products = db.execute(text("SELECT id, name, category FROM products")).fetchall()
    print("Current products:")
    for product in products:
        category = product[2] if product[2] else "None"
        print(f"  - {product[1]} (ID: {product[0]}): category=\"{category}\"")

    # Step 2: Assign products to appropriate categories
    print("\n🏷️ Assigning products to correct categories...")

    # Define category assignments
    category_assignments = [
        ("gold drop oil", "Groceries"),
        ("parle g", "Groceries"),
        ("milk", "Dairy"),
        ("masoor dal", "Groceries")  # Already assigned, but ensure it stays
    ]

    for product_name, new_category in category_assignments:
        # Check if product exists
        product_result = db.execute(text("SELECT id, category FROM products WHERE name = :name"),
                                  {"name": product_name}).fetchone()

        if product_result:
            current_category = product_result[1]
            print(f"Updating {product_name}: '{current_category}' → '{new_category}'")

            db.execute(text("UPDATE products SET category = :category WHERE name = :name"),
                      {"category": new_category, "name": product_name})

        else:
            print(f"⚠️  Product '{product_name}' not found in database")

    # Commit changes
    db.commit()
    print("✅ Category assignments completed")

    # Step 3: Verify changes
    print("\n🔍 Verifying category assignments...")
    updated_products = db.execute(text("SELECT id, name, category FROM products")).fetchall()
    print("Updated products:")
    for product in updated_products:
        category = product[2] if product[2] else "None"
        print(f"  - {product[1]} (ID: {product[0]}): category=\"{category}\"")

    # Step 4: Test the stock API filtering
    print("\n🧪 Testing category filtering...")

    # Test Groceries category
    groceries_result = db.execute(text("SELECT COUNT(*) FROM products WHERE category ILIKE 'groceries'")).fetchone()
    print(f"Products in 'Groceries' category: {groceries_result[0]}")

    # List products in Groceries
    groceries_products = db.execute(text("SELECT name FROM products WHERE category ILIKE 'groceries'")).fetchall()
    for product in groceries_products:
        print(f"  - {product[0]}")

    print("\n✅ Category update script completed successfully!")

except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
    import traceback
    traceback.print_exc()
finally:
    db.close()
