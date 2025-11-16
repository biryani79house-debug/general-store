#!/usr/bin/env python3
from dotenv import load_dotenv
import os
load_dotenv()

USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Product

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if USE_SQLITE else {"options": "-c timezone=Asia/Kolkata"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()
products = db.query(Product).all()

print(f"Found {len(products)} products in database:")
for product in products:
    print(f"ID: {product.id}, Name: '{product.name}', Stock: {product.stock}, Unit: {product.unit_type}")

db.close()
