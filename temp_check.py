from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv('DATABASE_URL', 'sqlite:///./kirana_store.db')

if 'postgresql' in database_url:
    engine = create_engine(database_url, connect_args={"options": "-c timezone=Asia/Kolkata"})
else:
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

with engine.connect() as conn:
    # Get product details
    result = conn.execute(text('SELECT id, name, selling_price, proportions, proportion_prices FROM products WHERE id = 2'))
    product = result.fetchone()

    print(f'Product: {product[1]}')
    print(f'Selling price: {product[2]}')
    print(f'Proportions: {product[3]}')
    print(f'Proportion prices: {product[4]}')

    if product[4]:
        import json
        proportion_prices = json.loads(product[4])
        print('Parsed proportion prices:', proportion_prices)
        if '500ml' in proportion_prices:
            print(f'500ml price: {proportion_prices["500ml"]}')
            calc_quantity = proportion_prices['500ml'] / product[2] if product[2] > 0 else 1
            print(f'Calculated quantity for 500ml: {calc_quantity}')

conn.close()
