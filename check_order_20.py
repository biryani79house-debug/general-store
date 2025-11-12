import os
import sys
sys.path.append('.')
from main import SessionLocal, Sale
from sqlalchemy import text

# Check database connection and sales data
db = SessionLocal()
try:
    # Test connection
    db.execute(text('SELECT 1'))
    print('✅ Database connected successfully')

    # Get all sales with bill_id info
    sales = db.query(Sale).order_by(Sale.id).all()
    print(f'📊 Total sales records: {len(sales)}')

    # Look specifically for bill_id 20
    bill_20_sales = [s for s in sales if s.bill_id == 20]
    print(f'\n🔍 Sales with bill_id 20: {len(bill_20_sales)}')

    if bill_20_sales:
        print('📋 Details for bill_id 20:')
        for sale in bill_20_sales:
            product_name = sale.product.name if sale.product else "Unknown"
            print(f'  Sale ID {sale.id}: {product_name} - Quantity: {sale.quantity}, Total: ₹{sale.total_amount}')
    else:
        print('❌ No sales found with bill_id 20')

    # Check if there are any sales with bill_id NULL that might be recent
    null_bill_sales = [s for s in sales if s.bill_id is None]
    print(f'\n⚠️ Sales with NULL bill_id: {len(null_bill_sales)}')

    if null_bill_sales:
        print('📋 Recent NULL bill_id sales:')
        for sale in null_bill_sales[-5:]:  # Last 5
            product_name = sale.product.name if sale.product else "Unknown"
            print(f'  Sale ID {sale.id}: {product_name} - ₹{sale.total_amount} - {sale.sale_date}')

    # Check the most recent sales
    print(f'\n🕒 Most recent 10 sales:')
    recent_sales = sales[-10:] if len(sales) >= 10 else sales
    for sale in recent_sales:
        bill_id = sale.bill_id if sale.bill_id else 'NULL'
        product_name = sale.product.name if sale.product else "Unknown"
        print(f'  Sale {sale.id}: Bill {bill_id}, {product_name}, Qty: {sale.quantity}, ₹{sale.total_amount}')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()
