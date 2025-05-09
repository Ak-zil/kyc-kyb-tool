"""
Database session management.
Creates and manages SQLAlchemy sessions for database interactions.
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Log the database URI (without password)
db_uri = str(settings.SQLALCHEMY_DATABASE_URI)
safe_db_uri = db_uri.replace(settings.POSTGRES_PASSWORD, "********")
logger.info(f"Connecting to database: {safe_db_uri}")

# Create SQLAlchemy engine with connection pool
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),  # Convert to string explicitly
    pool_pre_ping=True,  # Test connections before using them
    pool_size=10,        # Connection pool size
    max_overflow=20,     # Maximum overflow connections
    pool_recycle=3600,   # Recycle connections after 1 hour
    connect_args={"connect_timeout": 10},  # Connection timeout in seconds
)

# Create session factory for SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get a database session
def get_db():
    """
    Dependency function that provides a SQLAlchemy session.
    Creates a new SQLAlchemy session and automatically closes it after use.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()