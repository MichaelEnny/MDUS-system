"""
Database Connection and Session Management for MDUS System
Provides database connectivity, session management, and connection pooling.
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self, database_url: str = None, echo: bool = False):
        """Initialize database manager"""
        self.database_url = database_url or self._get_database_url()
        self.echo = echo
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
        self._setup_session_factory()
    
    def _get_database_url(self) -> str:
        """Get database URL from environment variables"""
        return (
            f"postgresql://"
            f"{os.getenv('POSTGRES_USER', 'mdus_user')}:"
            f"{os.getenv('POSTGRES_PASSWORD', 'mdus_password')}@"
            f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB', 'mdus_db')}"
        )
    
    def _setup_engine(self):
        """Setup SQLAlchemy engine with connection pooling"""
        # Connection pool settings optimized for document processing workload
        pool_settings = {
            'poolclass': QueuePool,
            'pool_size': int(os.getenv('DB_POOL_SIZE', '20')),  # Base pool size
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '30')),  # Additional connections
            'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),  # Timeout in seconds
            'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),  # Recycle connections after 1 hour
            'pool_pre_ping': True,  # Validate connections before use
        }
        
        # Create engine with optimization settings
        self.engine = create_engine(
            self.database_url,
            echo=self.echo,
            connect_args={
                "options": "-c timezone=utc",
                "application_name": "mdus_system",
                "connect_timeout": 10,
            },
            **pool_settings
        )
        
        # Add event listeners for monitoring and optimization
        self._setup_engine_events()
        
        logger.info(f"Database engine created with pool_size={pool_settings['pool_size']}")
    
    def _setup_engine_events(self):
        """Setup engine event listeners for monitoring and optimization"""
        
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set connection-level optimizations"""
            if 'postgresql' in self.database_url:
                with dbapi_connection.cursor() as cursor:
                    # Set session-level optimizations
                    cursor.execute("SET statement_timeout = '300s'")  # 5 minute timeout
                    cursor.execute("SET lock_timeout = '60s'")  # 1 minute lock timeout
                    cursor.execute("SET idle_in_transaction_session_timeout = '300s'")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout"""
            logger.debug(f"Connection checked out: {connection_record}")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log connection checkin"""
            logger.debug(f"Connection checked in: {connection_record}")
    
    def _setup_session_factory(self):
        """Setup session factory"""
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,  # Manual flush control for better performance
            bind=self.engine,
            expire_on_commit=False  # Keep objects accessible after commit
        )
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_factory(self):
        """Get session factory for dependency injection"""
        return self.SessionLocal
    
    def create_all_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_all_tables(self):
        """Drop all database tables (use with caution)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_pool_status(self) -> dict:
        """Get connection pool status"""
        if hasattr(self.engine.pool, 'size'):
            return {
                'pool_size': self.engine.pool.size(),
                'checked_in': self.engine.pool.checkedin(),
                'checked_out': self.engine.pool.checkedout(),
                'overflow': self.engine.pool.overflow(),
                'invalid': self.engine.pool.invalid(),
            }
        return {"status": "Pool information not available"}
    
    def close(self):
        """Close database engine and cleanup"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine closed")


# Global database manager instance
db_manager = None


def init_database(database_url: str = None, echo: bool = False) -> DatabaseManager:
    """Initialize global database manager"""
    global db_manager
    db_manager = DatabaseManager(database_url=database_url, echo=echo)
    return db_manager


def get_database_manager() -> Optional[DatabaseManager]:
    """Get global database manager instance"""
    return db_manager


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session from global manager"""
    if not db_manager:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    with db_manager.get_session() as session:
        yield session


def get_db_session_factory():
    """Get session factory from global manager"""
    if not db_manager:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    return db_manager.get_session_factory()


# Dependency for FastAPI or similar frameworks
def get_db():
    """Database dependency for FastAPI"""
    if not db_manager:
        raise RuntimeError("Database not initialized")
    
    db = db_manager.SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseHealthCheck:
    """Database health monitoring utilities"""
    
    @staticmethod
    def check_database_health() -> dict:
        """Comprehensive database health check"""
        if not db_manager:
            return {"status": "error", "message": "Database not initialized"}
        
        try:
            with get_db_session() as session:
                # Check basic connectivity
                session.execute(text("SELECT 1"))
                
                # Check key tables exist
                tables_check = session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name IN 
                    ('users', 'documents', 'document_analysis', 'processing_jobs')
                """)).fetchall()
                
                # Check pool status
                pool_status = db_manager.get_pool_status()
                
                # Check for long-running transactions
                long_transactions = session.execute(text("""
                    SELECT count(*) 
                    FROM pg_stat_activity 
                    WHERE state = 'active' AND now() - query_start > interval '5 minutes'
                """)).scalar()
                
                return {
                    "status": "healthy",
                    "tables_found": len(tables_check),
                    "pool_status": pool_status,
                    "long_running_transactions": long_transactions,
                    "timestamp": session.execute(text("SELECT NOW()")).scalar()
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "error", 
                "message": str(e),
                "pool_status": db_manager.get_pool_status() if db_manager else None
            }
    
    @staticmethod
    def get_database_stats() -> dict:
        """Get database performance statistics"""
        if not db_manager:
            return {"error": "Database not initialized"}
        
        try:
            with get_db_session() as session:
                stats = {}
                
                # Table sizes
                table_stats = session.execute(text("""
                    SELECT 
                        schemaname as schema,
                        tablename as table,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes,
                        n_live_tup as live_tuples,
                        n_dead_tup as dead_tuples
                    FROM pg_stat_user_tables
                    ORDER BY n_live_tup DESC
                """)).fetchall()
                
                stats['table_statistics'] = [dict(row) for row in table_stats]
                
                # Index usage
                index_stats = session.execute(text("""
                    SELECT 
                        schemaname as schema,
                        tablename as table,
                        indexname as index,
                        idx_tup_read as tuples_read,
                        idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes
                    WHERE idx_tup_read > 0
                    ORDER BY idx_tup_read DESC
                    LIMIT 20
                """)).fetchall()
                
                stats['index_usage'] = [dict(row) for row in index_stats]
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}