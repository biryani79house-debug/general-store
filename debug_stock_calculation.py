from dotenv import load_dotenv
load_dotenv()
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL, connect_args={"options": "-c timezone=Asia/Kolkata"})

db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()

def debug_stock_calculation():
    """Debug the stock calculation for almonds proportion sales"""
    try:
        # Get almonds product
        product = db.execute(text("""
            SELECT id, name, selling_price, proportion_prices, stock
            FROM products WHERE name LIKE '%almonds%' LIMIT 1
        """)).fetchone()

        if not product:
            print("❌ Almonds product not found!")
            return

        product_id, name, selling_price, proportion_prices_str, stock = product
        print(f"📦 Product: {name} (ID: {product_id})")
        print(f"   Base Price: ₹{selling_price}/kg")
        print(f"   Current Stock: {stock} kg")
        print(f"   Proportion Prices: {proportion_prices_str}")

        # Parse proportion prices
        if proportion_prices_str:
            proportion_prices = json.loads(proportion_prices_str)
            print(f"   Parsed Prices: {proportion_prices}")

            # Calculate what 750gm should cost and convert to kg equivalent
            if '750gm' in proportion_prices:
                proportion_price_750g = proportion_prices['750gm']
                kg_equivalent = proportion_price_750g / selling_price  # 336 / 448 = 0.75

                print(f"   750gm price: ₹{proportion_price_750g}")
                print(f"   750gm kg equivalent: {kg_equivalent} kg")
                print(f"   Available stock for 750gm: {stock // kg_equivalent:.1f} units")
                print(f"   Stock status: {'✅ Available' if stock >= kg_equivalent else '❌ Out of stock'}")

        # Test the actual sale logic
        test_quantity = "750gm"
        print(f"\n🔧 Testing sale calculation for quantity: '{test_quantity}'")

        # Simulate the API logic
        numeric_quantity = 0.0

        try:
            proportion_prices = json.loads(proportion_prices_str)
            if test_quantity in proportion_prices:
                proportion_price = float(proportion_prices[test_quantity])
                base_price = selling_price
                if base_price > 0:
                    numeric_quantity = proportion_price / base_price
        except Exception as e:
            print(f"   ⚠️ Error in calculation: {e}")

        print(f"   Calculated numeric quantity: {numeric_quantity} kg")
        print(f"   Stock check result: {'✅ Enough stock' if stock >= numeric_quantity else '❌ Insufficient stock'}")
        print(f"   Remaining stock after sale: {stock - numeric_quantity} kg")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
