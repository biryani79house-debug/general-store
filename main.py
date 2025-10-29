from datetime import datetime, timezone, timedelta
import os
import io
import csv
from contextlib import asynccontextmanager
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status, Depends, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship, joinedload
from sqlalchemy import ForeignKey, Enum as SQLEnum
import enum
import jwt
import bcrypt
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.messaging_response import MessagingResponse
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

# JWT Secret Key
SECRET_KEY_JWT = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")

# Load environment variables from .env file for local development
load_dotenv()

# Use SQLite for local development, PostgreSQL for production
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./kirana_store.db"
    print("📱 Using SQLite database for local development")
else:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL not set in environment variables!")
        print("Please set your DATABASE_URL environment variable to connect to PostgreSQL")
        print("Example: postgresql://username:password@hostname:port/database_name")
        print("For local development, create a .env file with your DATABASE_URL")
        # Don't crash the app, but it won't work without database
    else:
        print(f"📡 Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Local database'}")

# Initialize the HTTPBearer instance
security = HTTPBearer()

# Create a SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if USE_SQLITE else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

# --- Database Models ---
IST = timezone(timedelta(hours=5, minutes=30))

class UserRole(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"

class Permission(enum.Enum):
    SALES = "sales"
    PURCHASE = "purchase"
    CREATE_PRODUCT = "create_product"
    DELETE_PRODUCT = "delete_product"
    CREATE_CATEGORY = "create_category"
    DELETE_CATEGORY = "delete_category"
    SALES_LEDGER = "sales_ledger"
    PURCHASE_LEDGER = "purchase_ledger"
    STOCK_LEDGER = "stock_ledger"
    PROFIT_LOSS = "profit_loss"
    OPENING_STOCK = "opening_stock"
    USER_MANAGEMENT = "user_management"

# Permissions for each role
ROLE_PERMISSIONS = {
    UserRole.ADMIN.value: [
        Permission.SALES,
        Permission.PURCHASE,
        Permission.CREATE_PRODUCT,
        Permission.DELETE_PRODUCT,
        Permission.SALES_LEDGER,
        Permission.PURCHASE_LEDGER,
        Permission.STOCK_LEDGER,
        Permission.PROFIT_LOSS,
        Permission.OPENING_STOCK,
        Permission.USER_MANAGEMENT,
    ],
    UserRole.MANAGER.value: [
        Permission.SALES,
        Permission.PURCHASE,
        Permission.SALES_LEDGER,
        Permission.PURCHASE_LEDGER,
        Permission.STOCK_LEDGER,
        Permission.OPENING_STOCK,
    ],
    UserRole.EMPLOYEE.value: [
        Permission.SALES,
        Permission.PURCHASE,
    ],
}

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
    create_category = Column(Boolean, default=True)
    delete_category = Column(Boolean, default=True)
    sales_ledger = Column(Boolean, default=True)
    purchase_ledger = Column(Boolean, default=True)
    stock_ledger = Column(Boolean, default=True)
    profit_loss = Column(Boolean, default=True)
    opening_stock = Column(Boolean, default=True)
    user_management = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(IST))
    # Sales relationship
    user_sales = relationship("Sale", back_populates="user", lazy=True)
    # Purchases relationship
    user_purchases = relationship("Purchase", back_populates="user", lazy=True)

class Product(Base):
    """Represents a product in the store."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    purchase_price = Column(Float, nullable=False)  # Cost price when buying from supplier
    selling_price = Column(Float, nullable=False)   # Selling price to customers
    unit_type = Column(String, nullable=False)      # Unit type: kgs, ltr, or pcs
    category = Column(String, nullable=True)        # Category name (optional)
    stock = Column(Float, default=0)                # Current stock level (changes with sales/purchases)
    initial_stock = Column(Float, default=0)        # Initial stock when product was created (immutable)
    created_at = Column(DateTime, default=lambda: datetime.now(IST))

class Sale(Base):
    """Records a single sale transaction."""
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)
    sale_date = Column(DateTime, default=lambda: datetime.now(IST))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    product = relationship("Product")
    user = relationship("User", lazy=True)

class Purchase(Base):
    """Records a purchase of stock from a supplier."""
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    total_cost = Column(Float, nullable=False)
    purchase_date = Column(DateTime, default=lambda: datetime.now(IST))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    product = relationship("Product")
    user = relationship("User", lazy=True)

class Category(Base):
    """Category table for organizing products"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(IST))

# --- Pydantic Models for API Requests/Responses ---
class ProductBase(BaseModel):
    name: str
    purchase_price: float = Field(..., gt=0, description="Purchase price must be a positive number")
    selling_price: float = Field(..., gt=0, description="Selling price must be a positive number")
    unit_type: str = Field(..., description="Unit type: kgs, ltr, or pcs")

class ProductCreate(ProductBase):
    category: Optional[str] = Field(None, description="Product category")
    stock: int = Field(0, ge=0, description="Initial stock level")

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    unit_type: Optional[str] = None
    stock: Optional[int] = None

class ProductResponse(ProductCreate):
    id: int
    created_at: datetime

class SaleCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0, description="Quantity must be positive")

class SaleResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    total_amount: float
    sale_date: datetime

class PurchaseCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0, description="Quantity must be positive")
    unit_cost: float = Field(..., gt=0, description="Cost per unit must be positive")

class PurchaseResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    total_cost: float
    purchase_date: datetime

class OrderItem(BaseModel):
    product_name: str
    quantity: int

class WhatsAppOrderRequest(BaseModel):
    customer_name: str
    phone_number: str
    items: List[OrderItem]

    class Config:
        schema_extra = {
            "example": {
                "customer_name": "John Doe",
                "phone_number": "+919876543210",
                "items": [
                    {"product_name": "Milk", "quantity": 2},
                    {"product_name": "Bread", "quantity": 1}
                ]
            }
        }

class PurchaseLedgerEntry(BaseModel):
    purchase_id: int
    date: datetime
    product_id: int
    product_name: str
    quantity: int
    unit_cost: float
    total_cost: float
    supplier_info: Optional[str] = None

class SalesLedgerEntry(BaseModel):
    sale_id: int
    date: datetime
    product_id: int
    product_name: str
    product_category: Optional[str] = None
    quantity: int
    unit_price: float
    total_amount: float
    customer_info: Optional[str] = None

class ProductStockHistory(BaseModel):
    date: datetime
    transaction_type: str  # "PURCHASE", "SALE", "OPENING"
    reference: str
    quantity: int
    stock_after_transaction: int
    details: str

class ProductStockLedger(BaseModel):
    product_id: int
    product_name: str
    current_stock: int
    opening_stock: int
    total_purchases: int
    total_sales: int
    history: List[ProductStockHistory]

class ProductStockSnapshot(BaseModel):
    product_id: int
    product_name: str
    price: float
    stock: int
    stock_value: float
    unit_type: str
    last_updated: datetime

# --- Pydantic Models for Authentication ---
class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    # Optionally include role for legacy users
    role: Optional[str] = None
    is_active: bool
    # Include permissions for new system
    permissions: Optional[List[str]] = None

class UserCreateRequest(BaseModel):
    username: str
    password: str
    email: str
    sales: bool = False
    purchase: bool = False
    create_product: bool = False
    delete_product: bool = False
    create_category: bool = False
    delete_category: bool = False
    sales_ledger: bool = False
    purchase_ledger: bool = False
    stock_ledger: bool = False
    profit_loss: bool = False
    opening_stock: bool = False
    user_management: bool = False

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Authentication functions
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"⚠️ User '{username}' not found")
        return None
    if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        print(f"⚠️ Invalid password for user '{username}'")
        return None
    print(f"✅ Authentication successful for user '{username}'")
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)  # Token expires in 24 hours
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY_JWT, algorithm="HS256")
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY_JWT, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Lifespan event to create the database tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created.")

        # Test database connection first
        db = SessionLocal()
        db.execute(text("SELECT 1"))

        # Check if the new columns exist by trying to query them
        try:
            # Try to access the new columns to see if they exist
            db.query(Product.purchase_price, Product.selling_price, Product.unit_type).first()
            print("✅ New database schema detected")

            # Check if categories exist
            category_count = db.query(Category).count()
            if category_count == 0:
                # Create sample categories
                sample_categories = [
                    Category(name="Fruits"),
                    Category(name="Vegetables"),
                    Category(name="Dairy"),
                    Category(name="Bakery"),
                    Category(name="Groceries"),
                    Category(name="Beverages"),
                    Category(name="Snacks"),
                    Category(name="Meat & Fish"),
                ]
                db.add_all(sample_categories)
                db.commit()
                print("✅ Sample categories added to database.")

            product_count = db.query(Product).count()
            if product_count == 0:
                print("Seeding database with sample products...")
                sample_products = [
                    Product(name="Apple", purchase_price=80.00, selling_price=100.00, unit_type="kgs", category="Fruits", stock=50),
                    Product(name="Banana", purchase_price=40.00, selling_price=50.00, unit_type="kgs", category="Fruits", stock=30),
                    Product(name="Orange", purchase_price=60.00, selling_price=80.00, unit_type="kgs", category="Fruits", stock=25),
                    Product(name="Milk", purchase_price=50.00, selling_price=65.00, unit_type="ltr", category="Dairy", stock=20),
                    Product(name="Bread", purchase_price=30.00, selling_price=40.00, unit_type="pcs", category="Bakery", stock=15),
                    Product(name="Eggs", purchase_price=70.00, selling_price=90.00, unit_type="pcs", category="Meat & Fish", stock=40),
                    Product(name="Rice", purchase_price=100.00, selling_price=120.00, unit_type="kgs", category="Groceries", stock=60),
                    Product(name="Sugar", purchase_price=45.00, selling_price=55.00, unit_type="kgs", category="Groceries", stock=35),
                ]
                db.add_all(sample_products)
                db.commit()
                print("✅ Sample products added to database.")
            else:
                print(f"Database already contains {product_count} products.")

        except Exception as column_error:
            print(f"⚠️ Schema mismatch detected: {column_error}")
            print("🔄 Attempting to update database schema...")

            # For PostgreSQL/Render, use a safer approach
            try:
                # First, try to add the missing column without dropping tables
                try:
                    # Check if created_at column exists
                    result = db.execute(text("SELECT created_at FROM products LIMIT 1"))
                    print("✅ created_at column already exists")
                except Exception:
                    print("📝 Adding created_at column to products table...")
                    # Add the missing column
                    db.execute(text("ALTER TABLE products ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                    print("✅ created_at column added successfully")

                # Update existing records with current timestamp if they don't have created_at
                try:
                    db.execute(text("UPDATE products SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
                    db.commit()
                    print("✅ Existing records updated with creation timestamps")
                except Exception as update_error:
                    print(f"⚠️ Could not update existing records: {update_error}")
                    # This is not critical, so we'll continue

                # Check if category column exists, if not add it
                try:
                    db.execute(text("ALTER TABLE products ADD COLUMN category STRING"))
                    print("✅ category column added to products table")
                except Exception:
                    print("✅ category column already exists")

                print("✅ Database schema updated successfully")

                # Check if we need sample data
                product_count = db.query(Product).count()
                if product_count == 0:
                    # Create default admin user if no users exist
                    user_count = db.query(User).count()
                    if user_count == 0:
                        default_password = "123456"
                        hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())

                        default_admin = User(
                            username="raza123",
                            email="admin@kirana.store",
                            password_hash=hashed_password.decode('utf-8'),
                            # New permission system - give all permissions to default admin
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
                        db.add(default_admin)
                        db.commit()
                        print(f"✅ Default admin user created: username=raza123, password={default_password}")
                        print("⚠️  PLEASE CHANGE THE DEFAULT PASSWORD AFTER FIRST LOGIN!")

                    # Create sample categories
                    sample_categories = [
                        Category(name="Fruits"),
                        Category(name="Vegetables"),
                        Category(name="Dairy"),
                        Category(name="Bakery"),
                        Category(name="Groceries"),
                        Category(name="Beverages"),
                        Category(name="Snacks"),
                        Category(name="Meat & Fish"),
                    ]
                    db.add_all(sample_categories)
                    db.commit()
                    print("✅ Sample categories added to database.")

                    print("Seeding database with sample products...")
                    sample_products = [
                        Product(name="Apple", purchase_price=80.00, selling_price=100.00, unit_type="kgs", category="Fruits", stock=50),
                        Product(name="Banana", purchase_price=40.00, selling_price=50.00, unit_type="kgs", category="Fruits", stock=30),
                        Product(name="Orange", purchase_price=60.00, selling_price=80.00, unit_type="kgs", category="Fruits", stock=25),
                        Product(name="Milk", purchase_price=50.00, selling_price=65.00, unit_type="ltr", category="Dairy", stock=20),
                        Product(name="Bread", purchase_price=30.00, selling_price=40.00, unit_type="pcs", category="Bakery", stock=15),
                        Product(name="Eggs", purchase_price=70.00, selling_price=90.00, unit_type="pcs", category="Meat & Fish", stock=40),
                        Product(name="Rice", purchase_price=100.00, selling_price=120.00, unit_type="kgs", category="Groceries", stock=60),
                        Product(name="Sugar", purchase_price=45.00, selling_price=55.00, unit_type="kgs", category="Groceries", stock=35),
                    ]
                    db.add_all(sample_products)
                    db.commit()
                    print("✅ Sample products added to database.")
                else:
                    print(f"Database already contains {product_count} products.")

            except Exception as update_error:
                print(f"❌ Failed to update schema: {update_error}")
                print("🔄 Falling back to table recreation method...")

                try:
                    # As a last resort, try the drop/create method
                    Base.metadata.drop_all(bind=engine)
                    Base.metadata.create_all(bind=engine)
                    print("✅ Database schema recreated successfully")

                    # Now add sample data
                    sample_products = [
                        Product(name="Apple", purchase_price=80.00, selling_price=100.00, unit_type="kgs", category="Fruits", stock=50),
                        Product(name="Banana", purchase_price=40.00, selling_price=50.00, unit_type="kgs", category="Fruits", stock=30),
                        Product(name="Orange", purchase_price=60.00, selling_price=80.00, unit_type="kgs", category="Fruits", stock=25),
                        Product(name="Milk", purchase_price=50.00, selling_price=65.00, unit_type="ltr", category="Dairy", stock=20),
                        Product(name="Bread", purchase_price=30.00, selling_price=40.00, unit_type="pcs", category="Bakery", stock=15),
                        Product(name="Eggs", purchase_price=70.00, selling_price=90.00, unit_type="pcs", category="Meat & Fish", stock=40),
                        Product(name="Rice", purchase_price=100.00, selling_price=120.00, unit_type="kgs", category="Groceries", stock=60),
                        Product(name="Sugar", purchase_price=45.00, selling_price=55.00, unit_type="kgs", category="Groceries", stock=35),
                    ]
                    db.add_all(sample_products)
                    db.commit()
                    print("✅ Sample products added to database.")

                except Exception as final_error:
                    print(f"❌ Failed to recreate schema: {final_error}")
                    print("Please check your DATABASE_URL and ensure the database is accessible")

        db.close()

    except Exception as e:
        print(f"❌ Critical database error: {e}")
        # Don't let database errors crash the entire app
        pass

    yield

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Kirana Store Management API",
    description="A backend for managing a local Kirana store's products, sales, and purchases, including an online order simulation.",
    lifespan=lifespan
)

# === FIXED CORS CONFIGURATION ===
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://nonnitric-ably-candra.ngrok-free.dev",
    "http://nonnitric-ably-candra.ngrok-free.dev",
    "https://*.ngrok-free.dev",
    "http://*.ngrok-free.dev",
    "https://kirana-store-seven.vercel.app",  # Add your Vercel frontend
    "https://*.vercel.app",
    "https://kirana-store-backend.onrender.com",
    "https://kirana-store-maoc.onrender.com",
    "https://kirana-store-docker.onrender.com",
    "https://kirana-store-backend-production.up.railway.app",
    "https://web-production-9d240.up.railway.app/",  # Add Railway production backend
    "https://*.railway.app",  # Allow all Railway domains
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# === CORS OPTIONS HANDLERS ===
@app.options("/{path:path}")
async def options_handler(path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "600"
        }
    )

# === YOUR ORIGINAL ENDPOINTS ===

# --- API Endpoint to serve products to the frontend ---
@app.get("/products")
async def get_products(category: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns the list of real products from database for the frontend to display.

    Supports optional category filtering for the sales page.
    """
    try:
        query = db.query(Product)

        # Apply category filter if provided (case-insensitive)
        if category:
            query = query.filter(Product.category.ilike(category))
            print(f"🔍 Filtering products by category: {category}")

        db_products = query.all()
        print(f"📦 Found {len(db_products)} products in database")

        frontend_products = []

        for product in db_products:
            frontend_products.append({
                "id": product.id,
                "name": product.name,
                "price": float(product.selling_price),  # Use selling_price for frontend display
                "purchase_price": float(product.purchase_price),
                "selling_price": float(product.selling_price),
                "unit_type": str(product.unit_type),  # Ensure it's returned as string
                "imageUrl": "",  # Let frontend generate dynamic images
                "stock": product.stock,
                "category": product.category  # Include category for filtering
            })

        print("✅ Successfully formatted products for frontend")
        return JSONResponse(content=frontend_products, media_type="application/json")

    except Exception as e:
        print(f"❌ Error fetching products: {e}")
        fallback_products = [
            {"id": 1, "name": "Apple", "price": 100.00, "imageUrl": "https://placehold.co/400x400/81c784/ffffff?text=Apple", "stock": 50},
            {"id": 2, "name": "Banana", "price": 50.00, "imageUrl": "https://placehold.co/400x400/fff176/ffffff?text=Banana", "stock": 30},
        ]
        return JSONResponse(content=fallback_products, media_type="application/json")

# --- API Endpoints for Products (DB operations) ---
@app.post("/products/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db), username: str = Depends(verify_token)):
    check_permission(Permission.CREATE_PRODUCT, db, username)

    # Handle category creation if provided and doesn't exist
    if hasattr(product, 'category') and product.category:
        # Check if category exists (case-insensitive)
        existing_category = db.query(Category).filter(Category.name.ilike(product.category)).first()
        if not existing_category:
            # Create new category automatically
            new_category = Category(name=product.category)
            db.add(new_category)
            db.flush()  # Get the ID but don't commit yet
            print(f"🆕 Auto-created category: '{product.category}' (ID: {new_category.id})")
        else:
            print(f"📁 Using existing category: '{existing_category.name}' (ID: {existing_category.id})")

    # Create product with initial stock set to current stock (which defaults to 0)
    db_product = Product(
        name=product.name,
        purchase_price=product.purchase_price,
        selling_price=product.selling_price,
        unit_type=product.unit_type,
        category=product.category if hasattr(product, 'category') and product.category else None,
        stock=product.stock,  # Set to provided initial stock
        initial_stock=product.stock  # Set initial stock to provided value
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# 2. ADD THE STOCK-SNAPSHOT ENDPOINT HERE (BEFORE THE DYNAMIC ROUTE)
# --- API Endpoint for Opening Stock Register ---
# Custom model for opening stock register response
class OpeningStockResponse(BaseModel):
    id: int
    name: str
    purchase_price: float
    selling_price: float
    unit_type: str
    quantity: int  # Current stock quantity calculated from purchase register
    stock_value: float  # Pre-calculated stock value using purchase_price
    created_at: datetime

@app.get("/opening-stock-register")
def get_opening_stock_register(db: Session = Depends(get_db), username: str = Depends(verify_token)):
    """
    Get opening stock register showing all products with quantity from purchase register.
    Shows total quantity purchased for each product (from all purchase records).
    """
    check_permission(Permission.OPENING_STOCK, db, username)

    try:
        products = db.query(Product).all()

        opening_stock_data = []

        for product in products:
            # Get total quantity from purchase register for this product
            total_purchase_quantity = db.query(db.func.sum(Purchase.quantity)).filter(Purchase.product_id == product.id).scalar()

            # Handle None case (no purchases yet)
            if total_purchase_quantity is None:
                total_purchase_quantity = 0

            opening_stock_quantity = int(total_purchase_quantity)

            # Pre-calculate stock value using purchase price
            stock_value = opening_stock_quantity * product.purchase_price

            print(f"Product {product.name}: quantity={opening_stock_quantity}, stock_value={stock_value}")

            opening_stock_data.append({
                "id": product.id,
                "name": product.name,
                "purchase_price": product.purchase_price,
                "selling_price": product.selling_price,
                "unit_type": product.unit_type,
                "quantity": opening_stock_quantity,
                "stock_value": stock_value,
                "created_at": product.created_at
            })

        print(f"📊 Generated opening stock register for {len(opening_stock_data)} products")
        print(f"🔍 DEBUG: Response data sample: {opening_stock_data[:2] if opening_stock_data else 'No data'}")
        return opening_stock_data

    except Exception as e:
        print(f"❌ Error generating opening stock register: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating opening stock register: {str(e)}")

@app.get("/products/stock-snapshot", response_model=List[ProductStockSnapshot])
def get_products_stock_snapshot(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    product_id: Optional[int] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
    
):
    """
    Get product stock snapshot with date filtering and category filtering.
    Always shows purchase prices for inventory valuation.
    Without date filters: current stock as of now
    With date filters: stock as of the specified date/end of date range
    """
    try:
        print(f"📊 Generating stock snapshot - Date From: {date_from}, Date To: {date_to}, Product ID: {product_id}")

        # Parse date filters - assume yyyy-mm-dd format from frontend date inputs
        filter_date_from = None
        filter_date_to = None

        if date_from:
            try:
                date_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                filter_date_from = date_dt.replace(tzinfo=IST)  # Start of the selected day
                print(f"📅 Parsed date_from: {filter_date_from}")
            except ValueError as e:
                print(f"⚠️ Invalid date_from format: {date_from}, error: {e}")

        if date_to:
            try:
                date_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                filter_date_to = date_dt.replace(tzinfo=IST) + timedelta(days=1)  # End of the selected day
                print(f"📅 Parsed date_to: {filter_date_to} (from input: {date_to})")
            except ValueError as e:
                print(f"⚠️ Invalid date_to format: {date_to}, error: {e}")

        # Base query for products
        query = db.query(Product)

        # Filter by product if specified
        if product_id:
            query = query.filter(Product.id == product_id)

        # Filter by category if provided (case-insensitive)
        if category:
            query = query.filter(Product.category.ilike(category))

        products = query.all()

        snapshots = []
        for product in products:
            # Default to current stock for no date filters or current date scenario
            calculated_stock = product.stock

            # If date filters are specified, calculate stock as of that date
            if filter_date_to:
                # Get all purchases up to the end of the filter date
                purchases = db.query(Purchase).filter(
                    Purchase.product_id == product.id,
                    Purchase.purchase_date < filter_date_to
                ).all()

                # Get all sales up to the end of the filter date
                sales = db.query(Sale).filter(
                    Sale.product_id == product.id,
                    Sale.sale_date < filter_date_to
                ).all()

                print(f"🔍 DEBUG: Filter date: {filter_date_to}, Product: {product.name}")
                for sale in sales:
                    print(f"   - Sale {sale.id}: Date={sale.sale_date}, Quantity={sale.quantity}")

                # Calculate stock as of the filter date
                # Formula: Stock as of date = Opening Stock + Purchases up to date - Sales up to date

                total_purchases_up_to_date = sum(p.quantity for p in purchases)
                total_sales_up_to_date = sum(s.quantity for s in sales)

                # Calculate what the opening stock was when this product was created
                # Opening Stock = Current Stock + Total Sales Ever - Total Purchases Ever
                all_purchases_ever = db.query(Purchase).filter(Purchase.product_id == product.id).all()
                all_sales_ever = db.query(Sale).filter(Sale.product_id == product.id).all()
                total_purchases_ever = sum(p.quantity for p in all_purchases_ever)
                total_sales_ever = sum(s.quantity for s in all_sales_ever)

                opening_stock = product.stock + total_sales_ever - total_purchases_ever
                calculated_stock = opening_stock + total_purchases_up_to_date - total_sales_up_to_date

                print(f"📊 Product {product.name}: Opening stock={opening_stock}, Purchases up to {filter_date_to.date()}={total_purchases_up_to_date}, Sales up to {filter_date_to.date()}={total_sales_up_to_date}, Calculated stock={calculated_stock}")

            elif filter_date_from:
                # If only date_from is specified, show stock at the end of that day
                # Set a date_to for the end of date_from day
                date_to_temp = filter_date_from + timedelta(days=1)

                purchases = db.query(Purchase).filter(
                    Purchase.product_id == product.id,
                    Purchase.purchase_date < date_to_temp
                ).all()

                sales = db.query(Sale).filter(
                    Sale.product_id == product.id,
                    Sale.sale_date < date_to_temp
                ).all()

                total_purchases_up_to_date = sum(p.quantity for p in purchases)
                total_sales_up_to_date = sum(s.quantity for s in sales)

                # Calculate opening stock and then add purchases - sales up to date
                all_purchases_ever = db.query(Purchase).filter(Purchase.product_id == product.id).all()
                all_sales_ever = db.query(Sale).filter(Sale.product_id == product.id).all()
                total_purchases_ever = sum(p.quantity for p in all_purchases_ever)
                total_sales_ever = sum(s.quantity for s in all_sales_ever)

                opening_stock = product.stock + total_sales_ever - total_purchases_ever
                calculated_stock = opening_stock + total_purchases_up_to_date - total_sales_up_to_date

            # Always use purchase price for stock valuation
            purchase_price = product.purchase_price
            stock_value = purchase_price * calculated_stock

            # Ensure proper type conversions for the Pydantic model
            snapshots.append(ProductStockSnapshot(
                product_id=product.id,
                product_name=product.name,
                price=purchase_price,  # Always purchase price for inventory valuation
                stock=int(calculated_stock),
                stock_value=float(stock_value),
                unit_type=product.unit_type,
                last_updated=datetime.now(IST)
            ))

        print(f"✅ Generated {len(snapshots)} stock snapshots")
        return snapshots

    except Exception as e:
        print(f"❌ Error generating stock snapshot: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating stock data: {str(e)}")

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return db_product

@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product_data: ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    for key, value in product_data.dict(exclude_unset=True).items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: int, db: Session = Depends(get_db), username: str = Depends(verify_token)):
    """
    Delete a product and all its associated sales and purchase records.
    After deletion, renumber all products with higher IDs to maintain serial order.
    """
    try:
        # Find the product
        db_product = db.query(Product).filter(Product.id == product_id).first()
        if db_product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        # Get product name for response message
        product_name = db_product.name

        # Delete all associated sales records first
        sales_count = db.query(Sale).filter(Sale.product_id == product_id).count()
        if sales_count > 0:
            db.query(Sale).filter(Sale.product_id == product_id).delete()
            print(f"Deleted {sales_count} sales records for product {product_name}")

        # Delete all associated purchase records
        purchases_count = db.query(Purchase).filter(Purchase.product_id == product_id).count()
        if purchases_count > 0:
            db.query(Purchase).filter(Purchase.product_id == product_id).delete()
            print(f"Deleted {purchases_count} purchase records for product {product_name}")

        # Now delete the product
        db.delete(db_product)
        db.flush()  # Don't commit yet, we need to renumber

        # Now renumber all products with ID > deleted product ID
        # First, drop foreign key constraints temporarily
        db.execute(text("ALTER TABLE purchases DROP CONSTRAINT purchases_product_id_fkey;"))
        db.execute(text("ALTER TABLE sales DROP CONSTRAINT sales_product_id_fkey;"))

        # Get all products with ID > product_id and renumber them down by 1
        products_to_renumber = db.query(Product).filter(Product.id > product_id).order_by(Product.id).all()

        for product in products_to_renumber:
            new_id = product.id - 1
            # Update product ID
            db.execute(text("UPDATE products SET id = :new_id WHERE id = :current_id"), {"new_id": new_id, "current_id": product.id})
            # Update foreign key references
            db.execute(text("UPDATE sales SET product_id = :new_id WHERE product_id = :old_id"), {"new_id": new_id, "old_id": product.id})
            db.execute(text("UPDATE purchases SET product_id = :new_id WHERE product_id = :old_id"), {"new_id": new_id, "old_id": product.id})

        # Recreate foreign key constraints
        db.execute(text("ALTER TABLE purchases ADD CONSTRAINT purchases_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id);"))
        db.execute(text("ALTER TABLE sales ADD CONSTRAINT sales_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id);"))

        # Commit all changes
        db.commit()

        return {
            "status": "success",
            "message": f"Product '{product_name}' deleted successfully. Removed {sales_count} sales and {purchases_count} purchases. Products have been renumbered to maintain serial order.",
            "product_id": product_id,
            "sales_deleted": sales_count,
            "purchases_deleted": purchases_count,
            "renumbered_products": len(products_to_renumber)
        }

    except Exception as e:
        db.rollback()
        print(f"Error deleting product {product_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting product: {str(e)}"
        )
# --- API Endpoints for Sales ---
@app.post("/sales/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def record_sale(sale: SaleCreate, db: Session = Depends(get_db), username: str = None):
    # Accept optional authentication - use token if available
    from fastapi import Depends
    try:
        username = verify_token(token=None)  # This will work differently, need to try
    except:
        username = None

    product = db.query(Product).filter(Product.id == sale.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.stock < sale.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough stock available")

    # Set created_by based on whom is recording the sale
    if username:
        # Authenticated user is recording the sale
        user = db.query(User).filter(User.username == username).first()
        if user:
            created_by = user.id
        else:
            # Fallback to first admin user if possible
            admin_user = db.query(User).filter(User.username == "raza123").first()
            created_by = admin_user.id if admin_user else 1  # Fallback to ID 1
    else:
        # Customer is placing the order or anonymous transaction
        customer_user = db.query(User).filter(User.username == "customer").first()
        if customer_user:
            created_by = customer_user.id
        else:
            # Fallback to first available user (should always have at least admin)
            first_user = db.query(User).first()
            created_by = first_user.id if first_user else 1

    # Use product's selling_price for the sale
    selling_price = product.selling_price
    total_amount = selling_price * sale.quantity

    db_sale = Sale(
        product_id=sale.product_id,
        quantity=sale.quantity,
        total_amount=total_amount,
        sale_date=datetime.now(IST),
        created_by=created_by
    )
    product.stock -= sale.quantity

    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale

# --- API Endpoints for Purchases ---
@app.post("/purchases/", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
def record_purchase(purchase: PurchaseCreate, db: Session = Depends(get_db), username: str = Depends(verify_token)):
    check_permission(Permission.PURCHASE, db, username)

    # Get the user who is creating this purchase
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    product = db.query(Product).filter(Product.id == purchase.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    total_cost = purchase.unit_cost * purchase.quantity
    db_purchase = Purchase(
        product_id=purchase.product_id,
        quantity=purchase.quantity,
        total_cost=total_cost,
        purchase_date=datetime.now(IST),
        created_by=user.id  # Set the user who created this purchase
    )
    product.stock += purchase.quantity

    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)
    return db_purchase

# --- ADD DELETE ENDPOINTS FOR SALES AND PURCHASES ---

@app.delete("/sales/{sale_id}", status_code=status.HTTP_200_OK)
def delete_sale(sale_id: int, db: Session = Depends(get_db)):
    """
    Delete a sale record and restore product stock.
    """
    try:
        # Find the sale record
        db_sale = db.query(Sale).filter(Sale.id == sale_id).first()
        if not db_sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale record not found")
        
        # Find the product
        product = db.query(Product).filter(Product.id == db_sale.product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        # Restore the stock
        product.stock += db_sale.quantity
        
        # Delete the sale record
        db.delete(db_sale)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Sale record deleted successfully. Restored {db_sale.quantity} units to {product.name} stock.",
            "sale_id": sale_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting sale: {str(e)}")

@app.delete("/purchases/{purchase_id}", status_code=status.HTTP_200_OK)
def delete_purchase(purchase_id: int, db: Session = Depends(get_db)):
    """
    Delete a purchase record and adjust product stock.
    """
    try:
        # Find the purchase record
        db_purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
        if not db_purchase:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase record not found")
        
        # Find the product
        product = db.query(Product).filter(Product.id == db_purchase.product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        # Check if we have enough stock to remove
        if product.stock < db_purchase.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Cannot delete purchase. Current stock ({product.stock}) is less than purchase quantity ({db_purchase.quantity})"
            )
        
        # Remove the purchased stock
        product.stock -= db_purchase.quantity
        
        # Delete the purchase record
        db.delete(db_purchase)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Purchase record deleted successfully. Removed {db_purchase.quantity} units from {product.name} stock.",
            "purchase_id": purchase_id
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting purchase: {str(e)}")

# --- API Endpoint for WhatsApp Orders ---
@app.post("/whatsapp-order/", status_code=status.HTTP_200_OK)
def process_whatsapp_order(order_request: WhatsAppOrderRequest, db: Session = Depends(get_db)):
    """Simulates receiving an order from a WhatsApp webhook."""
    total_bill = 0
    items_sold = []
    
    for item in order_request.items:
        product = db.query(Product).filter(Product.name.ilike(item.product_name)).first()
        if not product:
            return {"status": "error", "message": f"Product '{item.product_name}' not found."}
        
        if product.stock < item.quantity:
            return {"status": "error", "message": f"Insufficient stock for '{item.product_name}'."}

        item_total = product.selling_price * item.quantity
        total_bill += item_total
        product.stock -= item.quantity
        
        db_sale = Sale(
            product_id=product.id,
            quantity=item.quantity,
            total_amount=item_total,
            created_by=1  # Default admin user for WhatsApp orders
        )
        db.add(db_sale)
        items_sold.append(item.product_name)
    
    db.commit()
    
    response_message = (
        f"Thank you, {order_request.customer_name}! Your order for {', '.join(items_sold)} "
        f"has been placed. Your total bill is Rs. {total_bill:.2f}. "
        "We will notify you once the payment is confirmed and the delivery is on its way."
    )
    
    print(f"Online order received from {order_request.customer_name} ({order_request.phone_number}). "
          f"Total bill: Rs. {total_bill:.2f}")

    return {"status": "success", "message": response_message, "total_bill": total_bill}

# --- Dummy product data for SMS handler ---
PRODUCTS_DB = {
    "apple": 100.00,
    "banana": 50.00,
    "orange": 80.00,
    "milk": 65.00,
    "bread": 40.00,
    "eggs": 90.00,
    "rice": 120.00,
    "sugar": 55.00
}

# --- 1. PURCHASE LEDGER - All Purchase Details ---
@app.get("/ledger/purchases", response_model=List[PurchaseLedgerEntry])
def get_purchase_ledger(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    product_id: Optional[int] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    username: str = Depends(verify_token)
):
    """
    Get complete purchase ledger with all purchase details.
    Supports filtering by date range, product, and category.
    Simplified to query purchases directly like the download endpoint.
    """
    try:
        check_permission(Permission.PURCHASE_LEDGER, db, username)
        print(f"🔄 Starting purchase ledger data retrieval for user: {username}")

        # Simplified approach - just query purchases data directly
        query = db.query(Purchase).options(joinedload(Purchase.product))

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Purchase.purchase_date >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Purchase.purchase_date <= end_dt)
        if product_id:
            query = query.filter(Purchase.product_id == product_id)

        # Filter by category if provided (case-insensitive)
        if category:
            query = query.filter(Purchase.product.has(Product.category.ilike(category)))

        purchases = query.order_by(Purchase.purchase_date.desc()).all()
        print(f"✅ Found {len(purchases)} purchase records")

        # Convert to simple format
        ledger_entries = []
        for purchase in purchases:
            unit_cost = purchase.total_cost / purchase.quantity if purchase.quantity > 0 else 0
            ledger_entries.append(PurchaseLedgerEntry(
                purchase_id=purchase.id,
                date=purchase.purchase_date,
                product_id=purchase.product_id,
                product_name=purchase.product.name if purchase.product else "Unknown",
                quantity=purchase.quantity,
                unit_cost=unit_cost,
                total_cost=purchase.total_cost,
                supplier_info=f"Supplier for {purchase.product.name if purchase.product else 'Unknown'}"
            ))

        print(f"🔄 Returning {len(ledger_entries)} purchase ledger entries")
        return ledger_entries

    except Exception as e:
        print(f"❌ ERROR in get_purchase_ledger: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error retrieving purchase ledger data: {str(e)}")

# --- 2. SALES LEDGER - All Sales Details ---
@app.get("/ledger/sales", response_model=List[SalesLedgerEntry])
def get_sales_ledger(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    product_id: Optional[int] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    username: str = Depends(verify_token)
):
    """
    Get complete sales ledger with all sales details.
    Supports filtering by date range, product, and category.
    Simplified to query sales directly like the download endpoint.
    """
    try:
        check_permission(Permission.SALES_LEDGER, db, username)
        print(f"🔄 Starting sales ledger data retrieval for user: {username}")

        # Simplified approach - just query sales data directly
        query = db.query(Sale).options(joinedload(Sale.product))

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Sale.sale_date >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Sale.sale_date <= end_dt)
        if product_id:
            query = query.filter(Sale.product_id == product_id)

        # Filter by category if provided (case-insensitive)
        if category:
            query = query.filter(Sale.product.has(Product.category.ilike(category)))

        sales = query.order_by(Sale.sale_date.desc()).all()
        print(f"✅ Found {len(sales)} sales records")

        # Convert to simple format
        ledger_entries = []
        for sale in sales:
            unit_price = sale.total_amount / sale.quantity if sale.quantity > 0 else 0
            ledger_entries.append(SalesLedgerEntry(
                sale_id=sale.id,
                date=sale.sale_date,
                product_id=sale.product_id,
                product_name=sale.product.name if sale.product else "Unknown",
                product_category=sale.product.category if sale.product else None,
                quantity=sale.quantity,
                unit_price=unit_price,
                total_amount=sale.total_amount,
                customer_info=f"Customer for {sale.product.name if sale.product else 'Unknown'}"
            ))

        print(f"🔄 Returning {len(ledger_entries)} sales ledger entries")
        return ledger_entries

    except Exception as e:
        print(f"❌ ERROR in get_sales_ledger: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error retrieving sales ledger data: {str(e)}")

# --- 3. STOCK LEDGER BY PRODUCT - Full History for Specific Product ---
@app.get("/ledger/stock/{product_id}", response_model=ProductStockLedger)
def get_product_stock_ledger(product_id: int, db: Session = Depends(get_db)):
    """
    Get complete stock history for a specific product.
    Shows opening stock, all purchases, all sales, and running balance.
    """
    # Get the product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get all purchases for this product (ordered by date)
    purchases = db.query(Purchase).filter(Purchase.product_id == product_id).order_by(Purchase.purchase_date).all()
    
    # Get all sales for this product (ordered by date)
    sales = db.query(Sale).filter(Sale.product_id == product_id).order_by(Sale.sale_date).all()
    
    # Combine and sort all transactions by date
    all_transactions = []
    
    for purchase in purchases:
        all_transactions.append({
            "date": purchase.purchase_date,
            "type": "PURCHASE",
            "reference": f"Purchase #{purchase.id}",
            "quantity": purchase.quantity,
            "details": f"Purchased {purchase.quantity} units at ₹{purchase.total_cost/purchase.quantity:.2f} each"
        })
    
    for sale in sales:
        all_transactions.append({
            "date": sale.sale_date,
            "type": "SALE", 
            "reference": f"Sale #{sale.id}",
            "quantity": -sale.quantity,  # Negative for sales
            "details": f"Sold {sale.quantity} units at ₹{sale.total_amount/sale.quantity:.2f} each"
        })
    
    # Sort all transactions by date
    all_transactions.sort(key=lambda x: x["date"])
    
    # Calculate running balance
    current_stock = 0
    history = []
    
    # Add opening balance entry
    if all_transactions:
        # Calculate what the opening stock would have been
        total_purchases = sum(p.quantity for p in purchases)
        total_sales = sum(s.quantity for s in sales)
        opening_stock = product.stock + total_sales - total_purchases
        current_stock = opening_stock
    else:
        opening_stock = product.stock
        current_stock = product.stock
    
    # Add opening entry
    history.append(ProductStockHistory(
        date=all_transactions[0]["date"] if all_transactions else datetime.now(IST),
        transaction_type="OPENING",
        reference="Opening Stock",
        quantity=opening_stock,
        stock_after_transaction=opening_stock,
        details=f"Opening stock balance"
    ))
    
    # Process each transaction and update running balance
    for transaction in all_transactions:
        current_stock += transaction["quantity"] if transaction["type"] == "PURCHASE" else transaction["quantity"]
        
        history.append(ProductStockHistory(
            date=transaction["date"],
            transaction_type=transaction["type"],
            reference=transaction["reference"],
            quantity=transaction["quantity"],
            stock_after_transaction=current_stock,
            details=transaction["details"]
        ))
    
    return ProductStockLedger(
        product_id=product.id,
        product_name=product.name,
        current_stock=product.stock,
        opening_stock=opening_stock,
        total_purchases=sum(p.quantity for p in purchases),
        total_sales=sum(s.quantity for s in sales),
        history=history
    )

# --- 4. PRODUCT LIST for Stock Ledger Selection ---
@app.get("/ledger/products")
def get_products_for_ledger(db: Session = Depends(get_db)):
    """
    Get list of products with basic info for ledger selection.
    """
    products = db.query(Product).all()
    
    product_list = []
    for product in products:
        # Get purchase and sale counts
        purchase_count = db.query(Purchase).filter(Purchase.product_id == product.id).count()
        sale_count = db.query(Sale).filter(Sale.product_id == product.id).count()
        
        product_list.append({
            "product_id": product.id,
            "product_name": product.name,
            "current_stock": product.stock,
            "price": product.selling_price,
            "total_purchases": purchase_count,
            "total_sales": sale_count,
            "has_activity": purchase_count > 0 or sale_count > 0
        })
    
    return product_list

# --- 5. LEDGER SUMMARY DASHBOARD ---
@app.get("/ledger/summary")
def get_ledger_summary(db: Session = Depends(get_db)):
    """
    Get summary dashboard for all ledgers.
    """
    # Total counts
    total_products = db.query(Product).count()
    total_purchases = db.query(Purchase).count()
    total_sales = db.query(Sale).count()

    # Recent activity (last 30 days)
    thirty_days_ago = datetime.now(IST) - timedelta(days=30)

    recent_purchases = db.query(Purchase).filter(Purchase.purchase_date >= thirty_days_ago).count()
    recent_sales = db.query(Sale).filter(Sale.sale_date >= thirty_days_ago).count()

    # Total quantities
    total_purchase_quantity = db.query(Purchase.quantity).all()
    total_purchase_qty = sum([q[0] for q in total_purchase_quantity]) if total_purchase_quantity else 0

    total_sale_quantity = db.query(Sale.quantity).all()
    total_sale_qty = sum([q[0] for q in total_sale_quantity]) if total_sale_quantity else 0

    # Low stock products
    low_stock_products = db.query(Product).filter(Product.stock <= 10).count()

    return {
        "summary": {
            "total_products": total_products,
            "total_purchases": total_purchases,
            "total_sales": total_sales,
            "recent_purchases": recent_purchases,
            "recent_sales": recent_sales,
            "total_purchase_quantity": total_purchase_qty,
            "total_sale_quantity": total_sale_qty,
            "low_stock_products": low_stock_products
        },
        "last_updated": datetime.now(IST)
    }


# --- DOWNLOAD ENDPOINTS FOR EXCEL/CSV EXPORT ---

from fastapi.responses import StreamingResponse


def create_csv_response(data: list, filename: str, fieldnames: list):
    """Helper function to create CSV response from data"""
    if not data:
        # Return empty CSV with headers
        csv_content = io.StringIO()
        writer = csv.DictWriter(csv_content, fieldnames=fieldnames)
        writer.writeheader()
        csv_content.seek(0)
    else:
        # Create CSV from data
        csv_content = io.StringIO()
        if isinstance(data[0], dict):
            writer = csv.DictWriter(csv_content, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        else:
            # Handle list of lists
            writer = csv.writer(csv_content)
            if fieldnames:
                writer.writerow(fieldnames)
            writer.writerows(data)
        csv_content.seek(0)

    return StreamingResponse(
        io.StringIO(csv_content.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/download/sales-ledger")
def download_sales_ledger(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    username: str = Depends(verify_token)
):
    check_permission(Permission.SALES_LEDGER, db, username)
    """
    Download sales ledger as CSV file
    """
    try:
        print(f"🔄 Starting sales ledger download for user: {username}")

        # Simplified approach - just query sales data directly
        query = db.query(Sale).options(joinedload(Sale.product))

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Sale.sale_date >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Sale.sale_date <= end_dt)
        if product_id:
            query = query.filter(Sale.product_id == product_id)

        sales = query.order_by(Sale.sale_date.desc()).all()
        print(f"✅ Found {len(sales)} sales records")

        # Convert to simple CSV format
        csv_data = []
        total_amount = 0
        for sale in sales:
            unit_price = sale.total_amount / sale.quantity if sale.quantity > 0 else 0
            total_amount += sale.total_amount
            csv_data.append({
                "Sale ID": sale.id,
                "Date": sale.sale_date.strftime("%d/%m/%Y %H:%M") if sale.sale_date else "",
                "Product ID": sale.product_id,
                "Product Name": sale.product.name if sale.product else "Unknown",
                "Quantity": sale.quantity,
                "Unit Price (₹)": f"{unit_price:.2f}",
                "Total Amount (₹)": f"{sale.total_amount:.2f}",
                "Customer Info": f"Customer for {sale.product.name if sale.product else 'Unknown'}"
            })

        # Add summary row
        if csv_data:
            csv_data.insert(0, {
                "Sale ID": "SUMMARY",
                "Date": "",
                "Product ID": "",
                "Product Name": f"Total Sales: {len(sales)}",
                "Quantity": "",
                "Unit Price (₹)": "",
                "Total Amount (₹)": f"{total_amount:.2f}",
                "Customer Info": ""
            })

        filename = "sales_ledger.csv"
        fieldnames = ["Sale ID", "Date", "Product ID", "Product Name", "Quantity", "Unit Price (₹)", "Total Amount (₹)", "Customer Info"]

        print(f"🔄 Creating CSV response with {len(csv_data)} rows")
        return create_csv_response(csv_data, filename, fieldnames)

    except Exception as e:
        print(f"❌ ERROR in download_sales_ledger: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating sales ledger CSV: {str(e)}")


@app.get("/download/purchase-ledger")
def download_purchase_ledger(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    username: str = Depends(verify_token)
):
    check_permission(Permission.PURCHASE_LEDGER, db, username)
    """
    Download purchase ledger as CSV file
    """
    try:
        print(f"🔄 Starting purchase ledger download for user: {username}")

        # Simplified approach - just query purchases data directly
        query = db.query(Purchase).options(joinedload(Purchase.product))

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Purchase.purchase_date >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Purchase.purchase_date <= end_dt)
        if product_id:
            query = query.filter(Purchase.product_id == product_id)

        purchases = query.order_by(Purchase.purchase_date.desc()).all()
        print(f"✅ Found {len(purchases)} purchase records")

        # Convert to simple CSV format
        csv_data = []
        total_cost = 0
        for purchase in purchases:
            unit_cost = purchase.total_cost / purchase.quantity if purchase.quantity > 0 else 0
            total_cost += purchase.total_cost
            csv_data.append({
                "Purchase ID": purchase.id,
                "Date": purchase.purchase_date.strftime("%d/%m/%Y %H:%M") if purchase.purchase_date else "",
                "Product ID": purchase.product_id,
                "Product Name": purchase.product.name if purchase.product else "Unknown",
                "Quantity": purchase.quantity,
                "Unit Cost (₹)": f"{unit_cost:.2f}",
                "Total Cost (₹)": f"{purchase.total_cost:.2f}",
                "Supplier Info": f"Supplier for {purchase.product.name if purchase.product else 'Unknown'}"
            })

        # Add summary row
        if csv_data:
            csv_data.insert(0, {
                "Purchase ID": "SUMMARY",
                "Date": "",
                "Product ID": "",
                "Product Name": f"Total Purchases: {len(purchases)}",
                "Quantity": "",
                "Unit Cost (₹)": "",
                "Total Cost (₹)": f"{total_cost:.2f}",
                "Supplier Info": ""
            })

        filename = "purchase_ledger.csv"
        fieldnames = ["Purchase ID", "Date", "Product ID", "Product Name", "Quantity", "Unit Cost (₹)", "Total Cost (₹)", "Supplier Info"]

        print(f"🔄 Creating CSV response with {len(csv_data)} rows")
        return create_csv_response(csv_data, filename, fieldnames)

    except Exception as e:
        print(f"❌ ERROR in download_purchase_ledger: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating purchase ledger CSV: {str(e)}")


@app.get("/download/stock-ledger")
def download_stock_ledger(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    username: str = Depends(verify_token)
):
    check_permission(Permission.STOCK_LEDGER, db, username)
    """
    Download complete product stock ledger as CSV file
    """
    try:
        print(f"🔄 Starting stock ledger download for user: {username}")

        # Simplified approach - just get products without complex stock calculation
        products = db.query(Product).all()
        print(f"✅ Found {len(products)} products in database")

        # Convert to simple CSV format
        csv_data = []
        for product in products:
            csv_data.append({
                "Product ID": product.id,
                "Product Name": product.name,
                "Purchase Price (₹)": f"{product.purchase_price:.2f}",
                "Current Stock": product.stock,
                "Stock Value (₹)": f"{(product.purchase_price * product.stock):.2f}",
                "Unit Type": product.unit_type,
            })

        filename = "product_stock_ledger.csv"
        fieldnames = ["Product ID", "Product Name", "Purchase Price (₹)", "Current Stock", "Stock Value (₹)", "Unit Type"]

        print(f"🔄 Creating CSV response with {len(csv_data)} rows")
        return create_csv_response(csv_data, filename, fieldnames)

    except Exception as e:
        print(f"❌ ERROR in download_stock_ledger: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating stock ledger CSV: {str(e)}")


@app.get("/download/all-products-stock")
def download_all_products_stock(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    username: str = Depends(verify_token)
):
    check_permission(Permission.STOCK_LEDGER, db, username)
    """
    Download all products stock data as CSV file (friendly CSV format for stock management)
    """
    try:
        # Get the same data as the stock snapshot endpoint
        stock_data = get_products_stock_snapshot(date_from=date_from, date_to=date_to, product_id=product_id, db=db)

        # Create a more user-friendly CSV format for stock management
        csv_data = []

        # Add summary row at the top
        total_products = len(stock_data)
        total_stock_quantity = sum(entry.stock for entry in stock_data)
        total_stock_value = sum(entry.stock_value for entry in stock_data)

        csv_data.append({
            "Summary": f"Total Products: {total_products}",
            " ": f"Total Stock Quantity: {total_stock_quantity}",
            "  ": f"Total Stock Value: ₹{total_stock_value:.2f}",
            "   ": "",
            "    ": "",
            "     ": ""
        })

        csv_data.append({})  # Empty row for separation

        # Add product data
        for entry in stock_data:
            # Only include products with stock or that have some activity
            if entry.stock > 0 or total_stock_value > 0:
                # Calculate selling price if we had it, but since we don't, use a reasonable markup
                # For simplicity, we'll just show purchase price and stock value
                csv_data.append({
                    "Product Name": entry.product_name,
                    "Unit Type": entry.unit_type,
                    "Purchase Price (₹)": f"{entry.price:.2f}",
                    "Stock Quantity": entry.stock,
                    "Stock Value (₹)": f"{entry.stock_value:.2f}",
                    "Last Updated": entry.last_updated.strftime("%d/%m/%Y %H:%M") if entry.last_updated else ""
                })

        filename = "all_products_stock.csv"
        fieldnames = ["Product Name", "Unit Type", "Purchase Price (₹)", "Stock Quantity", "Stock Value (₹)", "Last Updated"]

        return create_csv_response(csv_data, filename, fieldnames)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating all products stock CSV: {str(e)}")


def calculate_stock_value_at_date(product_id: int, date_to: Optional[str], db: Session):
    """
    Helper function to calculate stock value for a product at a specific date
    Returns the stock value at that date using purchase price
    """
    if not date_to:
        # If no date specified, return current stock value
        product = db.query(Product).filter(Product.id == product_id).first()
        return product.purchase_price * product.stock if product else 0

    try:
        # Parse the date
        date_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00')).replace(tzinfo=IST) + timedelta(days=1)
        filter_date_to = date_dt

        # Get product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return 0

        # Default to current stock
        calculated_stock = product.stock

        # Calculate stock as of the filter date
        purchases = db.query(Purchase).filter(
            Purchase.product_id == product.id,
            Purchase.purchase_date < filter_date_to
        ).all()

        sales = db.query(Sale).filter(
            Sale.product_id == product.id,
            Sale.sale_date < filter_date_to
        ).all()

        total_purchases_up_to_date = sum(p.quantity for p in purchases)
        total_sales_up_to_date = sum(s.quantity for s in sales)

        # Calculate opening stock and then add purchases - sales up to date
        all_purchases_ever = db.query(Purchase).filter(Purchase.product_id == product.id).all()
        all_sales_ever = db.query(Sale).filter(Sale.product_id == product.id).all()
        total_purchases_ever = sum(p.quantity for p in all_purchases_ever)
        total_sales_ever = sum(s.quantity for s in all_sales_ever)

        opening_stock = product.stock + total_sales_ever - total_purchases_ever
        calculated_stock = opening_stock + total_purchases_up_to_date - total_sales_up_to_date

        return product.purchase_price * calculated_stock

    except Exception as e:
        print(f"❌ Error calculating stock value at date: {str(e)}")
        return 0


@app.get("/download/profit-loss")
def download_profit_loss(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    username: str = Depends(verify_token)
):
    check_permission(Permission.PROFIT_LOSS, db, username)
    """
    Download profit & loss analysis as CSV file matching the frontend table format
    """
    try:
        print(f"🔄 Starting profit-loss download for user: {username}")

        # Use the same logic as get_profit_loss_data to ensure consistent results
        # Fetch sales and purchase data with filters
        sales_query = db.query(Sale)
        purchases_query = db.query(Purchase)
        products_query = db.query(Product)

        # Apply date filters
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')).replace(tzinfo=IST)
            sales_query = sales_query.filter(Sale.sale_date >= start_dt)
            purchases_query = purchases_query.filter(Purchase.purchase_date >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')).replace(tzinfo=IST) + timedelta(days=1)
            sales_query = sales_query.filter(Sale.sale_date < end_dt)
            purchases_query = purchases_query.filter(Purchase.purchase_date < end_dt)

        # Apply product filter
        if product_id:
            sales_query = sales_query.filter(Sale.product_id == product_id)
            purchases_query = purchases_query.filter(Purchase.product_id == product_id)
            products_query = products_query.filter(Product.id == product_id)

        sales = sales_query.all()
        purchases = purchases_query.all()
        products = products_query.all()

        # Group data by product (same logic as frontend)
        product_analysis = []

        for product in products:
            # Filter sales and purchases for this product
            product_sales = [s for s in sales if s.product_id == product.id]
            product_purchases = [p for p in purchases if p.product_id == product.id]

            # Get opening stock value using helper function
            opening_stock_value = calculate_stock_value_at_date(product.id, start_date, db) if start_date else 0

            # Get closing stock value
            closing_stock_value = calculate_stock_value_at_date(product.id, end_date, db)

            # Calculate totals
            total_sales_amount = sum(s.total_amount for s in product_sales)
            total_purchase_cost = sum(p.total_cost for p in product_purchases)
            units_sold = sum(s.quantity for s in product_sales)

            # Calculate profit/loss: Sales - (Purchases - Opening Stock + Closing Stock)
            gross_profit = total_sales_amount - total_purchase_cost + closing_stock_value
            margin = f"{(gross_profit / total_sales_amount * 100):.2f}%" if total_sales_amount > 0 else "0.00%"

            product_analysis.append({
                "Product": product.name,
                "Units Sold": units_sold,
                "Opening Stock (₹)": f"{opening_stock_value:.2f}",
                "Purchase (₹)": f"{total_purchase_cost:.2f}",
                "Sales (₹)": f"{total_sales_amount:.2f}",
                "Closing Stock (₹)": f"{closing_stock_value:.2f}",
                "Gross Profit (₹)": f"{gross_profit:.2f}",
                "Margin (%)": margin
            })

        # Calculate totals
        total_units_sold = sum(row["Units Sold"] for row in product_analysis)
        total_opening = sum(float(row["Opening Stock (₹)"]) for row in product_analysis)
        total_purchases = sum(float(row["Purchase (₹)"]) for row in product_analysis)
        total_sales = sum(float(row["Sales (₹)"]) for row in product_analysis)
        total_closing = sum(float(row["Closing Stock (₹)"]) for row in product_analysis)
        total_profit = sum(float(row["Gross Profit (₹)"]) for row in product_analysis)
        overall_margin = f"{(total_profit / total_sales * 100):.2f}%" if total_sales > 0 else "0.00%"

        # Prepare CSV data
        csv_data = product_analysis.copy()

        # Add summary row at the end (same as frontend footer)
        csv_data.append({
            "Product": "Total:",
            "Units Sold": total_units_sold,
            "Opening Stock (₹)": f"{total_opening:.2f}",
            "Purchase (₹)": f"{total_purchases:.2f}",
            "Sales (₹)": f"{total_sales:.2f}",
            "Closing Stock (₹)": f"{total_closing:.2f}",
            "Gross Profit (₹)": f"{total_profit:.2f}",
            "Margin (%)": overall_margin
        })

        filename = "profit_loss_analysis.csv"
        fieldnames = ["Product", "Units Sold", "Opening Stock (₹)", "Purchase (₹)", "Sales (₹)", "Closing Stock (₹)", "Gross Profit (₹)", "Margin (%)"]

        print(f"🔄 Creating CSV response with {len(csv_data)} rows")
        return create_csv_response(csv_data, filename, fieldnames)

    except Exception as e:
        print(f"❌ ERROR in download_profit_loss: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating profit & loss CSV: {str(e)}")


# --- CATEGORY MANAGEMENT ENDPOINTS ---

class CategoryCreate(BaseModel):
    name: str = Field(..., description="Category name")

class CategoryResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

@app.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    categories = db.query(Category).all()
    return categories

@app.post("/categories/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    username: str = Depends(verify_token)
):
    """Create a new category"""
    check_permission(Permission.CREATE_CATEGORY, db, username)

    # Check if category already exists
    existing_category = db.query(Category).filter(Category.name.ilike(category.name)).first()
    if existing_category:
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    new_category = Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@app.delete("/categories/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    username: str = Depends(verify_token)
):
    """Delete a category if it's not being used by any products and renumber remaining categories"""
    check_permission(Permission.DELETE_CATEGORY, db, username)

    try:
        # Check if category exists
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        # Check if any products use this category
        products_using_category = db.query(Product).filter(Product.category.ilike(category.name)).count()
        if products_using_category > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete category '{category.name}' because it is used by {products_using_category} product(s)"
            )

        # Get category name for response
        category_name = category.name

        # Delete the category
        db.delete(category)
        db.flush()  # Don't commit yet, we need to renumber

        # Renumber all categories with ID > deleted category ID
        categories_to_renumber = db.query(Category).filter(Category.id > category_id).order_by(Category.id).all()

        for cat in categories_to_renumber:
            old_id = cat.id
            new_id = old_id - 1
            # Update category ID
            db.execute(text("UPDATE categories SET id = :new_id WHERE id = :old_id"), {"new_id": new_id, "old_id": old_id})

        # Reset the autoincrement sequence to continue from max_id + 1
        max_id = db.query(Category.id).order_by(Category.id.desc()).first()
        if max_id:
            # For SQLite: reset autoincrement sequence
            if USE_SQLITE:
                db.execute(text("DELETE FROM sqlite_sequence WHERE name='categories'"))
                db.execute(text("INSERT INTO sqlite_sequence (name, seq) VALUES ('categories', :max_id)"), {"max_id": max_id[0]})
            else:
                # For PostgreSQL: alter sequence
                db.execute(text("SELECT setval('categories_id_seq', :max_id)"), {"max_id": max_id[0]})

        # Commit all changes
        db.commit()

        return {
            "status": "success",
            "message": f"Category '{category_name}' deleted successfully. Categories have been renumbered and sequence reset to maintain continuous IDs.",
            "category_id": category_id,
            "renumbered_categories": len(categories_to_renumber)
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting category {category_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting category: {str(e)}")

# --- SMS Endpoint ---
@app.post("/sms")
async def incoming_sms(request: Request):
    """Handles an incoming message from Twilio and sends a reply."""
    try:
        form_data: Dict[str, Any] = await request.form()
        incoming_message = form_data.get('Body', '').lower()
        from_number = form_data.get('From', '')

        print(f"Received message from {from_number}: '{incoming_message}'")

        resp = MessagingResponse()
        
        reply_message = None
        for product_name, price in PRODUCTS_DB.items():
            if product_name in incoming_message:
                reply_message = f"The price for {product_name.capitalize()} is ₹{price:.2f}."
                break
        
        if reply_message is None:
            reply_message = "Thank you for your message! Please visit our online store to place an order."

        resp.message(reply_message)
        return JSONResponse(content=str(resp), media_type="text/xml")

    except Exception as e:
        print(f"An error occurred: {e}")
        resp = MessagingResponse()
        resp.message("Sorry, something went wrong. Please try again later.")
        return JSONResponse(content=str(resp), media_type="text/xml")

# === SEEDING ENDPOINT FOR DEMO ===
@app.post("/seed")
async def seed_products(db: Session = Depends(get_db)):
    """
    Seed the database with sample products - temporary for demo purposes
    """
    try:
        # Check if products already exist
        product_count = db.query(Product).count()
        if product_count > 0:
            return {"message": f"Database already has {product_count} products. No seeding needed."}

        # Create categories first
        categories = ["Fruits", "Vegetables", "Dairy", "Bakery", "Groceries", "Beverages", "Snacks", "Meat & Fish"]
        for cat_name in categories:
            if not db.query(Category).filter(Category.name.ilike(cat_name)).first():
                db.add(Category(name=cat_name))

        # Create customer user for customer sales
        customer_user_exists = db.query(User).filter(User.username == "customer").first()
        if not customer_user_exists:
            hashed = bcrypt.hashpw("customer".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            customer_user = User(
                username="customer",
                email="customer@kirana.store",
                password_hash=hashed,
                sales=False,
                purchase=False,
                create_product=False,
                delete_product=False,
                create_category=False,
                delete_category=False,
                sales_ledger=False,
                purchase_ledger=False,
                stock_ledger=False,
                profit_loss=False,
                opening_stock=False,
                user_management=False
            )
            db.add(customer_user)
            db.flush()

        # Sample products
        sample_products = [
            Product(name="Apple", purchase_price=80.00, selling_price=100.00, unit_type="kgs", category="Fruits", stock=50),
            Product(name="Banana", purchase_price=40.00, selling_price=50.00, unit_type="kgs", category="Fruits", stock=30),
            Product(name="Orange", purchase_price=60.00, selling_price=80.00, unit_type="kgs", category="Fruits", stock=25),
            Product(name="Milk", purchase_price=50.00, selling_price=65.00, unit_type="ltr", category="Dairy", stock=20),
            Product(name="Bread", purchase_price=30.00, selling_price=40.00, unit_type="pcs", category="Bakery", stock=15),
            Product(name="Eggs", purchase_price=70.00, selling_price=90.00, unit_type="pcs", category="Meat & Fish", stock=40),
            Product(name="Rice", purchase_price=100.00, selling_price=120.00, unit_type="kgs", category="Groceries", stock=60),
            Product(name="Sugar", purchase_price=45.00, selling_price=55.00, unit_type="kgs", category="Groceries", stock=35),
        ]
        db.add_all(sample_products)
        db.commit()

        return {"message": f"Seeded database with {len(sample_products)} products and {len(categories)} categories."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Seeding error: {str(e)}")

# --- Health Check Endpoints ---
@app.get("/")
async def root():
    return {
        "message": "Kirana Store API is running",
        "status": "active",
        "timestamp": datetime.now(IST).isoformat()
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(IST).isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

# --- DEBUG ENDPOINT REMOVED ---
# --- USER AUTHENTICATION ENDPOINTS ---

@app.post("/auth/register", response_model=UserResponse)
async def register_user(
    user_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user (public endpoint, creates users with EMPLOYEE role by default)
    """
    try:
        # Extract data from request
        username = user_data.username
        password = user_data.password
        email = username + "@example.com"  # Generate email from username since LoginRequest doesn't have email

        # Validate input
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password are required")

        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")

        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            if existing_user.username == username:
                raise HTTPException(status_code=400, detail="Username already exists")
            else:
                raise HTTPException(status_code=400, detail="Email already exists")

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create new user with basic permissions for public registration
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password.decode('utf-8'),
            # Basic permissions for new users - can be modified by admin later
            sales=True,
            purchase=True,
            create_product=False,
            delete_product=False,
            sales_ledger=False,
            purchase_ledger=False,
            stock_ledger=False,
            profit_loss=False,
            opening_stock=False,
            user_management=False,
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Return response with permissions
        permissions = [
            k for k, v in {
                "sales": new_user.sales,
                "purchase": new_user.purchase,
                "create_product": new_user.create_product,
                "delete_product": new_user.delete_product,
                "create_category": new_user.create_category,
                "delete_category": new_user.delete_category,
                "sales_ledger": new_user.sales_ledger,
                "purchase_ledger": new_user.purchase_ledger,
                "stock_ledger": new_user.stock_ledger,
                "profit_loss": new_user.profit_loss,
                "opening_stock": new_user.opening_stock,
                "user_management": new_user.user_management,
            }.items() if v
        ]

        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            is_active=new_user.is_active,
            permissions=permissions
        )
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate user using ORM with backwards compatibility."""
    try:
        # Query the user using ORM
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"⚠️ User '{username}' not found")
            return None

        # Get the stored password
        stored_password = user.password_hash
        if not stored_password:
            print(f"⚠️ User '{username}' has no password set")
            return None

        # Try bcrypt verification first (for modern hashed passwords)
        try:
            # stored_password is already a string (decoded), so we need to encode it back to bytes
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                print(f"✅ Authenticated '{username}' with bcrypt hash")
                return user
        except (ValueError, TypeError) as e:
            print(f"⚠️ bcrypt verification failed: {e}")
            # If bcrypt verification fails, it might be plain text (legacy support)
            pass

        # Check if it's plain text (for legacy users)
        if stored_password == password:
            print(f"✅ Authenticated '{username}' with plain text password")
            return user

        print(f"⚠️ Invalid password for user '{username}'")
        return None

    except Exception as e:
        print(f"❌ Authentication error for user '{username}': {str(e)}")
        import traceback
        traceback.print_exc()
        return None

@app.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token
    """
    try:
        user = authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Special handling for admin user "raza123" - ensure they have all permissions
        if user.username == "raza123":
            # Check if admin user has all permissions, if not, grant them
            if not (user.sales and user.purchase and user.create_product and user.delete_product and
                    user.create_category and user.delete_category and
                    user.sales_ledger and user.purchase_ledger and user.stock_ledger and
                    user.profit_loss and user.opening_stock and user.user_management):
                print(f"🔧 Granting all admin permissions to user {user.username}")
                user.sales = True
                user.purchase = True
                user.create_product = True
                user.delete_product = True
                user.create_category = True
                user.delete_category = True
                user.sales_ledger = True
                user.purchase_ledger = True
                user.stock_ledger = True
                user.profit_loss = True
                user.opening_stock = True
                user.user_management = True
                db.commit()
                print(f"✅ Admin permissions granted successfully to {user.username}")

        # Skip last login update to avoid database schema issues
        # user.last_login = datetime.now(IST)
        # db.commit()

        # Create access token
        access_token = create_access_token({"sub": user.username})

        # Get permissions safely - new system only
        permissions = [
            k for k, v in {
                "sales": user.sales,
                "purchase": user.purchase,
                "create_product": user.create_product,
                "delete_product": user.delete_product,
                "create_category": user.create_category,
                "delete_category": user.delete_category,
                "sales_ledger": user.sales_ledger,
                "purchase_ledger": user.purchase_ledger,
                "stock_ledger": user.stock_ledger,
                "profit_loss": user.profit_loss,
                "opening_stock": user.opening_stock,
                "user_management": user.user_management,
            }.items() if v
        ]

        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            permissions=permissions
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error but return a generic message
        print(f"Login error for user {login_data.username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during login")

# Authentication functions

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user(username: str = Depends(verify_token), db: Session = Depends(get_db)):
    """
    Get current authenticated user information
    """
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get permissions safely - new system only
        permissions = [
            k for k, v in {
                "sales": user.sales,
                "purchase": user.purchase,
                "create_product": user.create_product,
                "delete_product": user.delete_product,
                "create_category": user.create_category,
                "delete_category": user.delete_category,
                "sales_ledger": user.sales_ledger,
                "purchase_ledger": user.purchase_ledger,
                "stock_ledger": user.stock_ledger,
                "profit_loss": user.profit_loss,
                "opening_stock": user.opening_stock,
                "user_management": user.user_management,
            }.items() if v
        ]

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            permissions=permissions
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Logout endpoint - clears the token client-side, server-side just returns success
@app.post("/auth/logout")
async def logout(username: str = Depends(verify_token)):
    """
    Logout endpoint - returns success message for client-side token removal
    """
    return {"message": "Logged out successfully"}

@app.get("/auth/protected")
async def protected_route(username: str = Depends(verify_token)):
    """
    Example protected route that requires authentication
    """
    return {"message": f"Hello {username}, you are authenticated!"}

# --- USER MANAGEMENT ENDPOINTS (Admin Only) ---

@app.get("/users", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db), username: str = Depends(verify_token)):
    """
    Get all users (Admin only or user with user_management permission)
    """
    try:
        # Check permissions
        check_permission(Permission.USER_MANAGEMENT, db, username)

        users = db.query(User).all()
        user_responses = []
        for u in users:
            # Use permissions-based system (all users have permissions now)
            permissions = [
                k for k, v in {
                    "sales": u.sales,
                    "purchase": u.purchase,
                    "create_product": u.create_product,
                    "delete_product": u.delete_product,
                    "create_category": u.create_category,
                    "delete_category": u.delete_category,
                    "sales_ledger": u.sales_ledger,
                    "purchase_ledger": u.purchase_ledger,
                    "stock_ledger": u.stock_ledger,
                    "profit_loss": u.profit_loss,
                    "opening_stock": u.opening_stock,
                    "user_management": u.user_management,
                }.items() if v
            ]
            user_responses.append(UserResponse(
                id=u.id,
                username=u.username,
                email=u.email,
                is_active=u.is_active,
                permissions=permissions
            ))

        return user_responses
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_token)
):
    """
    Create a new user with individual permissions
    """
    try:
        # Check permissions
        check_permission(Permission.USER_MANAGEMENT, db, current_user)

        # Check if username already exists
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Check if email already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")

        # Hash password
        hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())

        # Create new user with individual permissions
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password.decode('utf-8'),
            sales=user_data.sales,
            purchase=user_data.purchase,
            create_product=user_data.create_product,
            delete_product=user_data.delete_product,
            create_category=user_data.create_category,
            delete_category=user_data.delete_category,
            sales_ledger=user_data.sales_ledger,
            purchase_ledger=user_data.purchase_ledger,
            stock_ledger=user_data.stock_ledger,
            profit_loss=user_data.profit_loss,
            opening_stock=user_data.opening_stock,
            user_management=user_data.user_management,
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Return response with permissions
        permissions = [
            k for k, v in {
                "sales": new_user.sales,
                "purchase": new_user.purchase,
                "create_product": new_user.create_product,
                "delete_product": new_user.delete_product,
                "sales_ledger": new_user.sales_ledger,
                "purchase_ledger": new_user.purchase_ledger,
                "stock_ledger": new_user.stock_ledger,
                "profit_loss": new_user.profit_loss,
                "opening_stock": new_user.opening_stock,
                "user_management": new_user.user_management,
            }.items() if v
        ]

        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            is_active=new_user.is_active,
            permissions=permissions
        )
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

class UserUpdateRequest(BaseModel):
    sales: Optional[bool] = None
    purchase: Optional[bool] = None
    create_product: Optional[bool] = None
    delete_product: Optional[bool] = None
    create_category: Optional[bool] = None
    delete_category: Optional[bool] = None
    sales_ledger: Optional[bool] = None
    purchase_ledger: Optional[bool] = None
    stock_ledger: Optional[bool] = None
    profit_loss: Optional[bool] = None
    opening_stock: Optional[bool] = None
    user_management: Optional[bool] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    email: Optional[str] = None

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_token)
):
    """
    Update user permissions and details
    """
    try:
        # Check permissions
        check_permission(Permission.USER_MANAGEMENT, db, current_user)

        # Find the user to update
        user_to_update = db.query(User).filter(User.id == user_id).first()
        if not user_to_update:
            raise HTTPException(status_code=404, detail="User not found")

        # Update permissions and other fields
        for field in user_data.__fields__:
            value = getattr(user_data, field)
            if value is not None:
                if field == "password" and value:
                    # Hash new password
                    hashed_password = bcrypt.hashpw(value.encode('utf-8'), bcrypt.gensalt())
                    setattr(user_to_update, "password_hash", hashed_password.decode('utf-8'))
                elif field != "password":  # Don't set password directly
                    setattr(user_to_update, field, value)

        db.commit()
        db.refresh(user_to_update)

        # Return response with updated permissions
        permissions = [
            k for k, v in {
                "sales": user_to_update.sales,
                "purchase": user_to_update.purchase,
                "create_product": user_to_update.create_product,
                "delete_product": user_to_update.delete_product,
                "sales_ledger": user_to_update.sales_ledger,
                "purchase_ledger": user_to_update.purchase_ledger,
                "stock_ledger": user_to_update.stock_ledger,
                "profit_loss": user_to_update.profit_loss,
                "opening_stock": user_to_update.opening_stock,
                "user_management": user_to_update.user_management,
            }.items() if v
        ]

        return UserResponse(
            id=user_to_update.id,
            username=user_to_update.username,
            email=user_to_update.email,
            is_active=user_to_update.is_active,
            permissions=permissions
        )
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_token)
):
    """
    Delete a user
    """
    try:
        # Check permissions
        check_permission(Permission.USER_MANAGEMENT, db, current_user)

        # Find the user to delete
        user_to_delete = db.query(User).filter(User.id == user_id).first()
        if not user_to_delete:
            raise HTTPException(status_code=404, detail="User not found")

        # Prevent deleting self
        current_user_obj = db.query(User).filter(User.username == current_user).first()
        if current_user_obj and current_user_obj.id == user_id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")

        db.delete(user_to_delete)
        db.commit()

        return {"status": "success", "message": f"User {user_to_delete.username} deleted successfully"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/auth/permissions")
def get_user_permissions(username: str = Depends(verify_token), db: Session = Depends(get_db)):
    """
    Get current user's permissions and accessible features
    """
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if user has individual permissions (new system) or fallback to roles (legacy)
        if hasattr(user, 'sales') and user.sales is not None:
            # User has individual permissions
            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active
                },
                "permissions": [
                    k for k, v in {
                        "sales": user.sales,
                        "purchase": user.purchase,
                        "create_product": user.create_product,
                        "delete_product": user.delete_product,
                        "sales_ledger": user.sales_ledger,
                        "purchase_ledger": user.purchase_ledger,
                        "stock_ledger": user.stock_ledger,
                        "profit_loss": user.profit_loss,
                        "opening_stock": user.opening_stock,
                        "user_management": user.user_management,
                    }.items() if v
                ],
                "accessible_features": {
                    "sales": user.sales,
                    "purchase": user.purchase,
                    "create_product": user.create_product,
                    "delete_product": user.delete_product,
                    "sales_ledger": user.sales_ledger,
                    "purchase_ledger": user.purchase_ledger,
                    "stock_ledger": user.stock_ledger,
                    "profit_loss": user.profit_loss,
                    "opening_stock": user.opening_stock,
                    "user_management": user.user_management,
                }
            }
        else:
            # Fallback to role-based permissions (legacy users)
            user_permissions = ROLE_PERMISSIONS.get(user.role.value, [])

            # Convert Permission enum to string values
            permissions = [perm.value for perm in user_permissions]

            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.value,
                    "is_active": user.is_active
                },
                "permissions": permissions,
                "accessible_features": {
                    "sales": Permission.SALES.value in permissions,
                    "purchase": Permission.PURCHASE.value in permissions,
                    "create_product": Permission.CREATE_PRODUCT.value in permissions,
                    "delete_product": Permission.DELETE_PRODUCT.value in permissions,
                    "sales_ledger": Permission.SALES_LEDGER.value in permissions,
                    "purchase_ledger": Permission.PURCHASE_LEDGER.value in permissions,
                    "stock_ledger": Permission.STOCK_LEDGER.value in permissions,
                    "profit_loss": Permission.PROFIT_LOSS.value in permissions,
                    "opening_stock": Permission.OPENING_STOCK.value in permissions,
                    "user_management": Permission.USER_MANAGEMENT.value in permissions,
                }
            }
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Permission-protected endpoint getters
def check_permission(required_permission: Permission, db: Session, username: str):
    """Helper function to check if user has required permission"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user has individual permissions (new system) or fallback to roles (legacy)
    if hasattr(user, 'sales') and user.sales is not None:
        # Check individual permission
        perm_attr = required_permission.value
        if not getattr(user, perm_attr, False):
            raise HTTPException(status_code=403, detail=f"Permission required: {required_permission.value}")
    else:
        # Fallback to role-based permissions
        user_permissions = ROLE_PERMISSIONS.get(user.role.value, [])
        if required_permission not in user_permissions:
            raise HTTPException(status_code=403, detail=f"Authentication required for {required_permission.value}")

@app.get("/protected/sales")
def protected_sales_endpoint(db: Session = Depends(get_db), username: str = Depends(verify_token)):
    """Protected sales endpoint - requires SALES permission"""
    check_permission(Permission.SALES, db, username)
    return {"message": "Sales access granted"}

@app.get("/protected/purchase")
def protected_purchase_endpoint(db: Session = Depends(get_db), username: str = Depends(verify_token)):
    """Protected purchase endpoint - requires PURCHASE permission"""
    check_permission(Permission.PURCHASE, db, username)
    return {"message": "Purchase access granted"}

@app.get("/protected/create-product")
def protected_create_product_endpoint(db: Session = Depends(get_db), username: str = Depends(verify_token)):
    """Protected create product endpoint - requires CREATE_PRODUCT permission"""
    check_permission(Permission.CREATE_PRODUCT, db, username)
    return {"message": "Create product access granted"}

@app.get("/protected/delete-product")
def protected_delete_product_endpoint(db: Session = Depends(get_db), username: str = Depends(verify_token)):
    """Protected delete product endpoint - requires DELETE_PRODUCT permission"""
    check_permission(Permission.DELETE_PRODUCT, db, username)
    return {"message": "Delete product access granted"}

# Add permission checks to existing endpoints
@app.post("/products/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db), username: str = Depends(verify_token)):
    check_permission(Permission.CREATE_PRODUCT, db, username)
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: int, db: Session = Depends(get_db), username: str = Depends(verify_token)):
    """Delete a product and all its associated sales and purchase records."""
    check_permission(Permission.DELETE_PRODUCT, db, username)
    # ... existing code ...

@app.post("/sales/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def record_sale(sale: SaleCreate, db: Session = Depends(get_db), username: str = Depends(verify_token)):
    check_permission(Permission.SALES, db, username)
    # ... existing code ...

@app.post("/purchases/", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
def record_purchase(purchase: PurchaseCreate, db: Session = Depends(get_db), username: str = Depends(verify_token)):
    check_permission(Permission.PURCHASE, db, username)
    # ... existing code ...

# Protected ledger endpoints
@app.get("/ledger/sales", response_model=List[SalesLedgerEntry])
def get_sales_ledger(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    username: str = Depends(verify_token)
):
    check_permission(Permission.SALES_LEDGER, db, username)
    # ... existing code here ....

@app.get("/ledger/purchases", response_model=List[PurchaseLedgerEntry])
def get_purchase_ledger(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    username: str = Depends(verify_token)
):
    check_permission(Permission.PURCHASE_LEDGER, db, username)
    # ... existing code ...

@app.get("/products/stock-snapshot", response_model=List[ProductStockSnapshot])
def get_products_stock_snapshot(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    username: str = Depends(verify_token)
):
    check_permission(Permission.STOCK_LEDGER, db, username)
    # ... existing code ...

@app.get("/profit-loss-data")
def get_profit_loss_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    product_id: Optional[int] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    username: str = Depends(verify_token)
):
    check_permission(Permission.PROFIT_LOSS, db, username)
    """
    Get complete profit & loss analysis with date/product/category filters.
    Calculates profit/loss based on sales vs purchases + opening/closing stock adjustments.
    """
    try:
        # Fetch sales and purchase data with filters
        sales_query = db.query(Sale)
        purchases_query = db.query(Purchase)
        products_query = db.query(Product)

        # Apply date filters
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')).replace(tzinfo=IST)
            sales_query = sales_query.filter(Sale.sale_date >= start_dt)
            purchases_query = purchases_query.filter(Purchase.purchase_date >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')).replace(tzinfo=IST) + timedelta(days=1)
            sales_query = sales_query.filter(Sale.sale_date < end_dt)
            purchases_query = purchases_query.filter(Purchase.purchase_date < end_dt)

        # Apply product filter
        if product_id:
            sales_query = sales_query.filter(Sale.product_id == product_id)
            purchases_query = purchases_query.filter(Purchase.product_id == product_id)
            products_query = products_query.filter(Product.id == product_id)

        # Apply category filter
        if category:
            sales_query = sales_query.filter(Sale.product.has(Product.category.ilike(category)))
            purchases_query = purchases_query.filter(Purchase.product.has(Product.category.ilike(category)))
            products_query = products_query.filter(Product.category.ilike(category))

        sales = sales_query.all()
        purchases = purchases_query.all()
        products = products_query.all()

        # Get opening stock register for opening stock values
        # For P&L calculation, use date-based opening stock if start_date is provided
        # If no start_date, use 0 as opening stock (beginning of business)
        if start_date:
            opening_stock_data = get_products_stock_snapshot(date_to=start_date, product_id=product_id, db=db)
        else:
            opening_stock_data = []  # Empty means opening stock is 0 for all products

        # Get closing stock snapshot
        closing_stock_data = get_products_stock_snapshot(date_to=end_date, product_id=product_id, db=db)

        # Group data by product
        product_analysis = []

        for product in products:
            # Filter sales and purchases for this product
            product_sales = [s for s in sales if s.product_id == product.id]
            product_purchases = [p for p in purchases if p.product_id == product.id]

            # Get opening stock
            opening_entry = next((os for os in opening_stock_data if os.product_id == product.id), None)
            opening_stock_value = (opening_entry.stock * product.purchase_price) if opening_entry else 0

            # Get closing stock
            closing_entry = next((cs for cs in closing_stock_data if cs.product_id == product.id), None)
            closing_stock_value = closing_entry.stock_value if closing_entry else 0

            # Calculate totals
            total_sales_amount = sum(s.total_amount for s in product_sales)
            total_purchase_cost = sum(p.total_cost for p in product_purchases)
            units_sold = sum(s.quantity for s in product_sales)

            # Calculate profit/loss: Sales - (Purchases - Opening Stock + Closing Stock) [since Opening Stock is part of purchase value]
            gross_profit = total_sales_amount - total_purchase_cost + closing_stock_value
            margin = f"{(gross_profit / total_sales_amount * 100):.2f}%" if total_sales_amount > 0 else "0.00%"

            product_analysis.append({
                "Product ID": product.id,
                "Product Name": product.name,
                "Units Sold": units_sold,
                "Opening Stock Value (₹)": f"{opening_stock_value:.2f}",
                "Purchase Cost (₹)": f"{total_purchase_cost:.2f}",
                "Sales Amount (₹)": f"{total_sales_amount:.2f}",
                "Closing Stock Value (₹)": f"{closing_stock_value:.2f}",
                "Gross Profit (₹)": f"{gross_profit:.2f}",
                "Profit Margin (%)": margin
            })

        # Calculate totals
        total_opening = sum(float(p["Opening Stock Value (₹)"]) for p in product_analysis)
        total_purchases = sum(float(p["Purchase Cost (₹)"]) for p in product_analysis)
        total_sales = sum(float(p["Sales Amount (₹)"]) for p in product_analysis)
        total_closing = sum(float(p["Closing Stock Value (₹)"]) for p in product_analysis)
        total_profit = sum(float(p["Gross Profit (₹)"]) for p in product_analysis)

        # Add total row
        product_analysis.append({
            "Product ID": "TOTAL",
            "Product Name": "ALL PRODUCTS",
            "Units Sold": "",
            "Opening Stock Value (₹)": f"{total_opening:.2f}",
            "Purchase Cost (₹)": f"{total_purchases:.2f}",
            "Sales Amount (₹)": f"{total_sales:.2f}",
            "Closing Stock Value (₹)": f"{total_closing:.2f}",
            "Gross Profit (₹)": f"{total_profit:.2f}",
            "Profit Margin (%)": f"{(total_profit / total_sales * 100):.2f}%" if total_sales > 0 else "0.00%"
        })

        return product_analysis

    except Exception as e:
        print(f"❌ Error generating profit & loss data: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating profit & loss data: {str(e)}")



@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_token)
):
    check_permission(Permission.USER_MANAGEMENT, db, current_user)
    return create_user(UserCreateRequest(username=username, password=password, email=email, sales=True, purchase=True), db, current_user)

@app.get("/users", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db), username: str = Depends(verify_token)):
    check_permission(Permission.USER_MANAGEMENT, db, username)
    # ... existing code ...

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
