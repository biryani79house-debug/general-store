#!/usr/bin/env python3
from dotenv import load_dotenv
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Product

load_dotenv()

USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if USE_SQLITE else {"options": "-c timezone=Asia/Kolkata"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()
products = db.query(Product).all()

print("Products as returned by /products API:")
for product in products:
    # Parse proportions JSON string back to list
    proportions_list = None
    if product.proportions:
        try:
            proportions_list = json.loads(product.proportions)
        except:
            proportions_list = None

    # Parse proportion_prices JSON string back to dict
    proportion_prices_dict = None
    if product.proportion_prices:
        try:
            proportion_prices_dict = json.loads(product.proportion_prices)
        except:
            proportion_prices_dict = None

    frontend_product = {
        "id": product.id,
        "name": product.name,
        "price": float(product.selling_price),
        "purchase_price": float(product.purchase_price),
        "selling_price": float(product.selling_price),
        "unit_type": str(product.unit_type),
        "proportions": proportions_list,
        "proportion_prices": proportion_prices_dict,
        "imageUrl": "",
        "stock": product.stock,
        "category": product.category
    }
    print(f"Product: {product.name}, Stock: {frontend_product['stock']} {frontend_product['unit_type']}")

db.close()
