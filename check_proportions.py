import os
import sys
sys.path.append('.')
from main import SessionLocal, Sale

# Check proportion and unit_price data
db = SessionLocal()
try:
    sales = db.query(Sale).order_by(Sale.id).all()
    print('🔍 Checking proportion and unit_price data:')
    for sale in sales:
        proportion = sale.proportion if sale.proportion else 'NULL'
        unit_price = f'{sale.unit_price:.2f}' if sale.unit_price else 'NULL'
        product_name = sale.product.name if sale.product else "Unknown"
        print(f'  Sale {sale.id}: bill_id={sale.bill_id}, product={product_name}, proportion={proportion}, unit_price={unit_price}')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()
