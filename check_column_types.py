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
        # Get column types for sales table
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name='sales' AND table_schema='public'
            ORDER BY ordinal_position
        """))
        print("Sales table column types:")
        for row in result:
            print(f"  {row[0]}: {row[1]} {'NULL' if row[2] == 'YES' else 'NOT NULL'} {row[3] or ''}")

except Exception as e:
    print(f'❌ Error: {e}')
