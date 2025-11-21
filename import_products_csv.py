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
    DATABASE_URL = os.getenv("DATABASE_URL")
    from sqlalchemy import create_engine
    # For PostgreSQL, set timezone to IST (Asia/Kolkata) to match stored timestamps
    engine = create_engine(DATABASE_URL, connect_args={"options": "-c timezone=Asia/Kolkata"})

from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

# Import the models
IST = timezone(timedelta(hours=5, minutes=30))

class Product:
    """Same as main.py"""
    __tablename__ = "products"

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if 'created_at' not in kwargs:
            self.created_at = datetime.now(IST)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def create_category_if_not_exists(category_name):
    """Create category if it doesn't exist"""
    if category_name:
        # Check if exists
        result = db.execute(text("SELECT id FROM categories WHERE name = :name"), {"name": category_name}).fetchone()
        if not result:
            # Insert new category
            db.execute(text("INSERT INTO categories (name, created_at) VALUES (:name, CURRENT_TIMESTAMP)"), {"name": category_name})
            db.commit()
            print(f"✅ Created category: {category_name}")

def import_csv_to_db(csv_path):
    products_imported = 0
    duplicates_skipped = 0

    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # Skip header if any

            for row in reader:
                if len(row) < 11:  # Ensure we have all required columns
                    print(f"⚠️ Skipping invalid row: {row}")
                    continue

                try:
                    product_id = int(row[0])
                    name = row[1].strip()
                    purchase_price = float(row[2])
                    selling_price = float(row[3])
                    unit_type = row[4].strip()
                    proportions = row[5] if row[5] else None
                    proportion_prices = row[6] if row[6] else None
                    category = row[7].strip() if row[7] else None
                    stock = float(row[8]) if row[8] else 0.0
                    initial_stock = float(row[9]) if len(row) > 9 and row[9] else stock
                    created_at = row[10] if len(row) > 10 and row[10] else None

                    # Create category if needed
                    create_category_if_not_exists(category)

                    # Check if product with this ID already exists
                    existing = db.execute(text("SELECT id FROM products WHERE id = :id"), {"id": product_id}).fetchone()
                    if existing:
                        print(f"⚠️ Product with ID {product_id} already exists, skipping: {name}")
                        duplicates_skipped += 1
                        continue

                    # Build INSERT query
                    if created_at:
                        # Parse the datetime string
                        try:
                            parsed_datetime = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            # Create the product with initial_stock set to 0 since we'll create a purchase record
                            db.execute(text("""
                                INSERT INTO products
                                (id, name, purchase_price, selling_price, unit_type, proportions, proportion_prices, category, stock, initial_stock, created_at)
                                VALUES
                                (:id, :name, :purchase_price, :selling_price, :unit_type, :proportions, :proportion_prices, :category, :stock, 0, :created_at)
                            """), {
                                "id": product_id,
                                "name": name,
                                "purchase_price": purchase_price,
                                "selling_price": selling_price,
                                "unit_type": unit_type,
                                "proportions": proportions,
                                "proportion_prices": proportion_prices,
                                "category": category,
                                "stock": stock,
                                "created_at": parsed_datetime
                            })

                            # Create a purchase record for the initial stock to show it as purchases
                            if stock > 0:
                                total_cost = stock * purchase_price
                                # Get the next purchase ID
                                max_purchase_id = db.execute(text("SELECT MAX(id) FROM purchases")).scalar()
                                next_purchase_id = (max_purchase_id or 0) + 1
                                # Get a user ID (prefer admin user)
                                admin_user = db.execute(text("SELECT id FROM users WHERE username = 'raza123'")).fetchone()
                                user_id = admin_user[0] if admin_user else 1

                                db.execute(text("""
                                    INSERT INTO purchases (id, product_id, quantity, total_cost, purchase_date, created_by)
                                    VALUES (:id, :product_id, :quantity, :total_cost, :purchase_date, :created_by)
                                """), {
                                    "id": next_purchase_id,
                                    "product_id": product_id,
                                    "quantity": stock,
                                    "total_cost": total_cost,
                                    "purchase_date": parsed_datetime,
                                    "created_by": user_id
                                })
                                print(f"✅ Created purchase record for {stock} units @ ₹{purchase_price:.2f} = ₹{total_cost:.2f}")
                        except Exception as parse_error:
                            print(f"⚠️ Error parsing created_at '{created_at}', using CURRENT_TIMESTAMP")
                            # Create the product with initial_stock set to 0 since we'll create a purchase record
                            db.execute(text("""
                                INSERT INTO products
                                (id, name, purchase_price, selling_price, unit_type, proportions, proportion_prices, category, stock, initial_stock)
                                VALUES
                                (:id, :name, :purchase_price, :selling_price, :unit_type, :proportions, :proportion_prices, :category, :stock, 0)
                            """), {
                                "id": product_id,
                                "name": name,
                                "purchase_price": purchase_price,
                                "selling_price": selling_price,
                                "unit_type": unit_type,
                                "proportions": proportions,
                                "proportion_prices": proportion_prices,
                                "category": category,
                                "stock": stock
                            })

                            # Create a purchase record for the initial stock to show it as purchases
                            if stock > 0:
                                total_cost = stock * purchase_price
                                # Get the next purchase ID
                                max_purchase_id = db.execute(text("SELECT MAX(id) FROM purchases")).scalar()
                                next_purchase_id = (max_purchase_id or 0) + 1
                                # Get a user ID (prefer admin user)
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
                                print(f"✅ Created purchase record for {stock} units @ ₹{purchase_price:.2f} = ₹{total_cost:.2f}")
                    else:
                        # No created_at, let database use default
                        # Create the product with initial_stock set to 0 since we'll create a purchase record
                        db.execute(text("""
                            INSERT INTO products
                            (id, name, purchase_price, selling_price, unit_type, proportions, proportion_prices, category, stock, initial_stock)
                            VALUES
                            (:id, :name, :purchase_price, :selling_price, :unit_type, :proportions, :proportion_prices, :category, :stock, 0)
                        """), {
                            "id": product_id,
                            "name": name,
                            "purchase_price": purchase_price,
                            "selling_price": selling_price,
                            "unit_type": unit_type,
                            "proportions": proportions,
                            "proportion_prices": proportion_prices,
                            "category": category,
                            "stock": stock
                        })

                        # Create a purchase record for the initial stock to show it as purchases
                        if stock > 0:
                            total_cost = stock * purchase_price
                            # Get the next purchase ID
                            max_purchase_id = db.execute(text("SELECT MAX(id) FROM purchases")).scalar()
                            next_purchase_id = (max_purchase_id or 0) + 1
                            # Get a user ID (prefer admin user)
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
                            print(f"✅ Created purchase record for {stock} units @ ₹{purchase_price:.2f} = ₹{total_cost:.2f}")

                    products_imported += 1
                    print(f"✅ Imported product: {name} (ID: {product_id})")

                except Exception as e:
                    print(f"❌ Error importing product from row: {row}")
                    print(f"   Error: {e}")
                    db.rollback()
                    continue

        print(f"\n📊 Import Summary:")
        print(f"   ✅ Products imported: {products_imported}")
        print(f"   ⚠️  Duplicates skipped: {duplicates_skipped}")
        print(f"   🎯 Total processed: {products_imported + duplicates_skipped}")

    except Exception as e:
        print(f"❌ Fatal error during import: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    csv_file = "new products.csv"

    if not os.path.exists(csv_file):
        print(f"❌ CSV file '{csv_file}' not found!")
        exit(1)

    print(f"🚀 Starting import of products from '{csv_file}'...")
    print(f"📊 Using database: {'SQLite (dev)' if USE_SQLITE else 'PostgreSQL (prod)'}")

    import_csv_to_db(csv_file)

    print("✅ Import completed!")
