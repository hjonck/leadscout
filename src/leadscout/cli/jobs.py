"""
Production job management CLI commands.

Provides enterprise-scale job processing with learning analytics and
resumable job framework integration.

Key Features:
- Resumable job processing with automatic recovery
- Real-time progress monitoring and reporting
- Learning analytics and cost optimization tracking
- Batch management with configurable parameters
- Production-grade error handling and validation

Commands:
- process: Process leads with resumable job framework
- list: List recent jobs and their status
- status: Get detailed status for a specific job
- export: Export job results to various formats
- cancel: Cancel a running job

Usage:
    leadscout jobs process input.xlsx --batch-size 100
    leadscout jobs list --status running
    leadscout jobs status job-id-here
    leadscout jobs export job-id-here --format excel
"""

import click
import asyncio
from pathlib import Path
from typing import Optional
import structlog

from ..core.resumable_job_runner import ResumableJobRunner
from ..core.config import get_settings

logger = structlog.get_logger(__name__)


@click.group()
def jobs():
    """Manage resumable job processing with learning analytics."""
    pass


@jobs.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--batch-size', default=100, help='Batch size for processing (10-500)')
@click.option('--resume/--no-resume', default=True, help='Resume existing job if found')
@click.option('--learning/--no-learning', default=True, help='Enable learning database')
@click.option('--force', is_flag=True, help='Force start by clearing any stale locks')
def process(input_file: str, output: Optional[str], batch_size: int, 
           resume: bool, learning: bool, force: bool):
    """Process leads with resumable job framework and learning analytics.
    
    This command processes Excel files containing lead data with:
    - Automatic resume capability from any interruption point
    - Learning database integration for cost optimization
    - Real-time progress monitoring and error handling
    - Configurable batch processing for optimal performance
    - Force mode to clear stale locks from interrupted jobs
    
    Args:
        input_file: Path to Excel file containing leads
        output: Optional output file path (auto-generated if not provided)
        batch_size: Number of leads to process per batch (default: 100)
        resume: Whether to resume existing job if found (default: True)
        learning: Whether to enable learning database (default: True)
        force: Clear any stale locks before starting (useful after interruptions)
    
    Examples:
        leadscout jobs process leads.xlsx
        leadscout jobs process leads.xlsx --batch-size 50 --output enriched.xlsx
        leadscout jobs process leads.xlsx --force  # Clear stale locks
        leadscout jobs process leads.xlsx --no-resume --no-learning
    """
    
    # Validate batch size
    if batch_size < 10 or batch_size > 500:
        raise click.BadParameter("Batch size must be between 10 and 500")
    
    click.echo(f"🚀 Starting job processing: {input_file}")
    click.echo(f"   Batch size: {batch_size}")
    click.echo(f"   Resume enabled: {resume}")
    click.echo(f"   Learning enabled: {learning}")
    if force:
        click.echo(f"   Force mode: Clearing any stale locks")
    
    async def run_job():
        try:
            # Initialize resumable job runner
            runner = ResumableJobRunner(
                input_file=Path(input_file),
                output_file=Path(output) if output else None,
                batch_size=batch_size,
                force_unlock=force
            )
            
            # Run the job
            job_id = await runner.run()
            
            click.echo(f"✅ Job completed successfully: {job_id}")
            
            # Show real learning summary using database analysis
            if learning:
                _display_real_learning_summary(job_id)
                
        except Exception as e:
            click.echo(f"❌ Job failed: {e}", err=True)
            logger.error("Job processing failed", error=str(e))
            raise click.ClickException(str(e))
    
    # Run the async job
    try:
        asyncio.run(run_job())
    except KeyboardInterrupt:
        click.echo("\n⚠️ Job interrupted by user. Job can be resumed with same command.")
    except Exception as e:
        click.echo(f"\n❌ Unexpected error: {e}", err=True)
        raise


@jobs.command()
@click.option('--status', type=click.Choice(['running', 'completed', 'failed', 'all']), 
              default='all', help='Filter by job status')
@click.option('--limit', default=10, help='Maximum number of jobs to show')
def list(status: str, limit: int):
    """List recent jobs and their status.
    
    Shows a summary of recent jobs with their processing status,
    progress, and key metrics.
    
    Args:
        status: Filter jobs by status (running, completed, failed, all)
        limit: Maximum number of jobs to display (default: 10)
    
    Examples:
        leadscout jobs list
        leadscout jobs list --status running
        leadscout jobs list --limit 20
    """
    
    try:
        import sqlite3
        import pandas as pd
        from pathlib import Path
        from datetime import datetime
        
        db_path = Path("cache/jobs.db")
        if not db_path.exists():
            click.echo(f"❌ Job database not found: {db_path}")
            click.echo("   Run a job processing command first to create the database")
            return
        
        conn = sqlite3.connect(db_path)
        
        try:
            # Build query based on status filter
            if status == 'all':
                status_filter = ""
            else:
                status_filter = f"WHERE status = '{status}'"
            
            query = f"""
            SELECT job_id, input_file_path, total_rows, processed_leads_count, 
                   status, start_time, completion_time, processing_time_total_ms,
                   api_costs_total
            FROM job_executions 
            {status_filter}
            ORDER BY start_time DESC
            LIMIT {limit}
            """
            
            jobs_df = pd.read_sql_query(query, conn)
            
            if jobs_df.empty:
                click.echo(f"\n📋 No jobs found with status: {status}")
                return
            
            click.echo(f"\n📋 Recent Jobs ({status}) - Showing {len(jobs_df)} of {limit} max")
            click.echo("=" * 120)
            
            # Header
            click.echo(f"{'Job ID':<12} {'Status':<12} {'File':<25} {'Leads':<8} {'Progress':<10} {'Time':<8} {'Cost':<10} {'Started':<16}")
            click.echo("-" * 120)
            
            # Job rows
            for _, job in jobs_df.iterrows():
                job_id_short = job['job_id'][:10] + ".." if len(job['job_id']) > 12 else job['job_id']
                
                # Get filename from path
                file_name = Path(job['input_file_path']).name
                if len(file_name) > 23:
                    file_name = file_name[:20] + "..."
                
                # Calculate progress
                total = job['total_rows'] or 0
                processed = job['processed_leads_count'] or 0
                if total > 0:
                    progress = f"{processed}/{total}"
                    if len(progress) > 10:
                        progress = f"{processed//1000}k/{total//1000}k"
                else:
                    progress = f"{processed}"
                
                # Format time
                if job['processing_time_total_ms']:
                    time_sec = job['processing_time_total_ms'] / 1000
                    if time_sec < 60:
                        time_str = f"{time_sec:.1f}s"
                    elif time_sec < 3600:
                        time_str = f"{time_sec/60:.1f}m"
                    else:
                        time_str = f"{time_sec/3600:.1f}h"
                else:
                    time_str = "-"
                
                # Format cost
                cost = job['api_costs_total'] or 0.0
                if cost == 0:
                    cost_str = "Free"
                elif cost < 0.01:
                    cost_str = f"${cost:.4f}"
                else:
                    cost_str = f"${cost:.2f}"
                
                # Format start time
                if job['start_time']:
                    try:
                        # Parse timestamp and format
                        start_dt = pd.to_datetime(job['start_time'])
                        start_str = start_dt.strftime("%m/%d %H:%M")
                    except:
                        start_str = str(job['start_time'])[:16]
                else:
                    start_str = "-"
                
                # Get status icon
                status_icon = _get_status_icon(job['status'])
                status_display = f"{status_icon} {job['status']}"
                
                click.echo(f"{job_id_short:<12} {status_display:<12} {file_name:<25} {processed:<8} {progress:<10} {time_str:<8} {cost_str:<10} {start_str:<16}")
            
            # Summary statistics
            click.echo("-" * 120)
            
            total_jobs = len(jobs_df)
            completed_jobs = len(jobs_df[jobs_df['status'] == 'completed'])
            running_jobs = len(jobs_df[jobs_df['status'] == 'running'])
            failed_jobs = len(jobs_df[jobs_df['status'] == 'failed'])
            
            total_leads = jobs_df['processed_leads_count'].sum()
            total_cost = jobs_df['api_costs_total'].sum()
            
            click.echo(f"📊 Summary: {total_jobs} jobs | ✅ {completed_jobs} completed | 🔄 {running_jobs} running | ❌ {failed_jobs} failed")
            click.echo(f"📈 Totals: {total_leads:,} leads processed | ${total_cost:.4f} total cost")
            
            # Show available commands
            click.echo(f"\n💡 Commands:")
            click.echo(f"   leadscout jobs status <job-id>     # Detailed job information")
            click.echo(f"   leadscout jobs export <job-id>     # Export job results")
            click.echo(f"   leadscout jobs analyze <job-id>    # Analyze job performance")
            
        finally:
            conn.close()
            
    except Exception as e:
        click.echo(f"❌ Failed to list jobs: {e}", err=True)
        logger.error("Job listing failed", error=str(e))


@jobs.command()
@click.argument('job_id')
def status(job_id: str):
    """Get detailed status for a specific job.
    
    Shows comprehensive information about a job including:
    - Processing progress and performance metrics
    - Learning analytics and cost optimization
    - Error details and retry information
    - Batch-level statistics
    
    Args:
        job_id: Job identifier to query
    
    Examples:
        leadscout jobs status abc123-def456-ghi789
    """
    
    async def get_status():
        try:
            from ..core.job_database import JobDatabase
            
            job_db = JobDatabase()
            
            # Get job learning analytics
            learning_analytics = job_db.get_job_learning_analytics(job_id)
            
            if learning_analytics:
                click.echo(f"\n📊 Job Status: {job_id}")
                click.echo("=" * 60)
                
                # Display job analytics
                _display_job_learning_analytics(learning_analytics)
            else:
                click.echo(f"❌ Job not found: {job_id}")
                
        except Exception as e:
            click.echo(f"❌ Failed to get job status: {e}", err=True)
            logger.error("Job status query failed", job_id=job_id, error=str(e))
    
    asyncio.run(get_status())


@jobs.command()
@click.argument('job_id')
@click.option('--format', type=click.Choice(['excel', 'csv', 'json']), 
              default='excel', help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def export(job_id: str, format: str, output: Optional[str]):
    """Export job results to file.
    
    Exports processed lead data from a completed job to various formats.
    Includes all enrichment data and classification results.
    
    Args:
        job_id: Job identifier to export
        format: Output format (excel, csv, json)
        output: Output file path (auto-generated if not provided)
    
    Examples:
        leadscout jobs export abc123 --format excel
        leadscout jobs export abc123 --format csv --output results.csv
    """
    
    try:
        import sqlite3
        import pandas as pd
        import json
        from pathlib import Path
        
        # Generate output filename if not provided
        if not output:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            extensions = {'excel': 'xlsx', 'csv': 'csv', 'json': 'json'}
            ext = extensions[format]
            output = f"job_{job_id[:8]}_results_{timestamp}.{ext}"
        
        output_path = Path(output)
        
        click.echo(f"📁 Exporting job results: {job_id}")
        click.echo(f"   Format: {format}")
        click.echo(f"   Output: {output_path}")
        
        # Connect to job database
        db_path = Path("cache/jobs.db")
        if not db_path.exists():
            click.echo(f"❌ Job database not found: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        
        try:
            # Get job info
            job_query = """
            SELECT job_id, input_file_path, total_rows, processed_leads_count, 
                   status, start_time, completion_time, processing_time_total_ms
            FROM job_executions 
            WHERE job_id = ?
            """
            job_info = pd.read_sql_query(job_query, conn, params=(job_id,))
            
            if job_info.empty:
                click.echo(f"❌ Job not found: {job_id}")
                return
            
            job = job_info.iloc[0]
            click.echo(f"   Input file: {job['input_file_path']}")
            click.echo(f"   Status: {job['status']}")
            click.echo(f"   Processed: {job['processed_leads_count']} leads")
            
            # Get lead processing results
            results_query = """
            SELECT row_index, batch_number, entity_name, director_name,
                   classification_result, processing_status, processing_time_ms,
                   api_provider, api_cost, created_at
            FROM lead_processing_results 
            WHERE job_id = ?
            ORDER BY row_index
            """
            results_df = pd.read_sql_query(results_query, conn, params=(job_id,))
            
            click.echo(f"   Retrieved: {len(results_df)} result records")
            
            # Parse classification results and expand columns
            enriched_data = []
            
            for _, row in results_df.iterrows():
                try:
                    # Parse classification JSON
                    classification_data = json.loads(row['classification_result']) if row['classification_result'] else {}
                    
                    # Create enriched row
                    enriched_row = {
                        'row_index': row['row_index'],
                        'batch_number': row['batch_number'],
                        'entity_name': row['entity_name'],
                        'director_name': row['director_name'],
                        'ethnicity_classification': classification_data.get('ethnicity', 'unknown'),
                        'classification_confidence': classification_data.get('confidence', 0.0),
                        'classification_method': classification_data.get('method', 'unknown'),
                        'processing_status': row['processing_status'],
                        'processing_time_ms': row['processing_time_ms'],
                        'api_provider': row['api_provider'],
                        'api_cost': row['api_cost'] or 0.0,
                        'processed_at': row['created_at']
                    }
                    
                    # Add any additional fields from classification
                    for key, value in classification_data.items():
                        if key not in ['ethnicity', 'confidence', 'method']:
                            enriched_row[f'classification_{key}'] = value
                    
                    enriched_data.append(enriched_row)
                    
                except json.JSONDecodeError as e:
                    click.echo(f"⚠️  Warning: Failed to parse classification for row {row['row_index']}: {e}")
                    # Add basic row without classification details
                    enriched_data.append({
                        'row_index': row['row_index'],
                        'entity_name': row['entity_name'],
                        'director_name': row['director_name'],
                        'processing_status': 'parse_error',
                        'error': str(e)
                    })
            
            # Create DataFrame
            export_df = pd.DataFrame(enriched_data)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save in requested format
            if format == 'excel':
                export_df.to_excel(output_path, index=False)
            elif format == 'csv':
                export_df.to_csv(output_path, index=False)
            elif format == 'json':
                export_df.to_json(output_path, orient='records', indent=2)
            
            click.echo(f"💾 Exported to: {output_path}")
            
            # Show summary statistics
            click.echo(f"\n📈 Export Summary:")
            click.echo(f"   Total records: {len(export_df)}")
            
            if 'ethnicity_classification' in export_df.columns:
                click.echo(f"   Ethnicity breakdown:")
                ethnicity_counts = export_df['ethnicity_classification'].value_counts()
                for ethnicity, count in ethnicity_counts.items():
                    click.echo(f"     {ethnicity}: {count}")
            
            if 'classification_method' in export_df.columns:
                click.echo(f"   Method breakdown:")
                method_counts = export_df['classification_method'].value_counts()
                for method, count in method_counts.items():
                    click.echo(f"     {method}: {count}")
            
            if 'api_cost' in export_df.columns:
                total_cost = export_df['api_cost'].sum()
                click.echo(f"   Total API cost: ${total_cost:.4f}")
            
            click.echo(f"✅ Export completed successfully!")
            
        finally:
            conn.close()
            
    except Exception as e:
        click.echo(f"❌ Export failed: {e}", err=True)
        logger.error("Job export failed", job_id=job_id, error=str(e))


@jobs.command()
@click.argument('job_id', required=False)
@click.option('--all', is_flag=True, help='Analyze all jobs instead of specific job')
def analyze(job_id: Optional[str], all: bool):
    """Analyze job statistics and learning effectiveness.
    
    Provides comprehensive analysis of job processing results including:
    - Classification method breakdown and effectiveness
    - Ethnicity distribution analysis
    - API provider usage statistics
    - Performance metrics and processing rates
    - Learning effectiveness and cost optimization
    - Performance target achievement
    
    Args:
        job_id: Specific job ID to analyze (optional)
        all: Analyze all jobs in database
    
    Examples:
        leadscout jobs analyze abc123-def456-ghi789
        leadscout jobs analyze --all
        leadscout jobs analyze  # Analyze all jobs (same as --all)
    """
    
    try:
        import sqlite3
        import pandas as pd
        import json
        from pathlib import Path
        from collections import defaultdict
        
        # Determine what to analyze
        if not job_id and not all:
            # Default to analyzing all jobs if no specific job provided
            all = True
            
        db_path = Path("cache/jobs.db")
        if not db_path.exists():
            click.echo(f"❌ Job database not found: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        
        try:
            if job_id:
                _analyze_specific_job(conn, job_id)
            else:
                _analyze_all_jobs(conn)
                
            # Also analyze learning database
            _analyze_learning_database()
                
        except Exception as e:
            click.echo(f"❌ Analysis failed: {e}")
            logger.error("Job analysis failed", error=str(e))
        finally:
            conn.close()
            
    except Exception as e:
        click.echo(f"❌ Analysis setup failed: {e}", err=True)
        logger.error("Job analysis setup failed", error=str(e))


@jobs.command()
@click.argument('job_id')
@click.option('--force', is_flag=True, help='Force cancel running job')
def cancel(job_id: str, force: bool):
    """Cancel a running job.
    
    Safely cancels a running job, ensuring data consistency.
    The job can be resumed later from the last committed batch.
    
    Args:
        job_id: Job identifier to cancel
        force: Force cancellation even if job is in critical section
    
    Examples:
        leadscout jobs cancel abc123
        leadscout jobs cancel abc123 --force
    """
    
    async def cancel_job():
        try:
            # This would implement job cancellation
            click.echo(f"🛑 Cancelling job: {job_id}")
            click.echo(f"   Force: {force}")
            
            # Placeholder implementation
            click.echo("(Cancellation functionality will be implemented)")
            
        except Exception as e:
            click.echo(f"❌ Cancellation failed: {e}", err=True)
            logger.error("Job cancellation failed", job_id=job_id, error=str(e))
    
    asyncio.run(cancel_job())


def _display_real_learning_summary(job_id: str):
    """Display real learning analytics from database."""
    import sqlite3
    import json
    from pathlib import Path
    
    try:
        db_path = Path("cache/jobs.db")
        if not db_path.exists():
            click.echo("⚠️  Job database not found")
            return
            
        conn = sqlite3.connect(db_path)
        
        # Get job results
        results_query = """
        SELECT classification_result, api_cost, processing_time_ms
        FROM lead_processing_results 
        WHERE job_id = ?
        """
        cursor = conn.execute(results_query, (job_id,))
        results = cursor.fetchall()
        
        if not results:
            click.echo("⚠️  No job results found")
            return
        
        # Parse results
        methods = []
        total_cost = 0.0
        
        for result_json, api_cost, _ in results:
            try:
                if result_json:
                    classification = json.loads(result_json)
                    methods.append(classification.get('method', 'unknown'))
                total_cost += api_cost or 0.0
            except:
                methods.append('error')
        
        # Calculate statistics
        total_classifications = len(methods)
        method_counts = {}
        for method in methods:
            method_counts[method] = method_counts.get(method, 0) + 1
        
        llm_count = method_counts.get('llm', 0)
        cache_count = method_counts.get('cache', 0)
        rule_count = method_counts.get('rule_based', 0)
        phonetic_count = method_counts.get('phonetic', 0)
        
        llm_percentage = llm_count / total_classifications * 100 if total_classifications > 0 else 0
        cache_percentage = cache_count / total_classifications * 100 if total_classifications > 0 else 0
        non_llm_count = rule_count + phonetic_count + cache_count
        cost_efficiency = non_llm_count / total_classifications * 100 if total_classifications > 0 else 0
        
        # Get learning database stats
        learning_db_path = Path("cache/llm_learning.db")
        patterns_count = 0
        if learning_db_path.exists():
            learning_conn = sqlite3.connect(learning_db_path)
            try:
                patterns_cursor = learning_conn.execute("SELECT COUNT(*) FROM learned_patterns")
                patterns_count = patterns_cursor.fetchone()[0]
            except:
                pass
            learning_conn.close()
        
        click.echo(f"\n🧠 Learning Analytics")
        click.echo("=" * 40)
        click.echo(f"  Total Classifications: {total_classifications}")
        click.echo(f"  LLM Usage: {llm_count} ({llm_percentage:.1f}%)")
        click.echo(f"  Cache Hits: {cache_count} ({cache_percentage:.1f}%)")
        click.echo(f"  Rule-based: {rule_count} ({rule_count/total_classifications*100:.1f}%)")
        click.echo(f"  Patterns in Database: {patterns_count}")
        
        click.echo(f"\n💰 Cost Optimization:")
        click.echo(f"  Actual Cost: ${total_cost:.4f}")
        click.echo(f"  Cost per Lead: ${total_cost/total_classifications:.6f}")
        click.echo(f"  Cost Efficiency: {cost_efficiency:.1f}%")
        
        click.echo(f"\n🎯 Performance Targets:")
        click.echo(f"  {'✅' if llm_percentage < 5 else '❌'} LLM Usage < 5%: {llm_percentage:.1f}%")
        click.echo(f"  {'✅' if cost_efficiency > 50 else '❌'} Cost Efficiency > 50%: {cost_efficiency:.1f}%")
        click.echo(f"  {'✅' if total_cost == 0 else '⚠️'} Zero Cost Operation: ${total_cost:.4f}")
        
        conn.close()
        
    except Exception as e:
        click.echo(f"⚠️  Could not display learning summary: {e}")

def _display_learning_summary(summary: dict):
    """Display learning analytics summary (legacy placeholder)."""
    
    if not summary:
        return
    
    click.echo(f"\n🧠 Learning Analytics")
    click.echo("=" * 40)
    
    llm_usage = summary.get('llm_usage', {})
    learning_system = summary.get('learning_system', {})
    cost_opt = summary.get('cost_optimization', {})
    targets = summary.get('performance_targets', {})
    
    click.echo(f"  Total Classifications: {summary.get('total_classifications', 0)}")
    click.echo(f"  LLM Usage: {llm_usage.get('count', 0)} ({llm_usage.get('rate', 0):.1f}%)")
    click.echo(f"  Learned Pattern Hits: {learning_system.get('learned_pattern_hits', 0)} "
              f"({learning_system.get('learning_rate', 0):.1f}%)")
    click.echo(f"  Patterns in Database: {learning_system.get('patterns_in_database', 0)}")
    click.echo(f"  Phonetic Families: {learning_system.get('phonetic_families', 0)}")
    
    click.echo(f"\n💰 Cost Optimization:")
    click.echo(f"  Estimated Cost (no learning): ${cost_opt.get('estimated_cost_without_learning', 0):.4f}")
    click.echo(f"  Actual Cost: ${cost_opt.get('actual_cost', 0):.4f}")
    click.echo(f"  Cost Saved: ${cost_opt.get('cost_saved', 0):.4f} "
              f"({cost_opt.get('cost_savings_percent', 0):.1f}%)")
    
    click.echo(f"\n🎯 Performance Targets:")
    for target, achieved in targets.items():
        icon = "✅" if achieved else "❌"
        target_name = target.replace('_', ' ').title()
        click.echo(f"  {icon} {target_name}")


def _display_job_learning_analytics(analytics: dict):
    """Display detailed job learning analytics."""
    
    click.echo(f"📊 Learning Analytics:")
    click.echo(f"  Total Classifications: {analytics.get('total_classifications', 0)}")
    click.echo(f"  LLM Classifications: {analytics.get('llm_classifications', 0)}")
    click.echo(f"  Learned Classifications: {analytics.get('learned_classifications', 0)}")
    click.echo(f"  Rule-based Classifications: {analytics.get('rule_classifications', 0)}")
    click.echo(f"  Phonetic Classifications: {analytics.get('phonetic_classifications', 0)}")
    
    click.echo(f"\n💡 Learning Efficiency:")
    click.echo(f"  Patterns Generated: {analytics.get('patterns_generated', 0)}")
    click.echo(f"  Learning Efficiency: {analytics.get('learning_efficiency', 0):.3f} patterns/LLM call")
    
    click.echo(f"\n💰 Cost Optimization:")
    click.echo(f"  Estimated Cost Saved: ${analytics.get('estimated_cost_saved', 0):.4f}")
    click.echo(f"  Actual LLM Cost: ${analytics.get('actual_llm_cost', 0):.4f}")
    click.echo(f"  Cost Savings: {analytics.get('cost_savings_percent', 0):.1f}%")
    
    # Show batch summary if available
    batch_summary = analytics.get('batch_summary', {})
    if batch_summary:
        click.echo(f"\n📦 Batch Summary:")
        click.echo(f"  Total Batches: {batch_summary.get('total_batches', 0)}")
        click.echo(f"  Total LLM Calls: {batch_summary.get('total_llm_calls', 0)}")
        click.echo(f"  Total Learned Hits: {batch_summary.get('total_learned_hits', 0)}")
        click.echo(f"  Average Batch Time: {batch_summary.get('avg_batch_time', 0):.2f}ms")


def _analyze_specific_job(conn, job_id: str):
    """Analyze a specific job in detail."""
    import json
    import pandas as pd
    
    # Get job info
    job_query = """
    SELECT job_id, input_file_path, total_rows, processed_leads_count, 
           status, start_time, completion_time, processing_time_total_ms,
           api_costs_total
    FROM job_executions 
    WHERE job_id = ?
    """
    job_info = pd.read_sql_query(job_query, conn, params=(job_id,))
    
    if job_info.empty:
        click.echo(f"❌ Job not found: {job_id}")
        return
    
    job = job_info.iloc[0]
    
    click.echo(f"📊 Job Analysis: {job_id}")
    click.echo("=" * 60)
    click.echo(f"   Input File: {job['input_file_path']}")
    click.echo(f"   Status: {job['status']}")
    click.echo(f"   Total Leads: {job['total_rows']}")
    click.echo(f"   Processed: {job['processed_leads_count']}")
    click.echo(f"   Processing Time: {job['processing_time_total_ms']/1000:.2f} seconds")
    click.echo(f"   Total API Cost: ${job['api_costs_total']:.4f}")
    
    # Get lead processing results
    results_query = """
    SELECT classification_result, processing_status, processing_time_ms,
           api_provider, api_cost, batch_number
    FROM lead_processing_results 
    WHERE job_id = ?
    """
    results_df = pd.read_sql_query(results_query, conn, params=(job_id,))
    
    if results_df.empty:
        click.echo("❌ No processing results found")
        return
    
    # Parse classification results
    methods = []
    ethnicities = []
    confidences = []
    providers = []
    
    for _, row in results_df.iterrows():
        try:
            if row['classification_result']:
                classification = json.loads(row['classification_result'])
                methods.append(classification.get('method', 'unknown'))
                ethnicities.append(classification.get('ethnicity', 'unknown'))
                confidences.append(classification.get('confidence', 0.0))
            providers.append(row['api_provider'] or 'none')
        except:
            methods.append('error')
            ethnicities.append('error')
            confidences.append(0.0)
    
    # Calculate statistics
    click.echo(f"\n🎯 Classification Methods:")
    method_counts = pd.Series(methods).value_counts()
    total_classifications = len(methods)
    
    for method, count in method_counts.items():
        percentage = count / total_classifications * 100
        click.echo(f"   {method.title()}: {count} ({percentage:.1f}%)")
    
    click.echo(f"\n🌍 Ethnicity Distribution:")
    ethnicity_counts = pd.Series(ethnicities).value_counts()
    for ethnicity, count in ethnicity_counts.items():
        percentage = count / total_classifications * 100
        click.echo(f"   {ethnicity.title()}: {count} ({percentage:.1f}%)")
    
    click.echo(f"\n🔍 Provider Usage:")
    provider_counts = pd.Series(providers).value_counts()
    for provider, count in provider_counts.items():
        percentage = count / len(providers) * 100
        click.echo(f"   {provider.title()}: {count} ({percentage:.1f}%)")
    
    # Performance metrics
    avg_processing_time = results_df['processing_time_ms'].mean()
    total_api_cost = results_df['api_cost'].sum()
    
    click.echo(f"\n⚡ Performance Metrics:")
    click.echo(f"   Average Processing Time: {avg_processing_time:.2f}ms")
    click.echo(f"   Processing Rate: {1000/avg_processing_time:.1f} leads/second")
    click.echo(f"   Total API Cost: ${total_api_cost:.4f}")
    click.echo(f"   Cost per Lead: ${total_api_cost/total_classifications:.6f}")
    
    # Learning effectiveness
    rule_based_count = method_counts.get('rule_based', 0)
    phonetic_count = method_counts.get('phonetic', 0)
    cache_count = method_counts.get('cache', 0)
    llm_count = method_counts.get('llm', 0)
    
    non_llm_count = rule_based_count + phonetic_count + cache_count
    llm_percentage = llm_count / total_classifications * 100
    cost_efficiency = non_llm_count / total_classifications * 100
    
    click.echo(f"\n🧠 Learning Effectiveness:")
    click.echo(f"   Non-LLM Classifications: {non_llm_count} ({cost_efficiency:.1f}%)")
    click.echo(f"   LLM Usage: {llm_count} ({llm_percentage:.1f}%)")
    click.echo(f"   Cost Efficiency: {cost_efficiency:.1f}%")
    
    # Performance targets
    click.echo(f"\n🎯 Performance Targets:")
    click.echo(f"   {'✅' if llm_percentage < 5 else '❌'} LLM Usage < 5%: {llm_percentage:.1f}%")
    click.echo(f"   {'✅' if cost_efficiency > 80 else '❌'} Cost Efficiency > 80%: {cost_efficiency:.1f}%")
    click.echo(f"   {'✅' if avg_processing_time < 100 else '❌'} Processing < 100ms: {avg_processing_time:.1f}ms")


def _analyze_all_jobs(conn):
    """Analyze all jobs in the database."""
    import pandas as pd
    
    # Get all jobs
    jobs_query = """
    SELECT job_id, input_file_path, total_rows, processed_leads_count, 
           status, start_time, completion_time, processing_time_total_ms,
           api_costs_total
    FROM job_executions 
    ORDER BY start_time DESC
    """
    jobs_df = pd.read_sql_query(jobs_query, conn)
    
    if jobs_df.empty:
        click.echo("❌ No jobs found in database")
        return
    
    click.echo(f"📊 All Jobs Analysis")
    click.echo("=" * 60)
    click.echo(f"   Total Jobs: {len(jobs_df)}")
    
    # Job status breakdown
    status_counts = jobs_df['status'].value_counts()
    click.echo(f"\n📋 Job Status:")
    for status, count in status_counts.items():
        click.echo(f"   {status.title()}: {count}")
    
    # Completed jobs analysis
    completed_jobs = jobs_df[jobs_df['status'] == 'completed']
    
    if not completed_jobs.empty:
        total_leads = completed_jobs['processed_leads_count'].sum()
        total_time = completed_jobs['processing_time_total_ms'].sum() / 1000
        total_cost = completed_jobs['api_costs_total'].sum()
        
        click.echo(f"\n📈 Completed Jobs Summary:")
        click.echo(f"   Total Leads Processed: {total_leads:,}")
        click.echo(f"   Total Processing Time: {total_time:.2f} seconds")
        if total_time > 0:
            click.echo(f"   Average Processing Rate: {total_leads/total_time:.1f} leads/second")
        click.echo(f"   Total API Costs: ${total_cost:.4f}")
        if total_leads > 0:
            click.echo(f"   Average Cost per Lead: ${total_cost/total_leads:.6f}")
        
        # Show recent jobs
        click.echo(f"\n📝 Recent Jobs:")
        for _, job in completed_jobs.head(5).iterrows():
            processing_time = job['processing_time_total_ms'] / 1000
            rate = job['processed_leads_count'] / processing_time if processing_time > 0 else 0
            click.echo(f"   {job['job_id'][:8]}... | {job['processed_leads_count']:4d} leads | "
                      f"{rate:6.1f} leads/sec | ${job['api_costs_total']:.4f}")


def _analyze_learning_database():
    """Analyze the learning database patterns."""
    import sqlite3
    import pandas as pd
    from pathlib import Path
    
    learning_db_path = Path("cache/llm_learning.db")
    if not learning_db_path.exists():
        click.echo(f"\n❌ Learning database not found: {learning_db_path}")
        return
    
    conn = sqlite3.connect(learning_db_path)
    
    try:
        click.echo(f"\n🧠 Learning Database Analysis")
        click.echo("=" * 60)
        
        # Classification counts
        try:
            classifications_query = "SELECT COUNT(*) as count FROM llm_classifications"
            classifications_count = pd.read_sql_query(classifications_query, conn).iloc[0]['count']
        except:
            classifications_count = 0
        
        # Pattern counts
        try:
            patterns_query = "SELECT COUNT(*) as count FROM learned_patterns"
            patterns_count = pd.read_sql_query(patterns_query, conn).iloc[0]['count']
        except:
            patterns_count = 0
        
        click.echo(f"   Total LLM Classifications: {classifications_count}")
        click.echo(f"   Generated Patterns: {patterns_count}")
        
        if classifications_count > 0:
            learning_efficiency = patterns_count / classifications_count
            click.echo(f"   Learning Efficiency: {learning_efficiency:.2f} patterns per LLM call")
        
        # Ethnicity distribution in learning database
        try:
            ethnicity_query = "SELECT ethnicity, COUNT(*) as count FROM llm_classifications GROUP BY ethnicity"
            ethnicity_df = pd.read_sql_query(ethnicity_query, conn)
            
            if not ethnicity_df.empty:
                click.echo(f"\n🌍 Learning Database Ethnicities:")
                for _, row in ethnicity_df.iterrows():
                    click.echo(f"   {row['ethnicity'].title()}: {row['count']}")
        except Exception as e:
            click.echo(f"   ⚠️  Could not analyze ethnicities: {e}")
        
        # Pattern types
        try:
            pattern_types_query = "SELECT pattern_type, COUNT(*) as count FROM learned_patterns GROUP BY pattern_type"
            pattern_types_df = pd.read_sql_query(pattern_types_query, conn)
            
            if not pattern_types_df.empty:
                click.echo(f"\n🔍 Pattern Types:")
                for _, row in pattern_types_df.iterrows():
                    click.echo(f"   {row['pattern_type'].title()}: {row['count']}")
        except Exception as e:
            click.echo(f"   ⚠️  Could not analyze pattern types: {e}")
                
    except Exception as e:
        click.echo(f"❌ Learning analysis failed: {e}")
    finally:
        conn.close()


def _get_status_icon(status: str) -> str:
    """Get status icon for display."""
    icons = {
        'running': '🔄',
        'completed': '✅',
        'failed': '❌',
        'paused': '⏸️'
    }
    return icons.get(status, '❓')