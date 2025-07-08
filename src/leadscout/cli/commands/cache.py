"""Cache management commands."""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import click
import pandas as pd

from ...core.config import Settings


@click.group()
def cache() -> None:
    """Manage the LeadScout cache system.

    The cache stores enrichment results to improve performance and
    reduce API costs. Commands allow you to view status, clean up
    old entries, and manage cache data.
    """


@cache.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show cache status and statistics.

    Displays information about:
    - Cache size and location
    - Number of cached leads and classifications
    - Cache hit rates and performance metrics
    - Storage usage and cleanup recommendations
    """
    verbose: bool = ctx.obj.get("verbose", False)

    if verbose:
        click.echo("Retrieving cache status...")

    try:
        settings = Settings()
        cache_dir = settings.cache_dir
        
        click.echo("Cache Status")
        click.echo("=" * 50)
        click.echo(f"Cache directory: {cache_dir}")
        
        # Check if cache directory exists
        if not cache_dir.exists():
            click.echo("❌ Cache directory does not exist")
            return
            
        # Get database files
        jobs_db = cache_dir / "jobs.db"
        learning_db = cache_dir / "llm_learning.db"
        
        click.echo(f"\n📁 Database Files:")
        
        # Jobs database statistics
        if jobs_db.exists():
            size_mb = jobs_db.stat().st_size / (1024 * 1024)
            click.echo(f"  Jobs database: ✅ {size_mb:.2f} MB")
            
            try:
                conn = sqlite3.connect(jobs_db)
                
                # Get job count
                cursor = conn.execute("SELECT COUNT(*) FROM job_executions")
                job_count = cursor.fetchone()[0]
                
                # Get lead processing count
                cursor = conn.execute("SELECT COUNT(*) FROM lead_processing_results")
                lead_count = cursor.fetchone()[0]
                
                # Get recent activity
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM job_executions 
                    WHERE start_time > datetime('now', '-7 days')
                """)
                recent_jobs = cursor.fetchone()[0]
                
                conn.close()
                
                click.echo(f"    Total jobs: {job_count}")
                click.echo(f"    Total leads processed: {lead_count}")
                click.echo(f"    Recent jobs (7 days): {recent_jobs}")
                
            except Exception as e:
                click.echo(f"    ❌ Could not query database: {e}")
        else:
            click.echo(f"  Jobs database: ❌ Not found")
        
        # Learning database statistics
        if learning_db.exists():
            size_mb = learning_db.stat().st_size / (1024 * 1024)
            click.echo(f"  Learning database: ✅ {size_mb:.2f} MB")
            
            try:
                conn = sqlite3.connect(learning_db)
                
                # Get LLM classifications count
                cursor = conn.execute("SELECT COUNT(*) FROM llm_classifications")
                llm_count = cursor.fetchone()[0]
                
                # Get learned patterns count
                cursor = conn.execute("SELECT COUNT(*) FROM learned_patterns WHERE is_active = true")
                pattern_count = cursor.fetchone()[0]
                
                # Get phonetic families count
                cursor = conn.execute("SELECT COUNT(*) FROM phonetic_families")
                phonetic_count = cursor.fetchone()[0]
                
                conn.close()
                
                click.echo(f"    LLM classifications: {llm_count}")
                click.echo(f"    Active patterns: {pattern_count}")
                click.echo(f"    Phonetic families: {phonetic_count}")
                
            except Exception as e:
                click.echo(f"    ❌ Could not query database: {e}")
        else:
            click.echo(f"  Learning database: ❌ Not found")
        
        # Calculate total cache size
        total_size = 0
        for db_file in [jobs_db, learning_db]:
            if db_file.exists():
                total_size += db_file.stat().st_size
        
        total_size_mb = total_size / (1024 * 1024)
        
        click.echo(f"\n💾 Storage Summary:")
        click.echo(f"  Total cache size: {total_size_mb:.2f} MB")
        
        # Show cache effectiveness if we have data
        if jobs_db.exists() and learning_db.exists():
            try:
                # This would calculate cache hit rates
                click.echo(f"  Cache efficiency: Operational")
            except:
                pass
                
    except Exception as e:
        click.echo(f"❌ Failed to get cache status: {e}", err=True)
        ctx.exit(1)


@cache.command()
@click.option(
    "--older-than",
    type=int,
    default=30,
    help="Remove entries older than N days (default: 30)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be cleaned without actually doing it",
)
@click.pass_context
def clean(ctx: click.Context, older_than: int, dry_run: bool) -> None:
    """Clean up expired cache entries.

    Removes old cache entries to free up storage space and maintain
    performance. By default, removes entries older than 30 days.

    Examples:
        leadscout cache clean
        leadscout cache clean --older-than 7
        leadscout cache clean --dry-run
    """
    verbose: bool = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"Cleaning cache entries older than {older_than} days")
        click.echo(f"Dry run: {dry_run}")

    try:
        settings = Settings()
        cache_dir = settings.cache_dir
        
        if not cache_dir.exists():
            click.echo("❌ Cache directory does not exist")
            return
            
        cutoff_date = datetime.now() - timedelta(days=older_than)
        cutoff_str = cutoff_date.isoformat()
        
        click.echo(f"Cache Cleanup")
        click.echo("=" * 50)
        click.echo(f"Removing entries older than: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        jobs_db = cache_dir / "jobs.db"
        learning_db = cache_dir / "llm_learning.db"
        
        total_cleaned = 0
        
        # Clean jobs database
        if jobs_db.exists():
            try:
                conn = sqlite3.connect(jobs_db)
                
                if dry_run:
                    # Count what would be cleaned
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM job_executions 
                        WHERE completion_time < ? AND status = 'completed'
                    """, (cutoff_str,))
                    old_jobs = cursor.fetchone()[0]
                    
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM lead_processing_results lpr
                        JOIN job_executions je ON lpr.job_id = je.job_id
                        WHERE je.completion_time < ? AND je.status = 'completed'
                    """, (cutoff_str,))
                    old_results = cursor.fetchone()[0]
                    
                    click.echo(f"\n📋 Jobs Database (dry run):")
                    click.echo(f"  Would remove {old_jobs} completed jobs")
                    click.echo(f"  Would remove {old_results} lead processing results")
                    total_cleaned += old_jobs + old_results
                    
                else:
                    # Actually clean
                    cursor = conn.execute("""
                        DELETE FROM lead_processing_results 
                        WHERE job_id IN (
                            SELECT job_id FROM job_executions 
                            WHERE completion_time < ? AND status = 'completed'
                        )
                    """, (cutoff_str,))
                    results_deleted = cursor.rowcount
                    
                    cursor = conn.execute("""
                        DELETE FROM job_executions 
                        WHERE completion_time < ? AND status = 'completed'
                    """, (cutoff_str,))
                    jobs_deleted = cursor.rowcount
                    
                    conn.commit()
                    
                    click.echo(f"\n📋 Jobs Database:")
                    click.echo(f"  Removed {jobs_deleted} completed jobs")
                    click.echo(f"  Removed {results_deleted} lead processing results")
                    total_cleaned += jobs_deleted + results_deleted
                
                conn.close()
                
            except Exception as e:
                click.echo(f"  ❌ Error cleaning jobs database: {e}")
        else:
            click.echo(f"\n📋 Jobs Database: Not found")
        
        # Clean learning database
        if learning_db.exists():
            try:
                conn = sqlite3.connect(learning_db)
                
                if dry_run:
                    # Count what would be cleaned
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM classification_cache 
                        WHERE cached_timestamp < datetime('now', '-' || cache_ttl_hours || ' hours')
                        OR access_count = 0
                    """)
                    old_cache = cursor.fetchone()[0]
                    
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM learned_patterns 
                        WHERE last_validated < ? AND success_rate < 0.3
                    """, (cutoff_str,))
                    old_patterns = cursor.fetchone()[0]
                    
                    click.echo(f"\n🧠 Learning Database (dry run):")
                    click.echo(f"  Would remove {old_cache} expired cache entries")
                    click.echo(f"  Would deactivate {old_patterns} low-performing patterns")
                    total_cleaned += old_cache
                    
                else:
                    # Clean expired cache entries
                    cursor = conn.execute("""
                        DELETE FROM classification_cache 
                        WHERE cached_timestamp < datetime('now', '-' || cache_ttl_hours || ' hours')
                        OR (access_count = 0 AND cached_timestamp < ?)
                    """, (cutoff_str,))
                    cache_deleted = cursor.rowcount
                    
                    # Deactivate poor-performing patterns
                    cursor = conn.execute("""
                        UPDATE learned_patterns 
                        SET is_active = false 
                        WHERE last_validated < ? AND success_rate < 0.3
                    """, (cutoff_str,))
                    patterns_deactivated = cursor.rowcount
                    
                    conn.commit()
                    
                    click.echo(f"\n🧠 Learning Database:")
                    click.echo(f"  Removed {cache_deleted} expired cache entries")
                    click.echo(f"  Deactivated {patterns_deactivated} low-performing patterns")
                    total_cleaned += cache_deleted
                
                conn.close()
                
            except Exception as e:
                click.echo(f"  ❌ Error cleaning learning database: {e}")
        else:
            click.echo(f"\n🧠 Learning Database: Not found")
        
        # Summary
        click.echo(f"\n📊 Summary:")
        if dry_run:
            click.echo(f"  Would clean {total_cleaned} items")
            click.echo(f"  Run without --dry-run to actually clean")
        else:
            click.echo(f"  ✅ Cleaned {total_cleaned} items")
            click.echo(f"  Cache cleanup completed")
            
    except Exception as e:
        click.echo(f"❌ Cache cleanup failed: {e}", err=True)
        ctx.exit(1)


@cache.command()
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "xlsx"]),
    default="json",
    help="Export format (default: json)",
)
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output file path"
)
@click.pass_context
def export(ctx: click.Context, format: str, output: Optional[Path]) -> None:
    """Export cache data for analysis.

    Exports cached enrichment data in various formats for analysis,
    backup, or migration purposes.

    Examples:
        leadscout cache export --format json --output cache_data.json
        leadscout cache export --format csv --output classifications.csv
    """
    verbose: bool = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"Exporting cache data in {format} format")
        if output:
            click.echo(f"Output file: {output}")

    # Generate output filename if not provided
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Path(f"leadscout_cache_export_{timestamp}.{format}")

    try:
        settings = Settings()
        cache_dir = settings.cache_dir
        
        if not cache_dir.exists():
            click.echo("❌ Cache directory does not exist")
            return
            
        click.echo(f"Cache Export")
        click.echo("=" * 50)
        click.echo(f"Format: {format}")
        click.echo(f"Output: {output}")
        
        jobs_db = cache_dir / "jobs.db"
        learning_db = cache_dir / "llm_learning.db"
        
        export_data = {}
        
        # Export jobs data
        if jobs_db.exists():
            try:
                conn = sqlite3.connect(jobs_db)
                
                # Get jobs summary
                df_jobs = pd.read_sql_query("SELECT * FROM job_executions", conn)
                df_results = pd.read_sql_query("SELECT * FROM lead_processing_results", conn)
                
                export_data["jobs"] = df_jobs.to_dict('records')
                export_data["results"] = df_results.to_dict('records')
                
                click.echo(f"  ✅ Jobs data: {len(df_jobs)} jobs, {len(df_results)} results")
                conn.close()
                
            except Exception as e:
                click.echo(f"  ❌ Error reading jobs database: {e}")
        else:
            click.echo(f"  ⚠️  Jobs database not found")
            
        # Export learning data
        if learning_db.exists():
            try:
                conn = sqlite3.connect(learning_db)
                
                # Get learning data
                df_llm = pd.read_sql_query("SELECT * FROM llm_classifications", conn)
                df_patterns = pd.read_sql_query("SELECT * FROM learned_patterns", conn)
                df_families = pd.read_sql_query("SELECT * FROM phonetic_families", conn)
                
                export_data["llm_classifications"] = df_llm.to_dict('records')
                export_data["learned_patterns"] = df_patterns.to_dict('records')
                export_data["phonetic_families"] = df_families.to_dict('records')
                
                click.echo(f"  ✅ Learning data: {len(df_llm)} classifications, {len(df_patterns)} patterns")
                conn.close()
                
            except Exception as e:
                click.echo(f"  ❌ Error reading learning database: {e}")
        else:
            click.echo(f"  ⚠️  Learning database not found")
        
        # Add metadata
        export_data["metadata"] = {
            "export_timestamp": datetime.now().isoformat(),
            "export_format": format,
            "cache_directory": str(cache_dir),
            "total_tables": len([k for k in export_data.keys() if k != "metadata"])
        }
        
        # Save in requested format
        if format == "json":
            with open(output, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
                
        elif format == "csv":
            # For CSV, create multiple files
            base_name = output.stem
            output_dir = output.parent
            
            for table_name, data in export_data.items():
                if table_name == "metadata":
                    continue
                    
                if data:  # Only create file if there's data
                    csv_file = output_dir / f"{base_name}_{table_name}.csv"
                    df = pd.DataFrame(data)
                    df.to_csv(csv_file, index=False)
                    click.echo(f"    Created: {csv_file}")
                    
        elif format == "xlsx":
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for table_name, data in export_data.items():
                    if table_name == "metadata":
                        # Create metadata sheet
                        meta_df = pd.DataFrame([export_data["metadata"]])
                        meta_df.to_excel(writer, sheet_name='metadata', index=False)
                    elif data:  # Only create sheet if there's data
                        df = pd.DataFrame(data)
                        # Limit sheet name length
                        sheet_name = table_name[:31]  # Excel sheet name limit
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        click.echo(f"\n✅ Cache export completed successfully")
        click.echo(f"   Exported to: {output}")
        
        # Show file size
        if output.exists():
            size_mb = output.stat().st_size / (1024 * 1024)
            click.echo(f"   File size: {size_mb:.2f} MB")
            
    except Exception as e:
        click.echo(f"❌ Cache export failed: {e}", err=True)
        ctx.exit(1)


@cache.command()
@click.confirmation_option(
    prompt="Are you sure you want to rebuild the entire cache?"
)
@click.pass_context
def rebuild(ctx: click.Context) -> None:
    """Rebuild the entire cache from scratch.

    WARNING: This will delete all cached data and rebuild the cache
    structure. Use this if the cache becomes corrupted or you need
    to upgrade the cache schema.

    This operation cannot be undone.
    """
    verbose: bool = ctx.obj.get("verbose", False)

    if verbose:
        click.echo("Rebuilding cache from scratch...")

    try:
        settings = Settings()
        cache_dir = settings.cache_dir
        
        click.echo(f"Cache Rebuild")
        click.echo("=" * 50)
        click.echo("⚠️  WARNING: This will delete ALL cached data!")
        click.echo(f"Cache directory: {cache_dir}")
        
        jobs_db = cache_dir / "jobs.db"
        learning_db = cache_dir / "llm_learning.db"
        
        # Backup existing databases first
        backup_dir = cache_dir / "backup"
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backed_up = []
        
        for db_file in [jobs_db, learning_db]:
            if db_file.exists():
                backup_file = backup_dir / f"{db_file.stem}_backup_{timestamp}.db"
                import shutil
                shutil.copy2(db_file, backup_file)
                backed_up.append(backup_file)
                click.echo(f"  📋 Backed up: {db_file.name} → {backup_file.name}")
        
        if backed_up:
            click.echo(f"  ✅ Created {len(backed_up)} backup files in {backup_dir}")
        
        # Delete existing databases
        deleted = []
        for db_file in [jobs_db, learning_db]:
            if db_file.exists():
                db_file.unlink()
                deleted.append(db_file.name)
                click.echo(f"  🗑️  Deleted: {db_file.name}")
        
        if deleted:
            click.echo(f"  ✅ Removed {len(deleted)} database files")
        else:
            click.echo("  ℹ️  No existing databases to remove")
        
        # Recreate database structures
        click.echo(f"\n🔧 Recreating database structures...")
        
        # Recreate jobs database
        try:
            from ...core.job_database import JobDatabase
            job_db = JobDatabase()  # This will create the database structure
            click.echo(f"  ✅ Jobs database: Structure created")
        except Exception as e:
            click.echo(f"  ❌ Jobs database: Failed to create - {e}")
        
        # Recreate learning database
        try:
            from ...classification.learning_database import LLMLearningDatabase
            learning_db = LLMLearningDatabase()  # This will create the database structure
            click.echo(f"  ✅ Learning database: Structure created")
        except Exception as e:
            click.echo(f"  ❌ Learning database: Failed to create - {e}")
        
        # Verify new databases
        click.echo(f"\n🔍 Verifying new databases...")
        
        created = []
        for db_file in [jobs_db, learning_db]:
            if db_file.exists():
                size_mb = db_file.stat().st_size / (1024 * 1024)
                created.append(db_file.name)
                click.echo(f"  ✅ {db_file.name}: {size_mb:.3f} MB")
            else:
                click.echo(f"  ❌ {db_file.name}: Not created")
        
        # Summary
        click.echo(f"\n📊 Rebuild Summary:")
        click.echo(f"  Backed up: {len(backed_up)} files")
        click.echo(f"  Deleted: {len(deleted)} files")
        click.echo(f"  Created: {len(created)} files")
        
        if len(created) == 2:
            click.echo(f"  ✅ Cache rebuild completed successfully")
        else:
            click.echo(f"  ⚠️  Cache rebuild completed with issues")
            
        if backed_up:
            click.echo(f"\n💡 Backup files are available in: {backup_dir}")
            
    except Exception as e:
        click.echo(f"❌ Cache rebuild failed: {e}", err=True)
        ctx.exit(1)
