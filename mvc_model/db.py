# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
DB_BACKEND = os.getenv("DB_BACKEND", "sqlite")
if DB_BACKEND == "postgres":
    DATABASE_URL = "postgresql://user:pass@localhost/predictions"
else:
    DATABASE_URL = "sqlite:///./invoices.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()