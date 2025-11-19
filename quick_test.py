#!/usr/bin/env python3

import sys
sys.path.append('.')
from main import SessionLocal

def test_opening_stock():
    db = SessionLocal()
    try:
        from main import get_opening_stock_register

        # Mock permission check (simple approach)
        from main import check_permission
        original_check = check_permission
        def mock_check(*args, **kwargs):
            pass
        # Temporarily replace
        import main
        main.check_permission = mock_check

        result = get_opening_stock_register(db=db, username='raza123')

        print(f"✅ Opening stock register test successful!")
        print(f"📊 Found {len(result)} products")

        # Show sample results
        non_zero_count = 0
        for item in result[:10]:  # Check first 10
            qty = float(item['quantity'])
            if qty > 0:
                non_zero_count += 1
                print(f"  ✅ {item['name']}: qty={qty}, value=₹{item['stock_value']:.2f}")
            else:
                print(f"  ❌ {item['name']}: qty={qty}")

        if non_zero_count > 0:
            print(f"\n🎉 SUCCESS: {non_zero_count} products now show non-zero quantities!")
        else:
            print("\n❌ Still showing zero quantities for all products")

        # Restore original function
        main.check_permission = original_check

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_opening_stock()
