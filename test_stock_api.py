#!/usr/bin/env python3
"""
Test stock calculation and API endpoints
"""

import sys
sys.path.append('.')
from main import SessionLocal, calculate_current_stock, get_products

def test_stock_logic():
    """Test the stock calculation logic"""
    db = SessionLocal()
    try:
        from main import Product, Purchase, Sale

        # Get all products
        all_products = db.query(Product).all()
        print(f'🔍 Checking calculated stock for all {len(all_products)} products...')

        # Check which products have calculated stock > 0
        products_with_calculated_stock = []
        for product in all_products:
            calculated = calculate_current_stock(product.id, db)
            if calculated > 0:
                purchases = db.query(Purchase).filter(Purchase.product_id == product.id).count()
                sales = db.query(Sale).filter(Sale.product_id == product.id).count()
                products_with_calculated_stock.append({
                    'id': product.id,
                    'name': product.name,
                    'stored_stock': product.stock,
                    'calculated_stock': calculated,
                    'purchases': purchases,
                    'sales': sales
                })

        print(f'📦 Products with calculated stock > 0: {len(products_with_calculated_stock)}')
        for p in products_with_calculated_stock:
            print(f'  ID {p["id"]}: {p["name"]} - Stored: {p["stored_stock"]}, Calculated: {p["calculated_stock"]}, Purchases: {p["purchases"]}, Sales: {p["sales"]}')

        # Test the /products endpoint directly
        print('\n🌐 Testing /products endpoint response...')
        response_data = get_products(db=db)

        print(f'📊 /products endpoint returns {len(response_data)} products')
        stocked_count = sum(1 for p in response_data if p.get('stock', 0) > 0)
        print(f'📦 Products with stock > 0 in API response: {stocked_count}')

        if stocked_count > 0:
            print('  📋 Sample stocked products from API:')
            count = 0
            for p in response_data:
                if p.get('stock', 0) > 0 and count < 5:
                    print(f'    ✅ {p["name"]}: stock = {p["stock"]}')
                    count += 1

        # Summary
        stored_stock_count = sum(1 for p in all_products if p.stock > 0)
        calculated_stock_count = len(products_with_calculated_stock)

        print(f'\n📈 Summary:')
        print(f'   - Products with stored stock > 0: {stored_stock_count}')
        print(f'   - Products with calculated stock > 0: {calculated_stock_count}')
        print(f'   - Products returned by API with stock > 0: {stocked_count}')

        # Test the opening stock register endpoint
        print('\n🔍 Testing /opening-stock-register endpoint...')
        opening_stock_data = test_opening_stock_register(db)

        print(f'📊 /opening-stock-register returns {len(opening_stock_data)} products with stock levels:')
        for item in opening_stock_data[:5]:  # Show first 5
            print(f'    ✅ {item["name"]}: quantity = {item["quantity"]}, stock_value = ₹{item["stock_value"]:.2f}')

        db.close()

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

def test_opening_stock_register(db):
    """Test the opening stock register endpoint by importing the function"""
    from main import get_opening_stock_register

    # Mock the permission check
    original_check_permission = None
    try:
        from main import check_permission
        original_check_permission = check_permission
        def mock_check_permission(*args, **kwargs):
            pass  # Do nothing
    except ImportError:
        pass

    # Test the endpoint directly
    try:
        result = get_opening_stock_register(db=db, username="raza123")
        return result
    except Exception as e:
        print(f"❌ Error testing opening stock register: {e}")
        return []

if __name__ == "__main__":
