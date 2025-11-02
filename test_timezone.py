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
        # Check sales table
        result = db.execute(text("SELECT id, product_id, quantity, total_amount, sale_date FROM sales ORDER BY id DESC LIMIT 5"))
        sales = result.fetchall()

        print("=== SALES RECORDS ===")
        if not sales:
            print("No sales records found.")
        else:
            for sale in sales:
                print(f"ID: {sale[0]}, Product: {sale[1]}, Quantity: {sale[2]}, Amount: {sale[3]}, Date: {sale[4]}")

        # Check purchases table
        result = db.execute(text("SELECT id, product_id, quantity, total_cost, purchase_date FROM purchases ORDER BY id DESC LIMIT 5"))
        purchases = result.fetchall()

        print("\n=== PURCHASE RECORDS ===")
        if not purchases:
            print("No purchase records found.")
        else:
            for purchase in purchases:
                print(f"ID: {purchase[0]}, Product: {purchase[1]}, Quantity: {purchase[2]}, Cost: {purchase[3]}, Date: {purchase[4]}")

        # Check specific purchase ID 4
        print("\n=== SPECIFIC PURCHASE ID 4 ===")
        result = db.execute(text("SELECT id, product_id, quantity, total_cost, purchase_date FROM purchases WHERE id = 4"))
        purchase_4 = result.fetchone()
        if purchase_4:
            print(f"ID: {purchase_4[0]}, Product: {purchase_4[1]}, Quantity: {purchase_4[2]}, Cost: {purchase_4[3]}, Date: {purchase_4[4]}")
        else:
            print("Purchase ID 4 not found")

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
