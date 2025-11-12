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

    # Group by bill_id to see how many bills we have
    bill_groups = {}
    for sale in sales:
        bill_id = sale.bill_id if sale.bill_id else 'NULL'
        if bill_id not in bill_groups:
            bill_groups[bill_id] = []
        bill_groups[bill_id].append(sale.id)

    print(f'📋 Total unique bill_ids: {len(bill_groups)}')

    # Show bill_id distribution
    print('\n📋 Bill ID Distribution:')
    for bill_id, sale_ids in sorted(bill_groups.items()):
        ids_str = str(sale_ids[:5])
        if len(sale_ids) > 5:
            ids_str += '...'
        print(f'  Bill {bill_id}: {len(sale_ids)} sales (IDs: {ids_str})')

    # Check specifically for bill_id 1
    bill_1_sales = [s for s in sales if s.bill_id == 1]
    print(f'\n🔍 Sales with bill_id 1: {len(bill_1_sales)}')
    if bill_1_sales:
        print('📋 Details for bill_id 1:')
        for sale in bill_1_sales:
            product_name = sale.product.name if sale.product else "Unknown"
            proportion = f" ({sale.proportion})" if sale.proportion else ""
            unit_price = f" @ ₹{sale.unit_price:.2f}" if sale.unit_price else ""
            print(f'  Sale ID {sale.id}: {product_name}{proportion} - Qty: {sale.quantity}{unit_price}, Total: ₹{sale.total_amount}')

    # Check specifically for bill_id 2 (the one the user mentioned)
    bill_2_sales = [s for s in sales if s.bill_id == 2]
    print(f'\n🔍 Sales with bill_id 2: {len(bill_2_sales)}')
    if bill_2_sales:
        print('📋 Details for bill_id 2:')
        for sale in bill_2_sales:
            product_name = sale.product.name if sale.product else "Unknown"
            proportion = f" ({sale.proportion})" if sale.proportion else ""
            unit_price = f" @ ₹{sale.unit_price:.2f}" if sale.unit_price else ""
            print(f'  Sale ID {sale.id}: {product_name}{proportion} - Qty: {sale.quantity}{unit_price}, Total: ₹{sale.total_amount}')

    # Check specifically for bill_id 20
    bill_20_sales = [s for s in sales if s.bill_id == 20]
    print(f'\n🔍 Sales with bill_id 20: {len(bill_20_sales)}')
    if bill_20_sales:
        print('📋 Details for bill_id 20:')
        for sale in bill_20_sales:
            product_name = sale.product.name if sale.product else "Unknown"
            proportion = f" ({sale.proportion})" if sale.proportion else ""
            unit_price = f" @ ₹{sale.unit_price:.2f}" if sale.unit_price else ""
            print(f'  Sale ID {sale.id}: {product_name}{proportion} - Qty: {sale.quantity}{unit_price}, Total: ₹{sale.total_amount}')

    # Check recent sales (last 10)
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
