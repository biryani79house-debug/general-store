import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"DATABASE_URL found: {DATABASE_URL is not None}")

if DATABASE_URL:
    print(f"Connecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")

    engine = create_engine(DATABASE_URL, echo=False)
    session = Session(engine)

    try:
        print("\n=== PURCHASES TABLE CHECK ===")

        # Check if purchases table exists
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Available tables: {', '.join(tables)}")

        if 'purchases' in tables:
            print("✅ Purchases table exists")

            # Get count
            result = session.execute(text('SELECT COUNT(*) FROM purchases'))
            count = result.fetchone()[0]
            print(f"Total purchases: {count}")

            # Get null created_by count
            result = session.execute(text('SELECT COUNT(*) FROM purchases WHERE created_by IS NULL'))
            null_count = result.fetchone()[0]
            print(f"Purchases with NULL created_by: {null_count}")

            # Show sample records
            result = session.execute(text('''
                SELECT p.id, p.product_id, pr.name, p.quantity, p.total_cost,
                       p.purchase_date, p.created_by, u.username
                FROM purchases p
                LEFT JOIN products pr ON p.product_id = pr.id
                LEFT JOIN users u ON p.created_by = u.id
                ORDER BY p.purchase_date DESC
                LIMIT 10
            '''))

            print("\nSample purchases:")
            for row in result:
                print(f"ID: {row[0]}, Product: {row[2]}, Qty: {row[3]}, Total: ₹{row[4]:.2f}, Date: {row[5]}, Created by: {row[7]}")

        else:
            print("❌ Purchases table does not exist")

        print("=== CHECK COMPLETE ===")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        session.close()
else:
    print("❌ No DATABASE_URL found")
