"""Database connection management using SQLAlchemy."""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,
    max_overflow=10
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Get a database session."""
    session = SessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise


def test_connection():
    """Test the database connection."""
    try:
        session = get_db_session()
        result = session.execute(text("SELECT 1"))
        row = result.fetchone()
        session.close()
        return row[0] == 1
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False