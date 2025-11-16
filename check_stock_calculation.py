#!/usr/bin/env python3
from dotenv import load_dotenv
import os
import json
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from main import Product, Purchase, Sale

load_dotenv()

USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if USE_SQLITE else {"options": "-c timezone=Asia/Kolkata"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

def parse_sale_quantity(sale_quantity_str, product):
    """Parse sale quantity from string to numeric value in base units"""
    quantity_str = sale_quantity_str
    quantity = 0

    try:
        # Try to parse as float first (for cases like "2")
        quantity = float(quantity_str)
    except ValueError:
        # If it's a proportion string like "500gm", "500ml", etc.
        if product.proportion_prices:
            try:
                proportion_prices = json.loads(product.proportion_prices)
                unit_type = product.unit_type

                # Check if quantity_str matches any proportion name
                for prop_name, prop_price in proportion_prices.items():
                    if quantity_str == prop_name:
                        # Found the proportion, calculate quantity based on proportion size
                        prop_price_float = float(prop_price)

                        if unit_type == 'kgs':
                            if prop_name.endswith('gm') or prop_name.endswith('g'):
                                try:
                                    gram_value = float(prop_name.replace('gm', '').replace('g', ''))
                                    quantity = gram_value / 1000.0
                                except ValueError:
                                    quantity = 1
                            elif prop_name.endswith('kg'):
                                try:
                                    quantity = float(prop_name.replace('kg', ''))
                                except ValueError:
                                    quantity = 1
                            else:
                                quantity = prop_price_float / product.selling_price if product.selling_price > 0 else 1
                        elif unit_type == 'ltr':
                            if prop_name.endswith('ml'):
                                try:
                                    ml_value = float(prop_name.replace('ml', ''))
                                    quantity = ml_value / 1000.0
                                except ValueError:
                                    quantity = 1
                            elif prop_name.endswith('ltr'):
                                try:
                                    quantity = float(prop_name.replace('ltr', ''))
                                except ValueError:
                                    quantity = 1
                            else:
                                quantity = prop_price_float / product.selling_price if product.selling_price > 0 else 1
                        else:
                            quantity = prop_price_float / product.selling_price if product.selling_price > 0 else 1
                        break
            except Exception as e:
                print(f"Error parsing proportion for product {product.id}: {e}")
                quantity = 1

        if quantity == 0:
            quantity = 1

    return quantity

products = db.query(Product).all()

print("Product stock reconciliation:")
print("Product | Current DB Stock | Calculated Stock | Difference")
print("-" * 60)

for product in products:
    # Get all purchases for this product
    purchases = db.query(Purchase).filter(Purchase.product_id == product.id).all()
    total_purchased = sum(p.quantity for p in purchases)

    # Get all sales for this product
    sales = db.query(Sale).filter(Sale.product_id == product.id).all()
    total_sold = sum(parse_sale_quantity(sale.quantity, product) for sale in sales)

    calculated_stock = total_purchased - total_sold

    difference = product.stock - calculated_stock

    print(f"{product.name:<15} | {product.stock:<15.2f} {product.unit_type:<5} | {calculated_stock:<15.2f} {product.unit_type:<5} | {difference:<+10.2f}")

db.close()
