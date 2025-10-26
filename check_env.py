#!/usr/bin/env python3
"""
Check environment variables used by the app
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Environment Variables Check ===")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
print(f"USE_SQLITE: {os.getenv('USE_SQLITE')}")

# Check if .env file exists
if os.path.exists('.env'):
    print(".env file exists")
    with open('.env', 'r') as f:
        print(".env contents:")
        print(f.read())
else:
    print(".env file does NOT exist")
