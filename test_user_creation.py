#!/usr/bin/env python3
"""
Script to create the default admin user 'raza123' if it doesn't exist
"""

import os
import bcrypt
from datetime import datetime, timezone, timedelta

# Set environment variables for production database
os.environ["USE_SQLITE"] = "false"
os.environ["DATABASE_URL"] = "postgresql://postgres:TzzzioGfTBxTHRUOgZRzttAxUruaEvLg@yamanote.proxy.rlwy.net:50037/railway"

# Import our app components
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, text
from sqlalchemy.orm import declarative_base, sessionmaker
import sys

# Copy the database models from main.py
IST = timezone(timedelta(hours=5, minutes=30))

Base = declarative_base()

class User(Base):
    """User authentication and role management."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    # Individual permissions instead of roles
    sales = Column(Boolean, default=True)
    purchase = Column(Boolean, default=True)
    create_product = Column(Boolean, default=True)
    delete_product = Column(Boolean, default=True)
    sales_ledger = Column(Boolean, default=True)
    purchase_ledger = Column(Boolean, default=True)
    stock_ledger = Column(Boolean, default=True)
    profit_loss = Column(Boolean, default=True)
    opening_stock = Column(Boolean, default=True)
    user_management = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(IST))

def main():
    print("🔧 Creating default admin user 'raza123'")

    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not set")
        return

    print(f"📡 Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'database'}")

    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Test connection
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("✅ Database connection successful")
        except Exception as conn_error:
            print(f"❌ Database connection failed: {conn_error}")
            return

        # Create tables if they don't exist
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created/verified")
        except Exception as table_error:
            print(f"❌ Failed to create tables: {table_error}")
            return

        # Check if admin user already exists
        db = SessionLocal()
        try:
            existing_user = db.query(User).filter(User.username == "raza123").first()

            if existing_user:
                print(f"⚠️ Admin user 'raza123' already exists (ID: {existing_user.id})")
                # Update permissions just in case
                existing_user.sales = True
                existing_user.purchase = True
                existing_user.create_product = True
                existing_user.delete_product = True
                existing_user.sales_ledger = True
                existing_user.purchase_ledger = True
                existing_user.stock_ledger = True
                existing_user.profit_loss = True
                existing_user.opening_stock = True
                existing_user.user_management = True
                db.commit()
                print("✅ Admin permissions updated for existing user")
                return

            # Create default admin user
            default_password = "123456"  # Changed to match what user wants
            hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())

            admin_user = User(
                username="raza123",
                email="admin@kirana.store",
                password_hash=hashed_password.decode('utf-8'),
                # Grant all admin permissions
                sales=True,
                purchase=True,
                create_product=True,
                delete_product=True,
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

            print("✅ Default admin user created successfully!")
            print(f"   Username: raz123")
            print(f"   Password: {default_password}")
            print(f"   User ID: {admin_user.id}")
            print("   🔑 All admin permissions granted")
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()
