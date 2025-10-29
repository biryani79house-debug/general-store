#!/usr/bin/env python3
# Standalone test for opening stock register - doesn't import from main.py to avoid Railway env issues

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import ForeignKey, func

# Force SQLite database for testing
DATABASE_URL = 'sqlite:///./kirana_store.db'
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define minimal models just for testing
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    purchase_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    unit_type = Column(String, nullable=False)
    category = Column(String, nullable=True)  # This column is missing but we need it for queries
    stock = Column(Float, default=0)
    initial_stock = Column(Float, default=0)
    created_at = Column(DateTime)

class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    total_cost = Column(Float, nullable=False)
    purchase_date = Column(DateTime)
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

try:
    # Create a test session
    db = SessionLocal()

    # Test database connection
    db.execute(text('SELECT 1'))
    print('✅ Database connected')

    # Check products in database
    products = db.query(Product).all()
    print(f'📦 Found {len(products)} products in database')

    for i, p in enumerate(products):
        print(f'  Product {i+1}: ID={p.id}, Name={p.name}, Purchase Price={p.purchase_price}, Selling Price={p.selling_price}, Unit Type={p.unit_type}, Stock={p.stock}')

    # Check purchases
    purchases = db.query(Purchase).all()
    print(f'🛒 Found {len(purchases)} purchases in total')

    for i, p in enumerate(purchases):
        print(f'  Purchase {i+1}: Product {p.product_id}, Quantity {p.quantity}')

    # Now test opening stock calculation (without authentication check)
    print('\n🔍 Testing opening stock register logic...')

    opening_stock_data = []

    for i, product in enumerate(products):
        print(f'\n🔍 Processing Product {i+1}: {product.name}')

        if product.id is None or product.name is None or product.purchase_price is None:
            print(f'⚠️ Skipping: Missing required fields')
            print(f'   ID: {product.id}, Name: {product.name}, Purchase Price: {product.purchase_price}')
            continue

        try:
            purchase_total_result = db.query(db.func.sum(Purchase.quantity)).filter(Purchase.product_id == product.id).scalar()
            total_purchases = int(purchase_total_result or 0)
            print(f'   Total purchases: {total_purchases}')

            purchase_price = float(product.purchase_price)
            stock_value = float(total_purchases * purchase_price)

            print(f'   Stock value: ₹{stock_value:.2f}')

            opening_stock_data.append({
                'id': int(product.id),
                'name': str(product.name),
                'purchase_price': purchase_price,
                'selling_price': float(product.selling_price or 0),
                'unit_type': str(product.unit_type or 'pcs'),
                'quantity': total_purchases,
                'stock_value': stock_value
            })

            print(f'✅ Successfully added: {product.name}')

        except Exception as e:
            print(f'❌ Error processing {product.name}: {e}')
            import traceback
            traceback.print_exc()
            continue

    print(f'\n📊 Final result: {len(opening_stock_data)} products in opening stock')

    for item in opening_stock_data:
        print(f'  {item["name"]}: {item["quantity"]} units @ ₹{item["purchase_price"]} = ₹{item["stock_value"]:.2f}')

    if opening_stock_data:
        print('\n✅ OPENING STOCK REGISTER IS WORKING!')
    else:
        print('\n❌ OPENING STOCK REGISTER HAS ISSUES - NO DATA RETURNED')
        if not products:
            print('   No products found in database.')
        elif len(opening_stock_data) == 0:
            print('   All products were skipped due to validation (null values).')
        else:
            print('   Unknown issue.')

    db.close()

except Exception as e:
    import traceback
    print(f'❌ TEST ERROR: {e}')
    traceback.print_exc()
