from sqlalchemy import create_engine, text
import os

# Load environment variables - only for PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set for PostgreSQL")
    exit(1)

engine = create_engine(DATABASE_URL, connect_args={'options': '-c timezone=Asia/Kolkata'})

# Add customer_address column to sales table if it doesn't exist
try:
    with engine.connect() as conn:
        # Check if column exists (PostgreSQL)
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='sales' AND column_name='customer_address'
        """))

        if not result.fetchone():
            print('Adding customer_address column to sales table...')
            conn.execute(text('ALTER TABLE sales ADD COLUMN customer_address TEXT'))
            conn.commit()
            print('✅ customer_address column added successfully')
        else:
            print('✅ customer_address column already exists')

except Exception as e:
    print(f'❌ Error: {e}')
