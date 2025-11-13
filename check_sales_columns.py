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
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='sales' ORDER BY column_name
        """))
        columns = [row[0] for row in result]
        print('Sales table columns:', columns)

        # Check if customer_address exists
        if 'customer_address' in columns:
            print('✅ customer_address column exists')
        else:
            print('❌ customer_address column missing')
            print('Adding customer_address column...')
            conn.execute(text('ALTER TABLE sales ADD COLUMN customer_address TEXT'))
            conn.commit()
            print('✅ customer_address column added successfully')

except Exception as e:
    print(f'❌ Error: {e}')
