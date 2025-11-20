from dotenv import load_dotenv
load_dotenv()
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL, connect_args={"options": "-c timezone=Asia/Kolkata"})

db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()

def fix_initial_stock():
    """Set initial_stock equal to stock for imported products that have initial_stock = 0"""
    try:
        # Update products where initial_stock = 0 and stock > 0
        result = db.execute(text("""
            UPDATE products
            SET initial_stock = stock
            WHERE initial_stock = 0 AND stock > 0
        """))

        updated_count = result.rowcount
        db.commit()

        print(f"✅ Fixed {updated_count} products - set initial_stock = stock")

        # Verify the fix
        sample_products = db.execute(text("""
            SELECT id, name, stock, initial_stock
            FROM products
            WHERE id IN (5, 6, 7, 8)
        """)).fetchall()

        print("\n📊 Sample products after fix:")
        for p in sample_products:
            print(f"ID {p[0]}: {p[1]} - Stock: {p[2]}, Initial: {p[3]}")

        return updated_count

    except Exception as e:
        db.rollback()
        print(f"❌ Error fixing initial stock: {e}")
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Fixing initial_stock values to match stock for imported products...")
    fix_initial_stock()
