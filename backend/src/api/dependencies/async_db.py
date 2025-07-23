"""
Async database dependencies and setup.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from src.api.core.config import get_settings

settings = get_settings()

# Create async SQLAlchemy engine
# Convert PostgreSQL URL from postgresql:// to postgresql+asyncpg://
ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    future=True,
    echo=False,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async DB session.
    
    Yields:
        AsyncSession: Async database session
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()