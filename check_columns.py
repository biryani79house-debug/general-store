#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

USE_SQLITE = os.getenv('USE_SQLITE', 'true').lower() == 'true'

if USE_SQLITE:
    DATABASE_URL = 'sqlite:///./kirana_store.db'
else:
    DATABASE_URL = os.getenv('DATABASE_URL')

print(f"Database type: {'SQLite' if USE_SQLITE else 'PostgreSQL'}")
print(f"Database URL: {DATABASE_URL[:50]}...")

engine = create_engine(DATABASE_URL)

# Test database connection and check for proportion column
try:
    with engine.connect() as conn:
        print('Connected to database successfully')

        if USE_SQLITE:
            result = conn.execute(text('PRAGMA table_info(sales)'))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
        else:
            # Check PostgreSQL information schema
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'sales' ORDER BY ordinal_position"))
            column_names = [row[0] for row in result.fetchall()]

        print('Sales table columns:')
        for col in column_names:
            print(f'  - {col}')

        required_columns = ['proportion', 'unit_price']
        missing_columns = [col for col in required_columns if col not in column_names]

        if not missing_columns:
            print('✅ All required columns (proportion, unit_price) exist')
        else:
            print(f'❌ Missing columns: {missing_columns}')

except Exception as e:
    print(f'❌ Database connection or query error: {e}')
    import traceback
    traceback.print_exc()
