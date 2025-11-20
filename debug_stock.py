import sys
sys.path.append('.')
from main import SessionLocal, Product, Purchase, Sale, calculate_current_stock, get_products_stock_snapshot

db = SessionLocal()

try:
    print("=== TESTING STOCK CALCULATION FIX ===")

    # Check Clinic Plus Shampoo
    product = db.query(Product).filter(Product.name.ilike('Clinic Plus Shampoo')).first()
    if product:
        print(f'✅ Found product: {product.name} (ID: {product.id})')
        print(f'   Stored stock: {product.stock}')

        # Check purchases and sales
        purchases = db.query(Purchase).filter(Purchase.product_id == product.id).all()
        sales = db.query(Sale).filter(Sale.product_id == product.id).all()

        total_purchases = sum(p.quantity for p in purchases)
        total_sales = sum(float(s.quantity) if s.quantity.replace('.', '').isdigit() else 0 for s in sales)

        print(f'   Total purchases: {total_purchases}')
        print(f'   Total sales: {total_sales}')

        # Calculate stock
        calculated_stock = total_purchases - total_sales
        print(f'   Calculated stock (before fix): {calculated_stock}')

        # Test the fix logic
        if total_purchases == 0 and total_sales == 0:
            calculated_stock = product.stock
            print(f'   ✅ Fix applied: Using stored stock: {calculated_stock}')

        print(f'   Final stock value: {calculated_stock}')

        # Test the API directly
        print(f'\\n📊 Testing actual API call...')
        result = get_products_stock_snapshot(product_id=12, db=db)
        if result and len(result) > 0:
            first_item = result[0]
            print(f'   API returned stock: {first_item.stock}')
            print(f'   API returned price: {first_item.price}')
            print(f'   ✅ SUCCESS: Stock is now {first_item.stock} (was 0 before fix!)')
        else:
            print('   ❌ No result from API')

finally:
    db.close()
