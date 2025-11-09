"""Database management for licensing system."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, License, OpenAIKey, ScripMaster, ValidationLog
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "./licensing.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Initialize database and create tables."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")

def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session() -> Session:
    """Get database session (for non-FastAPI usage)."""
    return SessionLocal()
