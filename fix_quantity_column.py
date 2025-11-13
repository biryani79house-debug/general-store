from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    exit(1)

engine = create_engine(DATABASE_URL, connect_args={'options': '-c timezone=Asia/Kolkata'})

try:
    with engine.connect() as conn:
        # Check current type
        result = conn.execute(text("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name='sales' AND column_name='quantity'
        """))
        current_type = result.fetchone()[0]
        print(f"Current quantity column type: {current_type}")

        if current_type == 'integer':
            print("Changing quantity column from INTEGER to TEXT...")
            # First, we need to handle existing data
            # Since there might be integer data, we'll convert it to string
            conn.execute(text("ALTER TABLE sales ALTER COLUMN quantity TYPE TEXT"))
            conn.commit()
            print("✅ Quantity column changed to TEXT successfully")
        else:
            print("✅ Quantity column is already TEXT")

        # Also fix bill_id to be NOT NULL
        result = conn.execute(text("""
            SELECT is_nullable FROM information_schema.columns
            WHERE table_name='sales' AND column_name='bill_id'
        """))
        is_nullable = result.fetchone()[0]
        if is_nullable == 'YES':
            print("Making bill_id column NOT NULL...")
            # First set default value for existing NULL records
            conn.execute(text("UPDATE sales SET bill_id = 0 WHERE bill_id IS NULL"))
            conn.execute(text("ALTER TABLE sales ALTER COLUMN bill_id SET NOT NULL"))
            conn.commit()
            print("✅ bill_id column made NOT NULL successfully")
        else:
            print("✅ bill_id column is already NOT NULL")

except Exception as e:
    print(f'❌ Error: {e}')
