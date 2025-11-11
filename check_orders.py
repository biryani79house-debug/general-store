import os
import sys
sys.path.append('.')
from main import SessionLocal, Sale, Product

# Check what's in the database for orders 9 and 10
db = SessionLocal()
try:
    # Get sales for orders 9 and 10
    sales_9 = db.query(Sale).filter(Sale.id >= 9, Sale.id <= 10).all()

    print('=== SALES RECORDS FOR ORDERS 9-10 ===')
    for sale in sales_9:
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

    # Check if there are more sales for these orders
    print('\n=== CHECKING FOR GROUPED SALES ===')
    # Find all sales that might belong to the same order (same customer, similar time)
    if sales_9:
        base_sale = sales_9[0]
        related_sales = db.query(Sale).filter(
            Sale.customer_name == base_sale.customer_name,
            Sale.customer_phone == base_sale.customer_phone,
            Sale.sale_date >= base_sale.sale_date.replace(second=0, microsecond=0),
            Sale.sale_date <= base_sale.sale_date.replace(second=59, microsecond=999999)
        ).all()

        print(f'Found {len(related_sales)} related sales for order around {base_sale.sale_date}')
        for sale in related_sales:
            product = db.query(Product).filter(Product.id == sale.product_id).first()
            unit_price = sale.total_amount / sale.quantity if sale.quantity > 0 else 0
            print(f'  Sale {sale.id}: {product.name if product else "Unknown"} - {sale.quantity} × ₹{unit_price:.2f} = ₹{sale.total_amount:.2f}')

finally:
    db.close()
