#!/usr/bin/env python3
"""
Migration script to update existing products with default categories in PostgreSQL database.
This assigns default categories to products that don't have categories set.
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use environment variable for database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not set. Please set DATABASE_URL environment variable.")
    print("Example: postgresql://username:password@host:port/database")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

def main():
    """Update existing products with default categories"""
    print("🏗️  Updating existing products with default categories...")

    try:
        # Get a connection
        connection = engine.connect()

        # First, check how many products exist and how many have null categories
        result = connection.execute(text("SELECT COUNT(*) as total FROM products"))
        total_products = result.fetchone()[0]

        result = connection.execute(text("SELECT COUNT(*) as null_category FROM products WHERE category IS NULL OR category = ''"))
        null_categories = result.fetchone()[0]

        print(f"📊 Found {total_products} total products, {null_categories} with null/empty categories")

        if null_categories == 0:
            print("ℹ️  All products already have categories assigned - no update needed")
            connection.close()
            return

        # Define category assignments based on product names
        category_assignments = {
            # Groceries
            'rice': 'Groceries',
            'sugar': 'Groceries',
            'wheat flour': 'Groceries',
            'besan': 'Groceries',
            'daal': 'Groceries',
            'cooking oil': 'Groceries',
            'spices': 'Groceries',
            'salt': 'Groceries',
            'tea': 'Groceries',
            'coffee': 'Groceries',
            'biscuits': 'Groceries',
            'noodles': 'Groceries',
            'pasta': 'Groceries',
            'cereals': 'Groceries',

            # Vegetables
            'potato': 'Vegetables',
            'onion': 'Vegetables',
            'tomato': 'Vegetables',
            'carrot': 'Vegetables',
            'cabbage': 'Vegetables',
            'cauliflower': 'Vegetables',
            'spinach': 'Vegetables',
            'lettuce': 'Vegetables',
            'brinjal': 'Vegetables',
            'capsicum': 'Vegetables',
            'beans': 'Vegetables',
            'peas': 'Vegetables',
            'broccoli': 'Vegetables',

            # Fruits
            'apple': 'Fruits',
            'banana': 'Fruits',
            'orange': 'Fruits',
            'grapes': 'Fruits',
            'mango': 'Fruits',
            'pineapple': 'Fruits',
            'watermelon': 'Fruits',
            'papaya': 'Fruits',
            'guava': 'Fruits',
            'kiwi': 'Fruits',
            'strawberry': 'Fruits',

            # Dairy
            'milk': 'Dairy',
            'cheese': 'Dairy',
            'butter': 'Dairy',
            'ghee': 'Dairy',
            'yogurt': 'Dairy',
            'curd': 'Dairy',
            'cream': 'Dairy',

            # Beverages
            'juice': 'Beverages',
            'soda': 'Beverages',
            'energy drink': 'Beverages',
            'coconut water': 'Beverages',
            'sports drink': 'Beverages',

            # Snacks
            'chips': 'Snacks',
            'namkeen': 'Snacks',
            'popcorn': 'Snacks',
            'peanuts': 'Snacks',
            'dry fruits': 'Snacks',
            'chocolate': 'Snacks',
            'cookies': 'Snacks',

            # Bakery
            'bread': 'Bakery',
            ' buns': 'Bakery',
            'cake': 'Bakery',
            'pastry': 'Bakery',

            # Meat & Fish
            'chicken': 'Meat & Fish',
            'fish': 'Meat & Fish',
            'mutton': 'Meat & Fish',
            'eggs': 'Meat & Fish',

            # Household
            'detergent': 'Household',
            'cleaner': 'Household',
            'dish soap': 'Household',
            'laundry': 'Household',

            # Personal Care
            'soap': 'Personal Care',
            'shampoo': 'Personal Care',
            'toothpaste': 'Personal Care',
            'face wash': 'Personal Care',
            'shaving cream': 'Personal Care'
        }

        # Get all products without categories
        result = connection.execute(text("SELECT id, name FROM products WHERE category IS NULL OR category = '' ORDER BY name"))
        products_to_update = result.fetchall()

        updated_count = 0

        for product_id, product_name in products_to_update:
            # Try to find a category based on keywords in the product name
            assigned_category = None
            product_name_lower = product_name.lower()

            # First try exact matches
            for keyword, category in category_assignments.items():
                if keyword in product_name_lower:
                    assigned_category = category
                    break

            # If no keyword match, assign "Groceries" as the most general category
            if not assigned_category:
                assigned_category = 'Groceries'
                print(f"📝 Assigning default category 'Groceries' to: {product_name}")

            # Update the product
            connection.execute(text("UPDATE products SET category = :category WHERE id = :product_id"), {
                'category': assigned_category,
                'product_id': product_id
            })
            updated_count += 1

            print(f"✅ Updated {product_name} -> {assigned_category}")

        # Commit the transaction
        connection.commit()

        print(f"\n📋 Migration Summary:")
        print(f"  - Total products: {total_products}")
        print(f"  - Products updated: {updated_count}")
        print(f"  - Categories assigned: {len(set([cat for cat in category_assignments.values()]))} types")

        if updated_count > 0:
            print("✅ All existing products now have category assignments!")

        connection.close()

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if 'connection' in locals():
            connection.rollback()
            connection.close()
        sys.exit(1)

if __name__ == "__main__":
    main()
