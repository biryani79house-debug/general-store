#!/usr/bin/env python3
import os
import sys
sys.path.append('.')
from main import SessionLocal, Sale
from sqlalchemy import text

def check_sales_database():
    from main import Product

    db = SessionLocal()
    try:
        # Test connection
        db.execute(text('SELECT 1'))
        print('✅ Database connected successfully')

        # Get all sales and products
        sales = db.query(Sale).order_by(Sale.id).all()
        products = db.query(Product).all()
        print(f'📊 Total sales records: {len(sales)}')
        print(f'📦 Total products in database: {len(products)}')

        # Create product lookup
        product_lookup = {p.id: p for p in products}

        # Check data integrity - verify all sales reference valid products
        invalid_sales = []
        valid_sales = []

        for sale in sales:
            if sale.product_id not in product_lookup:
                invalid_sales.append(sale)
            else:
                valid_sales.append(sale)

        print(f'✅ Valid sales: {len(valid_sales)}')
        if invalid_sales:
            print(f'❌ Invalid sales (referencing non-existent products): {len(invalid_sales)}')
            for sale in invalid_sales:
                print(f'  Sale ID {sale.id}: references product_id {sale.product_id} - NOT FOUND')
        else:
            print('✅ All sales reference valid products')

        # Group by bill_id
        bill_groups = {}
        for sale in sales:
            bill_id = sale.bill_id if sale.bill_id else 'NULL'
            if bill_id not in bill_groups:
                bill_groups[bill_id] = []
            bill_groups[bill_id].append(sale.id)

        print(f'📋 Total unique bill_ids: {len(bill_groups)}')

        # Show bill distribution with product details
        print('\n📋 Bill ID Distribution (with products):')
        for bill_id, sale_ids in sorted(bill_groups.items()):
            bill_sales = [s for s in sales if (s.bill_id == bill_id if bill_id != 'NULL' else s.bill_id is None)]
            total_amount = sum(s.total_amount for s in bill_sales)

            print(f'  Bill {bill_id}: {len(sale_ids)} sales, Total: ₹{total_amount:.2f}')
            for sale in bill_sales:
                product_name = sale.product.name if sale.product else "INVALID PRODUCT"
                print(f'    • Sale {sale.id}: {product_name} (ID: {sale.product_id}) - ₹{sale.total_amount}')

        # Check for sales without bill_id
        null_bill_sales = [s for s in sales if s.bill_id is None]
        if null_bill_sales:
            print(f'\n⚠️ Found {len(null_bill_sales)} sales without bill_id:')
            for sale in null_bill_sales[:10]:
                product_name = sale.product.name if sale.product else "INVALID PRODUCT"
                print(f'  Sale ID {sale.id}: {product_name} - ₹{sale.total_amount}')
            if len(null_bill_sales) > 10:
                print(f'  ... and {len(null_bill_sales) - 10} more')

        # Check recent sales with product validation
        print(f'\n🕒 Recent sales (last 10) with product validation:')
        recent_sales = sales[-10:] if len(sales) >= 10 else sales
        for sale in recent_sales:
            bill_id = sale.bill_id if sale.bill_id else 'NULL'
            product_name = sale.product.name if sale.product else "INVALID PRODUCT"
            product_status = "✅" if sale.product else "❌"
            print(f'  {product_status} Sale {sale.id}: Bill {bill_id}, {product_name} (ID: {sale.product_id}), ₹{sale.total_amount}')

        # Check for orders with customer info (WhatsApp orders)
        whatsapp_orders = [s for s in sales if s.customer_name and s.customer_phone]
        if whatsapp_orders:
            print(f'\n📱 WhatsApp orders found: {len(whatsapp_orders)}')
            # Group WhatsApp orders by bill_id
            whatsapp_bills = {}
            for sale in whatsapp_orders:
                bill_id = sale.bill_id if sale.bill_id else 'NULL'
                if bill_id not in whatsapp_bills:
                    whatsapp_bills[bill_id] = []
                whatsapp_bills[bill_id].append(sale)

            print('📱 WhatsApp Order Bills (with product details):')
            for bill_id, bill_sales in whatsapp_bills.items():
                customer = bill_sales[0].customer_name
                total = sum(s.total_amount for s in bill_sales)
                print(f'  ORDER_{bill_sales[0].id}: Bill {bill_id}, Customer: {customer}, Items: {len(bill_sales)}, Total: ₹{total}')
                for sale in bill_sales:
                    product_name = sale.product.name if sale.product else "INVALID PRODUCT"
                    print(f'    • {product_name} - ₹{sale.total_amount}')

        # Summary
        print(f'\n📊 SUMMARY:')
        print(f'  • Total Products: {len(products)}')
        print(f'  • Total Sales: {len(sales)}')
        print(f'  • Valid Sales: {len(valid_sales)}')
        print(f'  • Invalid Sales: {len(invalid_sales)}')
        print(f'  • Bills: {len(bill_groups)}')
        print(f'  • WhatsApp Orders: {len(whatsapp_orders)}')

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_sales_database()
