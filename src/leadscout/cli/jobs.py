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
    
    async def list_jobs():
        try:
            from ..core.job_database import JobDatabase
            
            job_db = JobDatabase()
            # This would need to be implemented in JobDatabase
            # jobs_list = await job_db.list_jobs(status_filter=status, limit=limit)
            
            # For now, show placeholder
            click.echo(f"\n📋 Recent Jobs ({status}):")
            click.echo("=" * 80)
            click.echo("(Job listing functionality will be implemented after database methods are added)")
            
        except Exception as e:
            click.echo(f"❌ Failed to list jobs: {e}", err=True)
            logger.error("Job listing failed", error=str(e))
    
    asyncio.run(list_jobs())


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
    
    async def export_results():
        try:
            # This would implement result export functionality
            click.echo(f"📁 Exporting job results: {job_id}")
            click.echo(f"   Format: {format}")
            click.echo(f"   Output: {output or 'auto-generated'}")
            
            # Placeholder implementation
            click.echo("(Export functionality will be implemented)")
            
        except Exception as e:
            click.echo(f"❌ Export failed: {e}", err=True)
            logger.error("Job export failed", job_id=job_id, error=str(e))
    
    asyncio.run(export_results())


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


def _get_status_icon(status: str) -> str:
    """Get status icon for display."""
    icons = {
        'running': '🔄',
        'completed': '✅',
        'failed': '❌',
        'paused': '⏸️'
    }
    return icons.get(status, '❓')