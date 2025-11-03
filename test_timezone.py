#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Use SQLite for local development
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
if USE_SQLITE:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # For PostgreSQL, set timezone to IST to ensure timestamps are returned in IST
    engine = create_engine(DATABASE_URL, connect_args={"options": "-c timezone=Asia/Kolkata"})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_sales_timestamps():
    db = SessionLocal()
    try:
        # Check sales table - get ALL sales first to see total count
        result = db.execute(text("SELECT COUNT(*) FROM sales"))
        total_sales = result.fetchone()[0]
        print(f"=== SALES RECORDS (Total: {total_sales}) ===")

        # Get all sales to see what's available
        result = db.execute(text("SELECT id, product_id, quantity, total_amount, sale_date FROM sales ORDER BY id DESC"))
        all_sales = result.fetchall()

        print(f"Found {len(all_sales)} sale records in database")

        # Show last 10 sales
        sales_to_show = all_sales[:10]
        for sale in sales_to_show:
            print(f"ID: {sale[0]}, Product: {sale[1]}, Quantity: {sale[2]}, Amount: {sale[3]}, Date: {sale[4]}")

        # Specifically check for sale ID 114
        print("\n=== CHECKING FOR SALE ID 114 ===")
        result = db.execute(text("SELECT id, product_id, quantity, total_amount, sale_date FROM sales WHERE id = 114"))
        sale_114 = result.fetchone()
        if sale_114:
            print(f"✅ Sale ID 114 FOUND: {sale_114}")
            print(f"   Date: {sale_114[4]} (should be IST time)")
        else:
            print("❌ Sale ID 114 NOT FOUND")

        # Check max sale ID
        result = db.execute(text("SELECT MAX(id) FROM sales"))
        max_id_result = result.fetchone()
        max_id = max_id_result[0] if max_id_result else 0
        print(f"Maximum sale ID in database: {max_id}")

        # Check purchases table - get ALL purchases first to see total count
        result = db.execute(text("SELECT COUNT(*) FROM purchases"))
        total_purchases = result.fetchone()[0]
        print(f"\n=== PURCHASE RECORDS (Total: {total_purchases}) ===")

        # Get all purchases to see what's available
        result = db.execute(text("SELECT id, product_id, quantity, total_cost, purchase_date FROM purchases ORDER BY id DESC"))
        all_purchases = result.fetchall()

        print(f"Found {len(all_purchases)} purchase records in database")

        # Show last 10 purchases
        purchases_to_show = all_purchases[:10]
        for purchase in purchases_to_show:
            print(f"ID: {purchase[0]}, Product: {purchase[1]}, Quantity: {purchase[2]}, Cost: {purchase[3]}, Date: {purchase[4]}")

        # Specifically check for purchase ID 114
        print("\n=== CHECKING FOR PURCHASE ID 114 ===")
        result = db.execute(text("SELECT id, product_id, quantity, total_cost, purchase_date FROM purchases WHERE id = 114"))
        purchase_114 = result.fetchone()
        if purchase_114:
            print(f"✅ Purchase ID 114 FOUND: {purchase_114}")
        else:
            print("❌ Purchase ID 114 NOT FOUND")

        # Check max purchase ID
        result = db.execute(text("SELECT MAX(id) FROM purchases"))
        max_id_result = result.fetchone()
        max_id = max_id_result[0] if max_id_result else 0
        print(f"Maximum purchase ID in database: {max_id}")

        # Check current timezone setting
        try:
            result = db.execute(text("SHOW timezone"))
            timezone = result.fetchone()
            print(f"\nCurrent database timezone: {timezone[0] if timezone else 'Unknown'}")
        except:
            print("\nCould not check timezone (might be SQLite)")

        # Check raw timestamp storage (without timezone conversion)
        print("\n=== RAW TIMESTAMP CHECK (PostgreSQL) ===")
        try:
            result = db.execute(text("SELECT id, purchase_date AT TIME ZONE 'UTC' as utc_time, purchase_date AT TIME ZONE 'Asia/Kolkata' as ist_time FROM purchases WHERE id = 4"))
            raw_data = result.fetchone()
            if raw_data:
                print(f"Purchase ID 4 - UTC: {raw_data[1]}, IST: {raw_data[2]}")

            # Check what PostgreSQL thinks the stored timestamp is
            result = db.execute(text("SELECT id, purchase_date, EXTRACT(epoch FROM purchase_date) as epoch_seconds FROM purchases WHERE id = 4"))
            raw_data2 = result.fetchone()
            if raw_data2:
                print(f"Raw stored timestamp: {raw_data2[1]}, Epoch: {raw_data2[2]}")

        except Exception as e:
            print(f"Raw timestamp check failed (might be SQLite): {e}")

        # Test current time conversion
        from datetime import datetime, timezone, timedelta
        IST = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(IST)
        now_utc = now_ist.astimezone(timezone.utc)

        print(f"\n=== TIME CONVERSION TEST ===")
        print(f"Current time in IST: {now_ist}")
        print(f"Current time in UTC: {now_utc}")
        print(f"IST hour: {now_ist.hour}, UTC hour: {now_utc.hour}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_sales_timestamps()
