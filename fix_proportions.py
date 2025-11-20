import json
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

def fix_product_proportions():
    """Fix malformed proportions and proportion_prices in database"""
    try:
        # Get all products
        products = db.execute(text("SELECT id, name, proportions, proportion_prices FROM products")).fetchall()

        fixed_count = 0
        for product in products:
            product_id = product[0]
            name = product[1]
            proportions_str = product[2]
            prices_str = product[3]

            new_proportions = None
            new_prices = None

            # Fix proportions
            if proportions_str and proportions_str.startswith('[') and proportions_str.endswith(']'):
                # Convert '[1kg,750gm,500gm,250gm]' to '["1kg","750gm","500gm","250gm"]'
                try:
                    # Extract items between brackets
                    content = proportions_str[1:-1]  # Remove [ and ]
                    items = [item.strip() for item in content.split(',')]
                    new_proportions = json.dumps(items)
                except:
                    print(f"Failed to fix proportions for {name}: {proportions_str}")

            # Fix proportion prices
            if prices_str and prices_str.startswith('{') and prices_str.endswith('}'):
                # Convert '{1kg: 25.0, 750gm: 18.75}' to '{"1kg": 25.0, "750gm": 18.75}'
                try:
                    content = prices_str[1:-1]  # Remove { and }
                    pairs = [pair.strip() for pair in content.split(',')]
                    price_dict = {}
                    for pair in pairs:
                        if ':' in pair:
                            key, value = pair.split(':', 1)
                            key = key.strip()
                            # Add quotes around key if not present
                            if not key.startswith('"'):
                                key = f'"{key}"'
                            price_dict[key.strip('"')] = float(value.strip())
                    new_prices = json.dumps(price_dict)
                except Exception as e:
                    print(f"Failed to fix prices for {name}: {prices_str} - Error: {e}")

            # Update the product if changes are needed
            if new_proportions != proportions_str or new_prices != prices_str:
                update_fields = []
                params = {"product_id": product_id}

                if new_proportions is not None:
                    update_fields.append("proportions = :proportions")
                    params["proportions"] = new_proportions

                if new_prices is not None:
                    update_fields.append("proportion_prices = :proportion_prices")
                    params["proportion_prices"] = new_prices

                if update_fields:
                    query = f"UPDATE products SET {', '.join(update_fields)} WHERE id = :product_id"
                    db.execute(text(query), params)
                    db.commit()
                    fixed_count += 1
                    print(f"✅ Fixed product: {name} (ID: {product_id})")

        print(f"\n📊 Fixed {fixed_count} products")
        return fixed_count

    except Exception as e:
        db.rollback()
        print(f"❌ Error fixing proportions: {e}")
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Fixing malformed proportions and proportion_prices in database...")
    fix_product_proportions()
