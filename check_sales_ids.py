#!/usr/bin/env python3
"""
Check the current state of sales IDs in the database
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check sales table structure
    result = conn.execute(text('SELECT id FROM sales ORDER BY id'))
    ids = [row[0] for row in result.fetchall()]
    print(f'Total sales: {len(ids)}')
    print(f'First 10 IDs: {ids[:10]}')
    print(f'Last 10 IDs: {ids[-10:]}')

    # Check for gaps
    expected = list(range(1, len(ids) + 1))
    gaps = [i for i in expected if i not in ids]
    if gaps:
        print(f'Gaps found: {gaps}')
    else:
        print('No gaps found - IDs are consecutive!')

    # Check sequence current value
    try:
        seq_result = conn.execute(text("SELECT last_value FROM sales_id_seq"))
        seq_value = seq_result.fetchone()[0]
        print(f'Current sequence value: {seq_value}')
    except Exception as e:
        print(f'Could not check sequence value: {e}')
