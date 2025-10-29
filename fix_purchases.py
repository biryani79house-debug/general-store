import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"DATABASE_URL found: {DATABASE_URL is not None}")

if DATABASE_URL:
    print(f"Connecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")

    engine = create_engine(DATABASE_URL, echo=False)
    session = Session(engine)

    try:
        print("\n=== FIXING PURCHASE CREATED_BY ===")

        # Step 1: Check how many have NULL created_by
        result = session.execute(text('SELECT COUNT(*) FROM purchases WHERE created_by IS NULL'))
        null_count_before = result.fetchone()[0]
        print(f"Before fix: {null_count_before} purchases with NULL created_by")

        # Find admin user ID
        result = session.execute(text("SELECT id FROM users WHERE username = 'raza123' AND is_active = true"))
        admin_row = result.fetchone()
        if admin_row:
            admin_id = admin_row[0]
            print(f"Found admin user ID: {admin_id}")

            # Update purchases
            session.execute(text(f"""
                UPDATE purchases
                SET created_by = {admin_id}
                WHERE created_by IS NULL
            """))
            session.commit()
            print("✅ Updated purchases with admin user ID")

            # Verify
            result = session.execute(text('SELECT COUNT(*) FROM purchases WHERE created_by IS NULL'))
            null_count_after = result.fetchone()[0]
            print(f"After fix: {null_count_after} purchases with NULL created_by")

            # Show updated records
            result = session.execute(text('''
                SELECT p.id, p.product_id, pr.name, p.created_by, u.username
                FROM purchases p
                LEFT JOIN products pr ON p.product_id = pr.id
                LEFT JOIN users u ON p.created_by = u.id
                ORDER BY p.purchase_date DESC
                LIMIT 5
            '''))

            print("\nUpdated purchase records:")
            for row in result:
                print(f"ID: {row[0]}, Product: {row[2]}, Created by: {row[4]} (ID: {row[3]})")

        else:
            print("❌ No admin user 'raza123' found")

        print("=== FIX COMPLETE ===")

    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()

    finally:
        session.close()
else:
    print("❌ No DATABASE_URL found")
