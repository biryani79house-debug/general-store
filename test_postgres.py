from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Connecting to: {DATABASE_URL}")

if not DATABASE_URL:
    print("DATABASE_URL not set")
    exit()

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()
try:
    result = db.execute(text("SELECT * FROM users LIMIT 10"))
    users = result.fetchall()
    print("Users in database:")
    for user in users:
        print(user)
except Exception as e:
    print(f"Error: {e}")

try:
    result = db.execute(text("SELECT username, password_hash FROM users WHERE username = 'raza123'"))
    user = result.fetchone()
    if user:
        print(f"User {user[0]} password hash: {user[1]}")
    else:
        print("No user 'raza123' found")
except Exception as e:
    print(f"Error querying user: {e}")

db.close()
