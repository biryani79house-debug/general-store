import os
import sys
sys.path.append('.')
from main import SessionLocal, Sale, Product
import json

# Test the order reconstruction logic for ORDER_9
db = SessionLocal()
try:
    # Get the base sale (ID 9)
    base_sale_id = 9
    base_sale = db.query(Sale).filter(Sale.id == base_sale_id).first()

    if not base_sale:
        print(f"Order {base_sale_id} not found")
        sys.exit(1)

    print(f"=== RECONSTRUCTING ORDER {base_sale_id} ===")
    print(f"Base sale: {base_sale.customer_name} - {base_sale.customer_phone}")

    # Find all sales that belong to the same order
    order_sales = db.query(Sale).filter(
        Sale.customer_name == base_sale.customer_name,
        Sale.customer_phone == base_sale.customer_phone,
        Sale.sale_date >= base_sale.sale_date.replace(second=0, microsecond=0),
        Sale.sale_date <= base_sale.sale_date.replace(second=59, microsecond=999999)
    ).all()

    print(f"Found {len(order_sales)} sales in this order")

    # Reconstruct items array
    items = []
    total_amount = 0

    for sale in order_sales:
        product = db.query(Product).filter(Product.id == sale.product_id).first()
        if product:
            # Calculate the unit price from the sale total
            quantity = sale.quantity
            item_total = sale.total_amount
            unit_price = item_total / quantity if quantity > 0 else 0

            print(f"\nProcessing sale {sale.id}:")
            print(f"  Product: {product.name}")
            print(f"  Quantity: {quantity}")
            print(f"  Total: ₹{item_total:.2f}")
            print(f"  Calculated unit price: ₹{unit_price:.2f}")

            # Try to reconstruct the original item name and proportion
            item_name = product.name
            item_price = unit_price  # Default to the actual sale price

            # Check if this sale was for a proportion by comparing unit prices with proportion prices
            if product.proportion_prices:
                try:
                    proportion_prices = json.loads(product.proportion_prices)
                    print(f"  Available proportions: {proportion_prices}")

                    # Check each proportion to see if the unit price matches
                    for prop_name, prop_price in proportion_prices.items():
                        print(f"    Checking {prop_name}: ₹{float(prop_price):.2f} vs ₹{unit_price:.2f}")
                        if abs(float(prop_price) - unit_price) < 0.01:  # Allow for small rounding differences
                            # Found matching proportion
                            item_name = f"{product.name} ({prop_name})"
                            item_price = float(prop_price)
                            print(f"    ✓ Matched proportion: {prop_name}")
                            break
                    else:
                        print("    ✗ No proportion matched")
                except Exception as e:
                    print(f"  Error parsing proportion prices: {e}")
                    # Fall back to base price if proportion parsing fails
                    pass

            # If no proportion matched, check if it matches the base selling price
            if abs(product.selling_price - unit_price) < 0.01:
                # It's the base price, no proportion needed
                item_name = product.name
                item_price = product.selling_price
                print(f"  ✓ Using base price: ₹{product.selling_price:.2f}")
            else:
                print(f"  ⚠ Using calculated price: ₹{unit_price:.2f}")

            items.append({
                "name": item_name,
                "quantity": quantity,
                "price": item_price
            })
            total_amount += item_total

    print("\n=== FINAL ORDER DATA ===")
    print(f"Customer: {base_sale.customer_name}")
    print(f"Phone: {base_sale.customer_phone}")
    print("Items:")
    for item in items:
        print(f"  - {item['name']}: {item['quantity']} × ₹{item['price']:.2f} = ₹{item['quantity'] * item['price']:.2f}")
    print(f"Total: ₹{total_amount:.2f}")

finally:
    db.close()
