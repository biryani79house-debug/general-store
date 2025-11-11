#!/usr/bin/env python3
"""
Check proportion column in PostgreSQL database
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_postgres_proportion():
    """Check proportion values in PostgreSQL database"""
    try:
        # Get database URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables")
            return False

        print("📡 Connecting to PostgreSQL database...")

        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Check all products and their proportions
        cursor.execute("SELECT id, name, proportion FROM products ORDER BY id")
        products = cursor.fetchall()

        print(f"Found {len(products)} products in database:")
        for product in products:
            proportion = product[2] if product[2] is not None else 'None'
            print(f"  ID {product[0]}: {product[1]} -> proportion={proportion}")

        # Specifically check Test Rice 750gm
        cursor.execute("SELECT id, name, proportion FROM products WHERE name = %s", ('Test Rice 750gm',))
        result = cursor.fetchone()
        if result:
            print(f"\nTest Rice 750gm details: ID={result[0]}, name='{result[1]}', proportion='{result[2]}'")
        else:
            print("\nTest Rice 750gm not found in database")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Error checking PostgreSQL: {e}")
        return False

if __name__ == "__main__":
    check_postgres_proportion()
