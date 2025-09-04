#!/usr/bin/env python3
"""
Database Migration System for MDUS
Manages database schema versions and applies migrations in order.
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Database migration manager for MDUS system"""
    
    def __init__(self, connection_string: str):
        """Initialize migrator with database connection"""
        self.connection_string = connection_string
        self.migrations_dir = Path(__file__).parent / "migrations"
        
    def connect(self):
        """Create database connection"""
        try:
            return psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor
            )
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            sys.exit(1)
    
    def ensure_migrations_table(self):
        """Ensure schema_migrations table exists"""
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version VARCHAR(255) PRIMARY KEY,
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
                conn.commit()
                logger.info("Ensured schema_migrations table exists")
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations"""
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
                return [row['version'] for row in cursor.fetchall()]
    
    def get_available_migrations(self) -> List[str]:
        """Get list of available migration files"""
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory {self.migrations_dir} not found")
            return []
        
        migrations = []
        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            migration_name = file_path.stem
            migrations.append(migration_name)
        
        return migrations
    
    def get_pending_migrations(self) -> List[str]:
        """Get list of pending migrations"""
        applied = set(self.get_applied_migrations())
        available = self.get_available_migrations()
        
        pending = [m for m in available if m not in applied]
        return sorted(pending)
    
    def apply_migration(self, migration_name: str) -> bool:
        """Apply a single migration"""
        migration_file = self.migrations_dir / f"{migration_name}.sql"
        
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        logger.info(f"Applying migration: {migration_name}")
        
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    # Read and execute migration SQL
                    migration_sql = migration_file.read_text()
                    cursor.execute(migration_sql)
                    
                    # Record migration as applied (if not already recorded in migration file)
                    cursor.execute("""
                        INSERT INTO schema_migrations (version) 
                        VALUES (%s) 
                        ON CONFLICT (version) DO NOTHING
                    """, (migration_name,))
                    
                    conn.commit()
                    logger.info(f"Successfully applied migration: {migration_name}")
                    return True
                    
        except psycopg2.Error as e:
            logger.error(f"Failed to apply migration {migration_name}: {e}")
            return False
    
    def migrate(self, target_version: Optional[str] = None) -> bool:
        """Apply all pending migrations up to target version"""
        self.ensure_migrations_table()
        
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return True
        
        # Filter to target version if specified
        if target_version:
            try:
                target_index = pending.index(target_version)
                pending = pending[:target_index + 1]
            except ValueError:
                logger.error(f"Target migration '{target_version}' not found in pending migrations")
                return False
        
        logger.info(f"Found {len(pending)} pending migrations")
        
        success_count = 0
        for migration in pending:
            if self.apply_migration(migration):
                success_count += 1
            else:
                logger.error(f"Migration failed, stopping at: {migration}")
                break
        
        logger.info(f"Applied {success_count}/{len(pending)} migrations")
        return success_count == len(pending)
    
    def status(self) -> Dict:
        """Get migration status"""
        self.ensure_migrations_table()
        
        applied = self.get_applied_migrations()
        available = self.get_available_migrations()
        pending = self.get_pending_migrations()
        
        return {
            "applied_count": len(applied),
            "available_count": len(available),
            "pending_count": len(pending),
            "applied_migrations": applied,
            "pending_migrations": pending,
            "is_up_to_date": len(pending) == 0
        }
    
    def rollback(self, target_version: str) -> bool:
        """Rollback to target version (simplified - requires manual rollback scripts)"""
        logger.warning("Rollback functionality requires manual rollback scripts")
        logger.warning("This is a simplified implementation - use with caution")
        
        applied = self.get_applied_migrations()
        
        if target_version not in applied:
            logger.error(f"Target version '{target_version}' not found in applied migrations")
            return False
        
        # Find migrations to rollback (those after target_version)
        target_index = applied.index(target_version)
        to_rollback = applied[target_index + 1:]
        
        if not to_rollback:
            logger.info(f"Already at target version: {target_version}")
            return True
        
        logger.warning(f"Would need to rollback {len(to_rollback)} migrations: {to_rollback}")
        logger.warning("Manual rollback required - removing migration records only")
        
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    for migration in reversed(to_rollback):
                        cursor.execute(
                            "DELETE FROM schema_migrations WHERE version = %s",
                            (migration,)
                        )
                        logger.info(f"Removed migration record: {migration}")
                    
                    conn.commit()
                    return True
                    
        except psycopg2.Error as e:
            logger.error(f"Failed to rollback: {e}")
            return False

def get_connection_string():
    """Get database connection string from environment or defaults"""
    return (
        f"postgresql://"
        f"{os.getenv('POSTGRES_USER', 'mdus_user')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'mdus_password')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'mdus_db')}"
    )

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="MDUS Database Migration Tool")
    parser.add_argument(
        "command",
        choices=["status", "migrate", "rollback"],
        help="Migration command to execute"
    )
    parser.add_argument(
        "--target",
        help="Target migration version"
    )
    parser.add_argument(
        "--connection-string",
        default=get_connection_string(),
        help="Database connection string"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    migrator = DatabaseMigrator(args.connection_string)
    
    if args.command == "status":
        status = migrator.status()
        print(f"Database Migration Status:")
        print(f"  Applied migrations: {status['applied_count']}")
        print(f"  Available migrations: {status['available_count']}")
        print(f"  Pending migrations: {status['pending_count']}")
        print(f"  Up to date: {status['is_up_to_date']}")
        
        if status['pending_migrations']:
            print(f"\nPending migrations:")
            for migration in status['pending_migrations']:
                print(f"  - {migration}")
    
    elif args.command == "migrate":
        success = migrator.migrate(args.target)
        sys.exit(0 if success else 1)
    
    elif args.command == "rollback":
        if not args.target:
            logger.error("--target required for rollback command")
            sys.exit(1)
        
        success = migrator.rollback(args.target)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()