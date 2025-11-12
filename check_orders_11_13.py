import os
import sys
sys.path.append('.')
from main import SessionLocal, Sale, Product

# Check what's in the database for orders 11, 12, and 13
db = SessionLocal()
try:
    # Get sales for orders 11, 12, and 13
    sales = db.query(Sale).filter(Sale.id.in_([11, 12, 13])).all()

    print('=== SALES RECORDS FOR ORDERS 11-13 ===')
    for sale in sales:
        product = db.query(Product).filter(Product.id == sale.product_id).first()
        print(f'Sale ID: {sale.id}')
        print(f'Product: {product.name if product else "Unknown"}')
        print(f'Quantity: {sale.quantity}')
        print(f'Total Amount: ₹{sale.total_amount:.2f}')
        print(f'Customer: {sale.customer_name} - {sale.customer_phone}')
        print(f'Created By: {sale.created_by}')
        print(f'Date: {sale.sale_date}')

        # Check proportion prices
        if product and product.proportion_prices:
            print(f'Proportion Prices: {product.proportion_prices}')
        print('---')

finally:
    db.close()
