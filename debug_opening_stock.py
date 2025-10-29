#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from main import Product, Purchase

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"DATABASE_URL found: {DATABASE_URL is not None}")

if DATABASE_URL:
    print(f"Connecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")

    engine = create_engine(DATABASE_URL, echo=True)  # Enable echo to see SQL queries
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()

    try:
        print("\n=== TESTING OPENING STOCK REGISTER ===")

        # Test database connection
        result = db.execute(text("SELECT 1"))  # Simple test
        print("✅ Database connection successful")

        # Get all products
        products = db.query(Product).all()
        print(f"Found {len(products)} products")

        opening_stock_data = []

        for product in products:
            print(f"\nProcessing product: {product.name} (ID: {product.id})")

            # Calculate total purchase quantity
            try:
                from sqlalchemy import func
                total_purchase_quantity = db.query(func.sum(Purchase.quantity)).filter(Purchase.product_id == product.id).scalar()
                print(f"  Total purchase quantity: {total_purchase_quantity}")
            except Exception as calc_error:
                print(f"  ❌ Error calculating purchase quantity: {calc_error}")
                continue

            # Handle None case
            if total_purchase_quantity is None:
                total_purchase_quantity = 0

            opening_stock_quantity = int(total_purchase_quantity)
            stock_value = opening_stock_quantity * product.purchase_price

            print(f"  Opening stock quantity: {opening_stock_quantity}")
            print(f"  Stock value: {stock_value}")

            try:
                opening_stock_data.append({
                    "id": product.id,
                    "name": product.name,
                    "purchase_price": product.purchase_price,
                    "selling_price": product.selling_price,
                    "unit_type": product.unit_type,
                    "quantity": opening_stock_quantity,
                    "stock_value": stock_value,
                    "created_at": product.created_at
                })
                print("  ✅ Product processed successfully")
            except Exception as append_error:
                print(f"  ❌ Error adding product to data: {append_error}")

        print(f"\n🎉 Successfully processed {len(opening_stock_data)} products")

        # Print sample data
        if opening_stock_data:
            print("\nSample output:")
            for item in opening_stock_data[:3]:
                print(f"  {item['name']}: qty={item['quantity']}, value=₹{item['stock_value']:.2f}")

    except Exception as e:
        print(f"❌ ERROR in opening stock test: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()
        print("Database session closed")

else:
    print("❌ No DATABASE_URL found")
