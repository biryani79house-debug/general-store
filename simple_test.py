#!/usr/bin/env python3

import sys
sys.path.append('.')
from main import SessionLocal, get_opening_stock_register
import main

# Temporarily disable permission check
original_check = main.check_permission
def mock_check(*args, **kwargs):
    pass
main.check_permission = mock_check

db = SessionLocal()
try:
    result = get_opening_stock_register(db=db, username='raza123')
    print("✅ Opening stock register test successful!")
    print(f"📊 Found {len(result)} products")

    # Count products with non-zero quantities
    non_zero_count = 0
    for item in result:
        qty = float(item['quantity'])
        if qty > 0:
            non_zero_count += 1
            if non_zero_count <= 5:  # Show first 5
                print(f"  ✅ {item['name']}: {qty} units, value ₹{item['stock_value']:.2f}")

    print(f"\n📈 TOTAL: {non_zero_count}/{len(result)} products have stock > 0")

    if non_zero_count > 0:
        print("🎉 SUCCESS: Opening stock register is now showing actual stock levels!")
    else:
        print("❌ FAILED: Still showing zero quantities")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
    main.check_permission = original_check
