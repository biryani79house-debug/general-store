#!/usr/bin/env python3
"""
Script to update existing products to set initial_stock = current stock
"""
import os
from main import SessionLocal, Product

# Change to the current directory
os.chdir(r'd:\kirana Store Backend')

# Update all products to set initial_stock = stock
db = SessionLocal()
products = db.query(Product).all()

for product in products:
    product.initial_stock = product.stock
    print(f"Updated {product.name}: initial_stock = {product.stock}")

db.commit()
print(f"\n✅ Updated {len(products)} products to set initial_stock = stock")
