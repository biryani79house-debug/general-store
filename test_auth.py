#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import authenticate_user, get_db
from sqlalchemy.orm import Session

# Test authentication
db = next(get_db())
user = authenticate_user(db, "raza123", "123456")

if user:
    print(f"✅ Authentication successful!")
    print(f"User: {user.username}")
    print(f"Email: {user.email}")
    print(f"Active: {user.is_active}")
    print(f"Permissions: sales={user.sales}, purchase={user.purchase}, create_product={user.create_product}")
else:
    print("❌ Authentication failed")

db.close()
