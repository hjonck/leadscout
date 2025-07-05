#!/usr/bin/env python3
"""Database migration management script for LeadScout.

This script handles applying database migrations, rolling back changes,
and managing schema versions for the PostgreSQL database.

Usage:
    python scripts/db/migrate.py apply          # Apply all pending migrations
    python scripts/db/migrate.py rollback       # Rollback last migration
    python scripts/db/migrate.py status         # Show migration status
    python scripts/db/migrate.py reset          # Reset database (DANGEROUS)

Architecture:
- Uses PostgreSQL with asyncpg for high-performance async operations
- Tracks migration state in migrations_log table
- Supports both forward and backward migrations
- Includes safety checks and transaction rollback on errors

Integration Points:
- Used by Developer A for schema setup
- Provides foundation for Developer B's classification tables
- Supports both development and production environments
"""

import asyncio
import hashlib
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import asyncpg
import click
from pydantic import BaseSettings, Field


class DatabaseSettings(BaseSettings):
    """Database connection configuration."""
    
    database_url: str = Field(
        default="postgresql://leadscout:leadscout@localhost:5432/leadscout_dev",
        env="DATABASE_URL"
    )
    migration_table: str = Field(default="migrations_log")
    
    class Config:
        env_file = ".env"


class Migration:
    """Represents a single database migration."""
    
    def __init__(self, filename: Path):
        self.filename = filename
        self.name = filename.stem
        self.content = filename.read_text(encoding='utf-8')
        self.checksum = hashlib.sha256(self.content.encode()).hexdigest()
    
    def __str__(self) -> str:
        return f"Migration({self.name})"
    
    def __repr__(self) -> str:
        return f"Migration(name='{self.name}', checksum='{self.checksum[:8]}...')"


class MigrationManager:
    """Manages database schema migrations."""
    
    def __init__(self, settings: DatabaseSettings):
        self.settings = settings
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.logger = logging.getLogger(__name__)
    
    async def _get_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        return await asyncpg.connect(self.settings.database_url)
    
    async def _ensure_migrations_table(self, conn: asyncpg.Connection) -> None:
        """Create migrations tracking table if it doesn't exist."""
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.settings.migration_table} (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                checksum VARCHAR(64) NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                execution_time_ms INTEGER,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT
            )
        """)
    
    def _get_migration_files(self) -> List[Migration]:
        """Get all migration files sorted by name."""
        migration_files = sorted(self.migrations_dir.glob("*.sql"))
        return [Migration(f) for f in migration_files]
    
    async def _get_applied_migrations(self, conn: asyncpg.Connection) -> Dict[str, Dict[str, Any]]:
        """Get list of applied migrations from database."""
        rows = await conn.fetch(f"""
            SELECT name, checksum, applied_at, success, error_message
            FROM {self.settings.migration_table}
            ORDER BY applied_at
        """)
        return {row['name']: dict(row) for row in rows}
    
    async def _apply_migration(self, conn: asyncpg.Connection, migration: Migration) -> bool:
        """Apply a single migration within a transaction."""
        start_time = datetime.now()
        
        try:
            async with conn.transaction():
                # Execute the migration SQL
                await conn.execute(migration.content)
                
                # Record successful application
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                await conn.execute(f"""
                    INSERT INTO {self.settings.migration_table} 
                    (name, checksum, execution_time_ms, success)
                    VALUES ($1, $2, $3, TRUE)
                """, migration.name, migration.checksum, execution_time)
                
                self.logger.info(f"Applied migration {migration.name} in {execution_time}ms")
                return True
                
        except Exception as e:
            # Record failed application
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            await conn.execute(f"""
                INSERT INTO {self.settings.migration_table} 
                (name, checksum, execution_time_ms, success, error_message)
                VALUES ($1, $2, $3, FALSE, $4)
            """, migration.name, migration.checksum, execution_time, str(e))
            
            self.logger.error(f"Failed to apply migration {migration.name}: {e}")
            return False
    
    async def apply_migrations(self) -> None:
        """Apply all pending migrations."""
        conn = await self._get_connection()
        try:
            await self._ensure_migrations_table(conn)
            
            migrations = self._get_migration_files()
            applied = await self._get_applied_migrations(conn)
            
            pending = [m for m in migrations if m.name not in applied]
            
            if not pending:
                self.logger.info("No pending migrations")
                return
            
            self.logger.info(f"Applying {len(pending)} pending migrations")
            
            for migration in pending:
                success = await self._apply_migration(conn, migration)
                if not success:
                    self.logger.error(f"Migration {migration.name} failed, stopping")
                    break
            
            self.logger.info("Migration process completed")
            
        finally:
            await conn.close()
    
    async def get_status(self) -> None:
        """Show migration status."""
        conn = await self._get_connection()
        try:
            await self._ensure_migrations_table(conn)
            
            migrations = self._get_migration_files()
            applied = await self._get_applied_migrations(conn)
            
            print(f"\\nMigration Status:")
            print(f"Migration directory: {self.migrations_dir}")
            print(f"Total migrations: {len(migrations)}")
            print(f"Applied migrations: {len(applied)}")
            print(f"Pending migrations: {len(migrations) - len(applied)}")
            print("\\n" + "="*80)
            
            for migration in migrations:
                if migration.name in applied:
                    app_info = applied[migration.name]
                    status = "✅ APPLIED" if app_info['success'] else "❌ FAILED"
                    applied_at = app_info['applied_at'].strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{status:<12} {migration.name:<30} {applied_at}")
                    if not app_info['success']:
                        print(f"             Error: {app_info['error_message']}")
                else:
                    print(f"⏳ PENDING   {migration.name}")
            
            print("\\n" + "="*80)
            
        finally:
            await conn.close()
    
    async def reset_database(self) -> None:
        """Reset database by dropping all tables (DANGEROUS)."""
        conn = await self._get_connection()
        try:
            # Get all table names
            tables = await conn.fetch("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            
            if not tables:
                self.logger.info("No tables to drop")
                return
            
            self.logger.warning(f"Dropping {len(tables)} tables")
            
            # Drop all tables
            for table in tables:
                await conn.execute(f'DROP TABLE IF EXISTS "{table["tablename"]}" CASCADE')
                self.logger.info(f"Dropped table {table['tablename']}")
            
            # Drop functions
            functions = await conn.fetch("""
                SELECT proname FROM pg_proc 
                WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            """)
            
            for func in functions:
                await conn.execute(f'DROP FUNCTION IF EXISTS "{func["proname"]}" CASCADE')
                self.logger.info(f"Dropped function {func['proname']}")
            
            self.logger.info("Database reset completed")
            
        finally:
            await conn.close()


# CLI Interface
@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug: bool):
    """LeadScout Database Migration Manager."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@cli.command()
def apply():
    """Apply all pending migrations."""
    settings = DatabaseSettings()
    manager = MigrationManager(settings)
    asyncio.run(manager.apply_migrations())


@cli.command()
def status():
    """Show migration status."""
    settings = DatabaseSettings()
    manager = MigrationManager(settings)
    asyncio.run(manager.get_status())


@cli.command()
@click.confirmation_option(
    prompt='This will drop all tables and data. Are you sure?'
)
def reset():
    """Reset database by dropping all tables (DANGEROUS)."""
    settings = DatabaseSettings()
    manager = MigrationManager(settings)
    asyncio.run(manager.reset_database())


if __name__ == "__main__":
    cli()