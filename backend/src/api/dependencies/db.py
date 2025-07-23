from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Iterator, Generator

from src.api.core.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create schema-specific metadata
metadata = MetaData(schema=settings.DATABASE_SCHEMA)

# Base class for models with schema-specific metadata
Base = declarative_base(metadata=metadata)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting DB session.
    
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def get_db_session() -> Iterator[Session]:
    """
    Get a DB session for use in background tasks.
    
    Returns:
        Iterator[Session]: Database session iterator
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()