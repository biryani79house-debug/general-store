from dotenv import load_dotenv
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Base, User, Product, Category
from sqlalchemy import text
import bcrypt

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
USE_SQLITE = False  # Force PostgreSQL since we only use PostgreSQL

print(f"USE_SQLITE: {USE_SQLITE}")
print(f"DATABASE_URL: {DATABASE_URL}")

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./kirana_store.db" if USE_SQLITE else None
    if not DATABASE_URL:
        print("No DATABASE_URL")
        exit()

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if USE_SQLITE else {})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

try:
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Tables created")

    # Check if users exist
    user_count = db.query(User).count()
    print(f"Users in database: {user_count}")

    if user_count == 0:
        # Create admin user
        default_password = "123456"
        hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())

        admin = User(
            username="raza123",
            email="admin@kirana.store",
            password_hash=hashed_password.decode('utf-8'),
            sales=True,
            purchase=True,
            create_product=True,
            delete_product=True,
            create_category=True,
            delete_category=True,
            sales_ledger=True,
            purchase_ledger=True,
            stock_ledger=True,
            profit_loss=True,
            opening_stock=True,
            user_management=True,
            is_active=True
        )
        db.add(admin)
        print("Admin user created")

        # Create sample categories
        sample_categories = [
            Category(name="Fruits"),
            Category(name="Vegetables"),
            Category(name="Dairy"),
            Category(name="Bakery"),
            Category(name="Groceries"),
            Category(name="Beverages"),
            Category(name="Snacks"),
            Category(name="Meat & Fish"),
        ]
        db.add_all(sample_categories)
        print("Sample categories added")

        # Create sample products
        sample_products = [
            Product(name="Apple", purchase_price=80.00, selling_price=100.00, unit_type="kgs", category="Fruits", stock=50),
            Product(name="Banana", purchase_price=40.00, selling_price=50.00, unit_type="kgs", category="Fruits", stock=30),
            Product(name="Milk", purchase_price=50.00, selling_price=65.00, unit_type="ltr", category="Dairy", stock=20),
        ]
        db.add_all(sample_products)
        print("Sample products added")

        db.commit()
        print("Seeding completed")
    else:
        print("Users already exist, skipping seed")

except Exception as e:
    print(f"Error: {e}")
    db.rollback()

finally:
    db.close()
    print("Database seeding script finished")
