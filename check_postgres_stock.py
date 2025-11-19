#!/usr/bin/env python3
"""
Check products and stock in PostgreSQL database
"""

import os
from dotenv import load_dotenv
import psycopg2
import json

# Load environment variables
load_dotenv()

def check_stock():
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()

        print("🔍 Checking products and stock in PostgreSQL database")

        # Get total counts
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM products WHERE stock > 0")
        products_with_stock = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM purchases")
        total_purchases = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sales")
        total_sales = cursor.fetchone()[0]

        print("📊 Database Summary:")
        print(f"   - Total Products: {total_products}")
        print(f"   - Products with Stock > 0: {products_with_stock}")
        print(f"   - Total Purchases: {total_purchases}")
        print(f"   - Total Sales: {total_sales}")

        # Get first 10 products
        cursor.execute("""
            SELECT id, name, stock, purchase_price, selling_price, unit_type
            FROM products
            ORDER BY id
            LIMIT 10
        """)

        products = cursor.fetchall()
        print("\n📦 First 10 Products:")
        print("ID | Name | Stock | Buy Price | Sell Price | Unit")

        for product in products:
            print(f"{product[0]} | {product[1][:15]:15} | {product[2]:5} | ₹{product[3]:6.2f} | ₹{product[4]:6.2f} | {product[5]}")

        # Check a few specific products with purchases/sales
        cursor.execute("""
            SELECT
                p.id, p.name, p.stock,
                COUNT(pu.id) as purchases,
                COALESCE(SUM(pu.quantity), 0) as total_purchased,
                COUNT(s.id) as sales_count,
                COALESCE(SUM(s.total_amount), 0) as total_sales_value
            FROM products p
            LEFT JOIN purchases pu ON p.id = pu.product_id
            LEFT JOIN sales s ON p.id = s.product_id
            WHERE p.stock > 0
            GROUP BY p.id, p.name, p.stock
            ORDER BY p.stock DESC
            LIMIT 5
        """)

        stocked_products = cursor.fetchall()
        print("\n💰 Products with stock (showing top 5 by quantity):")
        for product in stocked_products:
            print(f"ID: {product[0]}, Name: {product[1]}, Stock: {product[2]}, "
                  f"Purchases: {product[3]}, Total Purchased: {product[4]}, "
                  f"Sales Count: {product[5]}, Sales Value: ₹{product[6]:.2f}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error checking stock: {e}")

if __name__ == "__main__":
    check_stock()
