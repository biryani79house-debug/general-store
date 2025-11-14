#!/usr/bin/env python3
"""
Check Gold Drop Oil database sales data directly
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

print('🔍 Checking actual Gold Drop Oil sales data from database...')
database_url = os.getenv('DATABASE_URL', 'sqlite:///./kirana_store.db')
print(f'Database: {database_url}')

# Use SQLAlchemy to connect (works with both SQLite and PostgreSQL)
if database_url:
    try:
        # For PostgreSQL, set timezone to IST (Asia/Kolkata) to match stored timestamps
        if 'postgresql' in database_url:
            engine = create_engine(database_url, connect_args={"options": "-c timezone=Asia/Kolkata"})
        else:
            engine = create_engine(database_url, connect_args={"check_same_thread": False})

        with engine.connect() as conn:
            # Check sales for product_id 2
            sales_result = conn.execute(text('SELECT id, product_id, quantity, total_amount, sale_date FROM sales WHERE product_id = 2'))
            sales = sales_result.fetchall()

            print(f'📋 Found {len(sales)} sales records for Gold Drop Oil (product_id: 2):')
            total_parsed_sales = 0
            for sale in sales:
                sale_id, product_id, quantity, amount, sale_date = sale
                print(f'  Sale ID {sale_id}: quantity="{quantity}", amount=₹{amount}')

                # Parse quantity exactly like the parsing function does
                qty_str = str(quantity)
                parsed_qty = 0

                try:
                    parsed_qty = float(qty_str)
                except ValueError:
                    # Handle proportion strings like "500gm", "500ml", etc.
                    if qty_str.endswith('ml'):
                        parsed_qty = float(qty_str.replace('ml', '')) / 1000.0
                    elif qty_str.endswith('ltr'):
                        parsed_qty = float(qty_str.replace('ltr', ''))
                    else:
                        try:
                            parsed_qty = float(qty_str)
                        except ValueError:
                            parsed_qty = 0

                print(f'    ✅ Parsed quantity: {parsed_qty} ltr')
                total_parsed_sales += parsed_qty

            print(f'\n💰 Total parsed sales: {total_parsed_sales} ltr')

            # Check purchases
            purchases_result = conn.execute(text('SELECT id, quantity, total_cost, purchase_date FROM purchases WHERE product_id = 2'))
            purchases = purchases_result.fetchall()

            print(f'\n📦 Found {len(purchases)} purchase records:')
            total_purchases = 0
            for purchase in purchases:
                purchase_id, quantity, cost, purchase_date = purchase
                print(f'  Purchase ID {purchase_id}: quantity={quantity}, cost=₹{cost}')
                total_purchases += quantity

            print(f'\n📊 CALCULATION:')
            print(f'  Total purchases: {total_purchases} ltr')
            print(f'  Total parsed sales: {total_parsed_sales} ltr')
            expected_stock = total_purchases - total_parsed_sales
            print(f'  Expected current stock: {total_purchases} - {total_parsed_sales} = {expected_stock} ltr')

            # Check current product stock in database
            stock_result = conn.execute(text('SELECT stock FROM products WHERE id = 2'))
            current_db_stock = stock_result.fetchone()
            if current_db_stock:
                print(f'  Database current stock: {current_db_stock[0]} ltr')

    except Exception as e:
        print(f'❌ Database connection error: {e}')
        print('Try running this after the server is running, as the DATABASE_URL may be set in the running environment.')
