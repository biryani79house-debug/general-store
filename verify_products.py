import os
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base, sessionmaker
import sqlalchemy as sa

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = sa.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

try:
    # Check current products
    products = db.execute(sa.text("SELECT id, name, stock FROM products ORDER BY id")).fetchall()
    print("Current products:")
    for product in products:
        print(f"ID: {product[0]}, Name: {product[1]}, Stock: {product[2]}")

    # Check sequence
    seq_result = db.execute(sa.text("SELECT last_value FROM products_id_seq")).scalar()
    print(f"Current sequence value: {seq_result}")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
