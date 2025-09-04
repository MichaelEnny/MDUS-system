"""
Database connection and session management
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from .config import get_settings

logger = logging.getLogger(__name__)

# Global variables
engine = None
SessionLocal = None

async def init_db():
    """Initialize database connection"""
    global engine, SessionLocal
    
    settings = get_settings()
    
    # Create async engine
    engine = create_async_engine(
        settings.postgres_url.replace("postgresql://", "postgresql+asyncpg://"),
        poolclass=NullPool,
        echo=False,  # Set to True for SQL logging
        future=True
    )
    
    # Create session factory
    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        autocommit=False
    )
    
    logger.info("Database connection initialized")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    if SessionLocal is None:
        await init_db()
    
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def close_db():
    """Close database connection"""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")