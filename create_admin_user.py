#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import User, get_db
import bcrypt

# Create admin user in PostgreSQL
db = next(get_db())

# Check if admin user already exists
existing_admin = db.query(User).filter(User.username == "raza123").first()
if existing_admin:
    print("Admin user 'raza123' already exists")
else:
    # Create admin user
    password = "123456"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    admin_user = User(
        username="raza123",
        email="admin@kirana.store",
        password_hash=hashed_password.decode('utf-8'),
        # Grant all permissions
        sales=True,
        purchase=True,
        create_product=True,
        delete_product=True,
        create_category=True,
        delete_category=True,
        sales_ledger=True,
        purchase_ledger=True,
        stock_ledger=True,
        profit_loss=True,
        opening_stock=True,
        user_management=True,
        is_active=True
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    print(f"✅ Admin user 'raza123' created successfully with password '{password}'")
    print(f"User ID: {admin_user.id}")

db.close()
