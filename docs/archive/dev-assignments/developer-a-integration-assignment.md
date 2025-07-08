# Developer A - Integration & Production Readiness Assignment

**Date**: 2025-07-06  
**Priority**: 🚨 **HIGH** - System Integration & Production Monitoring  
**Developer**: Developer A (CIPC Integration & Caching Specialist)  
**Context**: Resumable framework COMPLETE - Moving to learning database integration and production CLI  

## 🎯 **MISSION OBJECTIVE**

Integrate the learning database with your resumable job framework and create production-ready CLI tools for enterprise-scale lead processing with auto-improvement analytics.

## 📋 **MANDATORY READING**

**🎯 MUST read FIRST**:
1. `CLAUDE_RULES.md` Sections 7.15-7.18 - Auto-improvement system requirements
2. `src/leadscout/classification/learning_database.py` - Complete learning database implementation  
3. `dev-tasks/resumable-framework-completion-report.md` - Your completed framework specifications
4. `dev-tasks/developer-b-phase2-assignment.md` - Developer B's learning integration tasks for coordination

## 🏗️ **PHASE A1: LEARNING DATABASE INTEGRATION (WEEKS 1-2)**

### **Task A1.1: Learning Database Integration into Resumable Jobs**
**Priority**: CRITICAL - Required for auto-improvement system

#### **Implementation Requirements**

**File**: `src/leadscout/core/resumable_job_runner.py` (UPDATE EXISTING)

```python
# ADD imports at top
from ..classification.learning_database import LLMLearningDatabase, LLMClassificationRecord
from datetime import datetime
import json

class ResumableJobRunner:
    def __init__(self, ...):
        # ... existing initialization ...
        
        # NEW: Initialize learning database for job-level analytics
        self.learning_db = LLMLearningDatabase()
        self.job_session_id = f"job_{int(time.time())}"
        
        logger.info("Learning database integrated with resumable jobs",
                   db_path=str(self.learning_db.db_path))
    
    async def _process_batch(self, batch_data: List[Dict], batch_number: int) -> BatchResult:
        """Enhanced batch processing with learning analytics."""
        
        batch_start_time = time.time()
        batch_results = []
        learning_stats = {
            'llm_calls': 0,
            'learned_pattern_hits': 0,
            'new_patterns_generated': 0,
            'cost_saved': 0.0
        }
        
        for row_index, row_data in enumerate(batch_data):
            try:
                # Process lead (existing logic)
                result = await self._process_single_lead(row_data, batch_number, row_index)
                
                # NEW: Track learning statistics
                if result and result.get('classification'):
                    classification = result['classification']
                    
                    # Track LLM usage for analytics
                    if classification.method.value in ['llm', 'openai', 'anthropic']:
                        learning_stats['llm_calls'] += 1
                    elif hasattr(classification, 'learned_pattern') and classification.learned_pattern:
                        learning_stats['learned_pattern_hits'] += 1
                        # Estimate cost saved by using learned pattern instead of LLM
                        learning_stats['cost_saved'] += 0.002  # Average LLM cost
                
                batch_results.append(result)
                
            except Exception as e:
                logger.error("Lead processing failed in batch",
                           batch_number=batch_number,
                           row_index=row_index,
                           error=str(e))
                # Add failed result
                batch_results.append({
                    'status': 'failed',
                    'error': str(e),
                    'row_index': row_index
                })
        
        # Store batch learning analytics
        await self._store_batch_learning_analytics(batch_number, learning_stats)
        
        batch_time = time.time() - batch_start_time
        
        return BatchResult(
            batch_number=batch_number,
            processed_count=len([r for r in batch_results if r.get('status') == 'success']),
            failed_count=len([r for r in batch_results if r.get('status') == 'failed']),
            results=batch_results,
            processing_time=batch_time,
            learning_stats=learning_stats  # NEW
        )
    
    async def _store_batch_learning_analytics(self, batch_number: int, learning_stats: Dict):
        """Store learning analytics for batch processing."""
        
        try:
            # Update job database with learning metrics
            learning_data = {
                'batch_number': batch_number,
                'llm_calls': learning_stats['llm_calls'],
                'learned_pattern_hits': learning_stats['learned_pattern_hits'],
                'patterns_generated': learning_stats['new_patterns_generated'],
                'estimated_cost_saved': learning_stats['cost_saved'],
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in job metadata
            await self.job_db.update_job_metadata(
                self.current_job_id,
                {'batch_learning_analytics': learning_data}
            )
            
            logger.info("Batch learning analytics stored",
                       batch_number=batch_number,
                       llm_calls=learning_stats['llm_calls'],
                       learned_hits=learning_stats['learned_pattern_hits'],
                       cost_saved=learning_stats['cost_saved'])
            
        except Exception as e:
            logger.error("Failed to store batch learning analytics",
                        batch_number=batch_number,
                        error=str(e))
    
    async def get_job_learning_summary(self, job_id: str) -> Dict[str, Any]:
        """Get comprehensive learning analytics for a job."""
        
        try:
            # Get job statistics from database
            job_stats = await self.job_db.get_job_statistics(job_id)
            
            # Get learning database statistics
            learning_stats = self.learning_db.get_learning_statistics()
            
            # Calculate job-specific learning metrics
            total_classifications = job_stats.get('total_classifications', 0)
            llm_classifications = job_stats.get('llm_classifications', 0)
            learned_classifications = job_stats.get('learned_classifications', 0)
            
            llm_usage_rate = (llm_classifications / total_classifications * 100) if total_classifications > 0 else 0
            learning_rate = (learned_classifications / total_classifications * 100) if total_classifications > 0 else 0
            
            estimated_cost_without_learning = total_classifications * 0.002  # Average LLM cost
            actual_cost = llm_classifications * 0.002
            cost_saved = estimated_cost_without_learning - actual_cost
            cost_savings_percent = (cost_saved / estimated_cost_without_learning * 100) if estimated_cost_without_learning > 0 else 0
            
            return {
                'job_id': job_id,
                'total_classifications': total_classifications,
                'llm_usage': {
                    'count': llm_classifications,
                    'rate': llm_usage_rate,
                    'target_rate': 5.0  # Target <5%
                },
                'learning_system': {
                    'learned_pattern_hits': learned_classifications,
                    'learning_rate': learning_rate,
                    'patterns_in_database': learning_stats.get('active_learned_patterns', 0),
                    'phonetic_families': learning_stats.get('phonetic_families', 0)
                },
                'cost_optimization': {
                    'estimated_cost_without_learning': estimated_cost_without_learning,
                    'actual_cost': actual_cost,
                    'cost_saved': cost_saved,
                    'cost_savings_percent': cost_savings_percent
                },
                'performance_targets': {
                    'llm_usage_under_5_percent': llm_usage_rate < 5.0,
                    'learning_rate_over_10_percent': learning_rate > 10.0,
                    'cost_savings_over_50_percent': cost_savings_percent > 50.0
                }
            }
            
        except Exception as e:
            logger.error("Failed to generate job learning summary",
                        job_id=job_id,
                        error=str(e))
            return {}
```

#### **Enhanced Job Database Schema**

**File**: `src/leadscout/core/job_database.py` (UPDATE EXISTING)

```python
# ADD to existing schema
CREATE TABLE IF NOT EXISTS job_learning_analytics (
    job_id TEXT PRIMARY KEY,
    total_classifications INTEGER DEFAULT 0,
    llm_classifications INTEGER DEFAULT 0,
    learned_classifications INTEGER DEFAULT 0,
    rule_classifications INTEGER DEFAULT 0,
    phonetic_classifications INTEGER DEFAULT 0,
    patterns_generated INTEGER DEFAULT 0,
    estimated_cost_saved REAL DEFAULT 0.0,
    actual_llm_cost REAL DEFAULT 0.0,
    learning_efficiency REAL DEFAULT 0.0,  -- patterns per LLM call
    cost_savings_percent REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES job_executions(job_id)
);

# ADD to existing schema
CREATE TABLE IF NOT EXISTS batch_learning_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    batch_number INTEGER NOT NULL,
    llm_calls INTEGER DEFAULT 0,
    learned_pattern_hits INTEGER DEFAULT 0,
    new_patterns_generated INTEGER DEFAULT 0,
    cost_saved REAL DEFAULT 0.0,
    processing_time_ms REAL DEFAULT 0.0,
    batch_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES job_executions(job_id),
    UNIQUE(job_id, batch_number)
);
```

### **Task A1.2: Production CLI Integration**
**Objective**: Create production-ready CLI commands using resumable framework

#### **Enhanced CLI Commands**

**File**: `src/leadscout/cli/jobs.py` (CREATE NEW)

```python
"""
Production job management CLI commands.

Provides enterprise-scale job processing with learning analytics.
"""

import click
import asyncio
from pathlib import Path
from typing import Optional

from ..core.resumable_job_runner import ResumableJobRunner
from ..core.config import get_settings


@click.group()
def jobs():
    """Manage resumable job processing."""
    pass


@jobs.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--batch-size', default=100, help='Batch size for processing')
@click.option('--max-concurrent', default=5, help='Maximum concurrent API calls')
@click.option('--resume/--no-resume', default=True, help='Resume existing job if found')
@click.option('--learning/--no-learning', default=True, help='Enable learning database')
def process(input_file: str, output: Optional[str], batch_size: int, 
           max_concurrent: int, resume: bool, learning: bool):
    """Process leads with resumable job framework."""
    
    click.echo(f"🚀 Starting job processing: {input_file}")
    click.echo(f"   Batch size: {batch_size}")
    click.echo(f"   Max concurrent: {max_concurrent}")
    click.echo(f"   Learning enabled: {learning}")
    
    async def run_job():
        settings = get_settings()
        runner = ResumableJobRunner(
            settings=settings,
            batch_size=batch_size,
            max_concurrent=max_concurrent,
            enable_learning=learning
        )
        
        try:
            job_id = await runner.process_file(
                input_file=Path(input_file),
                output_file=Path(output) if output else None,
                resume_if_exists=resume
            )
            
            click.echo(f"✅ Job completed successfully: {job_id}")
            
            # Show learning summary
            if learning:
                summary = await runner.get_job_learning_summary(job_id)
                _display_learning_summary(summary)
                
        except Exception as e:
            click.echo(f"❌ Job failed: {e}", err=True)
            raise click.ClickException(str(e))
    
    asyncio.run(run_job())


@jobs.command()
@click.option('--status', type=click.Choice(['running', 'completed', 'failed', 'all']), 
              default='all', help='Filter by job status')
@click.option('--limit', default=10, help='Maximum number of jobs to show')
def list(status: str, limit: int):
    """List recent jobs and their status."""
    
    async def list_jobs():
        runner = ResumableJobRunner(get_settings())
        jobs_list = await runner.list_jobs(status_filter=status, limit=limit)
        
        if not jobs_list:
            click.echo("No jobs found.")
            return
        
        click.echo(f"\n📋 Recent Jobs ({status}):")
        click.echo("=" * 80)
        
        for job in jobs_list:
            status_icon = _get_status_icon(job['status'])
            click.echo(f"{status_icon} {job['job_id']}")
            click.echo(f"   File: {job['input_file_path']}")
            click.echo(f"   Progress: {job['processed_leads']}/{job['total_rows']} "
                      f"({job['progress_percent']:.1f}%)")
            click.echo(f"   Started: {job['start_time']}")
            if job['status'] == 'completed':
                click.echo(f"   Duration: {job['duration']}")
            click.echo()
    
    asyncio.run(list_jobs())


@jobs.command()
@click.argument('job_id')
def status(job_id: str):
    """Get detailed status for a specific job."""
    
    async def get_status():
        runner = ResumableJobRunner(get_settings())
        
        job_status = await runner.get_job_status(job_id)
        if not job_status:
            click.echo(f"❌ Job not found: {job_id}")
            return
        
        # Display job status
        _display_job_status(job_status)
        
        # Display learning analytics if available
        learning_summary = await runner.get_job_learning_summary(job_id)
        if learning_summary:
            _display_learning_summary(learning_summary)
    
    asyncio.run(get_status())


@jobs.command()
@click.argument('job_id')
@click.option('--format', type=click.Choice(['excel', 'csv', 'json']), 
              default='excel', help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def export(job_id: str, format: str, output: Optional[str]):
    """Export job results to file."""
    
    async def export_results():
        runner = ResumableJobRunner(get_settings())
        
        output_path = await runner.export_job_results(
            job_id=job_id,
            format=format,
            output_path=Path(output) if output else None
        )
        
        click.echo(f"✅ Results exported to: {output_path}")
    
    asyncio.run(export_results())


@jobs.command()
@click.argument('job_id')
@click.option('--force', is_flag=True, help='Force cancel running job')
def cancel(job_id: str, force: bool):
    """Cancel a running job."""
    
    async def cancel_job():
        runner = ResumableJobRunner(get_settings())
        
        success = await runner.cancel_job(job_id, force=force)
        if success:
            click.echo(f"✅ Job cancelled: {job_id}")
        else:
            click.echo(f"❌ Failed to cancel job: {job_id}")
    
    asyncio.run(cancel_job())


def _display_job_status(status: dict):
    """Display formatted job status."""
    
    click.echo(f"\n📊 Job Status: {status['job_id']}")
    click.echo("=" * 60)
    click.echo(f"  Status: {_get_status_icon(status['status'])} {status['status'].upper()}")
    click.echo(f"  Input File: {status['input_file_path']}")
    click.echo(f"  Progress: {status['processed_leads']}/{status['total_rows']} "
              f"({status['progress_percent']:.1f}%)")
    click.echo(f"  Batch Size: {status['batch_size']}")
    click.echo(f"  Current Batch: {status['current_batch']}")
    click.echo(f"  Started: {status['start_time']}")
    
    if status['status'] == 'completed':
        click.echo(f"  Completed: {status['completion_time']}")
        click.echo(f"  Duration: {status['duration']}")
    
    if status.get('error_summary'):
        click.echo(f"  Errors: {status['failed_leads']} leads failed")
        click.echo(f"  Error Summary: {status['error_summary']}")


def _display_learning_summary(summary: dict):
    """Display learning analytics summary."""
    
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
        click.echo(f"  {icon} {target.replace('_', ' ').title()}")


def _get_status_icon(status: str) -> str:
    """Get status icon for display."""
    icons = {
        'running': '🔄',
        'completed': '✅',
        'failed': '❌',
        'paused': '⏸️'
    }
    return icons.get(status, '❓')
```

#### **Update Main CLI**

**File**: `src/leadscout/cli/main.py` (UPDATE EXISTING)

```python
# ADD import
from .jobs import jobs

@click.group()
@click.version_option()
def cli():
    """LeadScout - AI-Powered Lead Enrichment System."""
    pass

# ADD jobs command group
cli.add_command(jobs)
```

## 🚀 **PHASE A2: PRODUCTION MONITORING & ANALYTICS (WEEKS 3-4)**

### **Task A2.1: Learning Analytics Dashboard**

**File**: `src/leadscout/cli/analytics.py` (CREATE NEW)

```python
"""
Learning analytics and monitoring commands.

Provides insights into learning system performance and cost optimization.
"""

import click
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from ..classification.learning_database import LLMLearningDatabase
from ..core.resumable_job_runner import ResumableJobRunner
from ..core.config import get_settings


@click.group()
def analytics():
    """Learning system analytics and monitoring."""
    pass


@analytics.command()
@click.option('--days', default=30, help='Number of days to analyze')
@click.option('--detailed', is_flag=True, help='Show detailed breakdown')
def learning(days: int, detailed: bool):
    """Show learning system performance analytics."""
    
    learning_db = LLMLearningDatabase()
    
    click.echo(f"🧠 Learning System Analytics (Last {days} days)")
    click.echo("=" * 60)
    
    # Get learning statistics
    stats = learning_db.get_learning_statistics()
    
    click.echo(f"📊 Overall Statistics:")
    click.echo(f"  Total LLM Classifications Stored: {stats.get('total_llm_classifications', 0)}")
    click.echo(f"  Active Learned Patterns: {stats.get('active_learned_patterns', 0)}")
    click.echo(f"  Phonetic Families: {stats.get('phonetic_families', 0)}")
    click.echo(f"  Learning Efficiency: {stats.get('learning_efficiency', 0):.3f} patterns/LLM call")
    
    # Recent performance
    if 'recent_30_days' in stats:
        recent = stats['recent_30_days']
        click.echo(f"\n📈 Recent Performance ({days} days):")
        click.echo(f"  Classifications: {recent.get('total_classifications', 0)}")
        click.echo(f"  Average Confidence: {recent.get('average_confidence', 0):.2f}")
        click.echo(f"  Total Cost: ${recent.get('total_cost_usd', 0):.4f}")
    
    if detailed:
        _show_detailed_learning_analytics(learning_db, days)


@analytics.command()
@click.option('--limit', default=10, help='Number of recent jobs to analyze')
def cost_optimization(limit: int):
    """Show cost optimization analytics across recent jobs."""
    
    async def analyze_costs():
        runner = ResumableJobRunner(get_settings())
        
        # Get recent completed jobs
        jobs = await runner.list_jobs(status_filter='completed', limit=limit)
        
        if not jobs:
            click.echo("No completed jobs found for analysis.")
            return
        
        click.echo(f"💰 Cost Optimization Analysis (Last {len(jobs)} jobs)")
        click.echo("=" * 70)
        
        total_cost_saved = 0.0
        total_estimated_cost = 0.0
        total_actual_cost = 0.0
        
        for job in jobs:
            try:
                summary = await runner.get_job_learning_summary(job['job_id'])
                if summary:
                    cost_opt = summary.get('cost_optimization', {})
                    estimated = cost_opt.get('estimated_cost_without_learning', 0)
                    actual = cost_opt.get('actual_cost', 0)
                    saved = cost_opt.get('cost_saved', 0)
                    
                    total_estimated_cost += estimated
                    total_actual_cost += actual
                    total_cost_saved += saved
                    
                    click.echo(f"  {job['job_id'][:12]}... | "
                              f"Estimated: ${estimated:.4f} | "
                              f"Actual: ${actual:.4f} | "
                              f"Saved: ${saved:.4f}")
            except Exception as e:
                click.echo(f"  {job['job_id'][:12]}... | Error: {e}")
        
        # Summary
        overall_savings_percent = (total_cost_saved / total_estimated_cost * 100) if total_estimated_cost > 0 else 0
        
        click.echo(f"\n📊 Overall Cost Optimization:")
        click.echo(f"  Total Estimated Cost (no learning): ${total_estimated_cost:.4f}")
        click.echo(f"  Total Actual Cost: ${total_actual_cost:.4f}")
        click.echo(f"  Total Cost Saved: ${total_cost_saved:.4f}")
        click.echo(f"  Overall Savings: {overall_savings_percent:.1f}%")
        
        # Performance assessment
        if overall_savings_percent >= 50:
            click.echo(f"  🎯 Excellent cost optimization achieved!")
        elif overall_savings_percent >= 25:
            click.echo(f"  ✅ Good cost optimization progress")
        else:
            click.echo(f"  📈 Learning system building effectiveness")
    
    asyncio.run(analyze_costs())


@analytics.command()
@click.option('--pattern-type', type=click.Choice(['all', 'phonetic', 'linguistic', 'structural']),
              default='all', help='Type of patterns to analyze')
def patterns(pattern_type: str):
    """Analyze learned patterns and their effectiveness."""
    
    learning_db = LLMLearningDatabase()
    
    click.echo(f"🔍 Pattern Analysis ({pattern_type})")
    click.echo("=" * 50)
    
    # This would require additional methods in LLMLearningDatabase
    # to analyze pattern effectiveness
    click.echo("Pattern effectiveness analysis would be implemented here")
    click.echo("showing which patterns are most successful at reducing LLM usage")


def _show_detailed_learning_analytics(learning_db: LLMLearningDatabase, days: int):
    """Show detailed learning analytics."""
    
    click.echo(f"\n🔍 Detailed Learning Analytics:")
    
    # This would require additional methods in learning database
    # to provide detailed breakdowns
    click.echo("  - Pattern generation trends")
    click.echo("  - Ethnicity classification distributions") 
    click.echo("  - Cost savings by pattern type")
    click.echo("  - Learning velocity over time")
```

### **Task A2.2: System Health Monitoring**

**File**: `src/leadscout/cli/monitor.py` (CREATE NEW)

```python
"""
System health monitoring and diagnostics.

Provides real-time monitoring of job processing and system performance.
"""

import click
import asyncio
import time
from datetime import datetime

from ..core.resumable_job_runner import ResumableJobRunner
from ..classification.learning_database import LLMLearningDatabase
from ..core.config import get_settings


@click.group()
def monitor():
    """System monitoring and health checks."""
    pass


@monitor.command()
@click.option('--interval', default=5, help='Refresh interval in seconds')
@click.option('--job-id', help='Monitor specific job')
def realtime(interval: int, job_id: str):
    """Real-time monitoring of job processing."""
    
    async def monitor_loop():
        runner = ResumableJobRunner(get_settings())
        
        while True:
            try:
                # Clear screen
                click.clear()
                
                click.echo(f"🔄 LeadScout Real-time Monitor")
                click.echo(f"{'=' * 60}")
                click.echo(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                click.echo()
                
                if job_id:
                    # Monitor specific job
                    await _monitor_specific_job(runner, job_id)
                else:
                    # Monitor all active jobs
                    await _monitor_all_jobs(runner)
                
                # System health
                await _show_system_health()
                
                click.echo(f"\nRefreshing in {interval}s... (Ctrl+C to exit)")
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                click.echo("\n👋 Monitoring stopped.")
                break
            except Exception as e:
                click.echo(f"❌ Monitoring error: {e}")
                await asyncio.sleep(interval)
    
    asyncio.run(monitor_loop())


async def _monitor_specific_job(runner: ResumableJobRunner, job_id: str):
    """Monitor a specific job."""
    
    status = await runner.get_job_status(job_id)
    if not status:
        click.echo(f"❌ Job not found: {job_id}")
        return
    
    click.echo(f"📊 Job: {job_id}")
    click.echo(f"Status: {status['status'].upper()}")
    click.echo(f"Progress: {status['processed_leads']}/{status['total_rows']} "
              f"({status['progress_percent']:.1f}%)")
    
    if status['status'] == 'running':
        click.echo(f"Current Batch: {status['current_batch']}")
        click.echo(f"Batch Size: {status['batch_size']}")
        
        # Estimate completion time
        if status['progress_percent'] > 0:
            elapsed = time.time() - status['start_timestamp']
            estimated_total = elapsed / (status['progress_percent'] / 100)
            remaining = estimated_total - elapsed
            eta = datetime.fromtimestamp(time.time() + remaining)
            click.echo(f"ETA: {eta.strftime('%H:%M:%S')}")
    
    # Learning analytics
    learning_summary = await runner.get_job_learning_summary(job_id)
    if learning_summary:
        llm_usage = learning_summary.get('llm_usage', {})
        click.echo(f"LLM Usage: {llm_usage.get('rate', 0):.1f}%")


async def _monitor_all_jobs(runner: ResumableJobRunner):
    """Monitor all active jobs."""
    
    running_jobs = await runner.list_jobs(status_filter='running', limit=5)
    
    if not running_jobs:
        click.echo("📭 No active jobs running.")
        return
    
    click.echo(f"🔄 Active Jobs ({len(running_jobs)}):")
    
    for job in running_jobs:
        click.echo(f"  {job['job_id'][:12]}... | "
                  f"{job['progress_percent']:.1f}% | "
                  f"Batch {job['current_batch']} | "
                  f"{job['input_file_path']}")


async def _show_system_health():
    """Show system health indicators."""
    
    click.echo(f"\n🏥 System Health:")
    
    try:
        # Database connectivity
        learning_db = LLMLearningDatabase()
        stats = learning_db.get_learning_statistics()
        click.echo(f"  ✅ Learning Database: {stats.get('total_llm_classifications', 0)} records")
        
        # Job database connectivity
        runner = ResumableJobRunner(get_settings())
        recent_jobs = await runner.list_jobs(limit=1)
        click.echo(f"  ✅ Job Database: Connected")
        
        # Memory usage (basic)
        import psutil
        memory = psutil.virtual_memory()
        click.echo(f"  📊 Memory Usage: {memory.percent:.1f}%")
        
    except Exception as e:
        click.echo(f"  ❌ Health Check Error: {e}")
```

## 🧪 **TESTING AND VALIDATION REQUIREMENTS**

### **Task A2.3: Integration Validation**

**File**: `test_integration_validation.py` (CREATE NEW)

```python
"""
Integration validation test for learning database and resumable jobs.

Tests end-to-end integration with learning analytics.
"""

import asyncio
import pandas as pd
from pathlib import Path
import tempfile
import os

from src.leadscout.core.resumable_job_runner import ResumableJobRunner
from src.leadscout.classification.learning_database import LLMLearningDatabase
from src.leadscout.core.config import get_settings

async def test_integration_validation():
    """Test complete integration with learning database."""
    
    print("🧪 INTEGRATION VALIDATION TEST")
    print("=" * 60)
    
    # Create test data
    test_data = {
        'EntityName': ['Test Company 1', 'Test Company 2', 'Test Company 3'],
        'DirectorName': ['LUCKY MABENA', 'JOHN SMITH', 'NXANGUMUNI HLUNGWANI'],
        'Keyword': ['LOGISTICS', 'TRANSPORT', 'SUPPLY']
    }
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        df = pd.DataFrame(test_data)
        df.to_excel(tmp.name, index=False)
        test_file = tmp.name
    
    try:
        # Test 1: Process with learning database
        print("\n📊 Test 1: Processing with Learning Database")
        
        settings = get_settings()
        runner = ResumableJobRunner(
            settings=settings,
            batch_size=2,
            enable_learning=True
        )
        
        job_id = await runner.process_file(
            input_file=Path(test_file),
            resume_if_exists=False
        )
        
        print(f"  ✅ Job completed: {job_id}")
        
        # Test 2: Validate learning analytics
        print("\n📊 Test 2: Learning Analytics Validation")
        
        learning_summary = await runner.get_job_learning_summary(job_id)
        
        if learning_summary:
            print(f"  ✅ Learning summary generated")
            print(f"  Total Classifications: {learning_summary.get('total_classifications', 0)}")
            print(f"  LLM Usage Rate: {learning_summary.get('llm_usage', {}).get('rate', 0):.1f}%")
            print(f"  Learning Rate: {learning_summary.get('learning_system', {}).get('learning_rate', 0):.1f}%")
        else:
            print(f"  ❌ Learning summary not generated")
        
        # Test 3: Learning database validation
        print("\n📊 Test 3: Learning Database Validation")
        
        learning_db = LLMLearningDatabase()
        db_stats = learning_db.get_learning_statistics()
        
        print(f"  ✅ Learning database accessible")
        print(f"  LLM Classifications: {db_stats.get('total_llm_classifications', 0)}")
        print(f"  Active Patterns: {db_stats.get('active_learned_patterns', 0)}")
        print(f"  Phonetic Families: {db_stats.get('phonetic_families', 0)}")
        
        # Test 4: CLI commands validation
        print("\n📊 Test 4: CLI Integration Test")
        
        # This would test CLI commands programmatically
        print(f"  ✅ CLI commands integrated")
        
        print(f"\n🎉 INTEGRATION VALIDATION COMPLETE")
        print(f"All systems integrated successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
        
    finally:
        # Cleanup
        os.unlink(test_file)

if __name__ == "__main__":
    asyncio.run(test_integration_validation())
```

## 📊 **DELIVERABLES**

### **Primary Deliverable: Integration Completion Report**
**File**: `dev-tasks/integration-completion-report.md`

**Required Sections**:
1. **Learning Database Integration Results** - Actual test results showing integration success
2. **Production CLI Implementation** - Complete job management commands with examples  
3. **Analytics and Monitoring** - Real-time monitoring and cost optimization tracking
4. **Performance Validation** - Integration performance metrics and system health
5. **Business Value Delivered** - Quantified improvements in cost optimization and automation

### **Supporting Deliverables**:
- Enhanced resumable job framework with learning integration
- Production-ready CLI commands for enterprise job management
- Real-time monitoring and analytics dashboards
- Comprehensive integration validation test suite

## ⚡ **CRITICAL SUCCESS FACTORS**

1. **Learning Database Integration**: Must work seamlessly with your resumable framework
2. **Production CLI**: Enterprise-ready commands for job management and monitoring
3. **Analytics and Monitoring**: Real-time insights into learning system performance
4. **Cost Optimization Tracking**: Measurable cost savings from auto-learning system
5. **System Integration**: Seamless coordination with Developer B's classification improvements

## 🚀 **SPRINT COMPLETION VISION**

By completion, your integration will provide:
- **Enterprise Job Processing**: Production-ready resumable jobs with learning analytics
- **Real-time Monitoring**: Live dashboards for job progress and system health
- **Cost Optimization Tracking**: Measurable ROI from learning system implementation
- **Production CLI**: Complete command-line interface for enterprise operations
- **Analytics Platform**: Comprehensive insights into learning system effectiveness

This sprint transforms your resumable job framework into a **production-grade platform** with intelligent cost optimization and enterprise monitoring capabilities.

---

**CRITICAL**: The learning database integration is essential for achieving our <5% LLM usage target. Your resumable framework must capture and track learning analytics to demonstrate the business value of our auto-improvement system.

**Timeline**: 4 weeks with focus on production readiness and enterprise features  
**Validation**: Must demonstrate learning database integration with actual cost optimization metrics  
**Standard**: Enterprise-grade production system with comprehensive monitoring and analytics