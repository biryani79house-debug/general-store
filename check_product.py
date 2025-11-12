import os
import sys
sys.path.append('.')
from main import SessionLocal, Product

# Check if the product exists in the database
db = SessionLocal()
try:
    # Check for exact product name
    product = db.query(Product).filter(Product.name.ilike('masoor dal')).first()
    if product:
        print(f'Product found: {product.name} (ID: {product.id})')
    else:
        print('Product "masoor dal" not found')

    # Check for similar products
    similar_products = db.query(Product).filter(Product.name.ilike('%dal%')).all()
    print(f'Products containing "dal": {len(similar_products)}')
    for p in similar_products[:5]:  # Show first 5
        print(f'  - {p.name} (ID: {p.id})')

except Exception as e:
    print(f'Error: {e}')
finally:
    db.close()
