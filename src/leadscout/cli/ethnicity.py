"""
Ethnicity confirmation CLI commands.

Provides ethnicity confirmation workflow management for dialler teams with:
- Excel confirmation upload processing
- Individual and bulk confirmation commands
- Status reporting and analytics
- Learning system integration

Key Features:
- Comprehensive Excel validation with detailed error reporting
- Precise record matching using source tracking
- Canonical ethnicity validation
- Bulk processing with transaction safety
- Integration with spatial learning system

Commands:
- upload-confirmations: Process Excel files with confirmed ethnicities
- confirm: Single ethnicity confirmation
- bulk-confirm: Bulk confirmations from CSV
- status: Job confirmation status and analytics

Usage:
    leadscout ethnicity upload-confirmations --file confirmed.xlsx --job-id abc123
    leadscout ethnicity confirm --job-id abc123 --row-number 25 --ethnicity "African"
    leadscout ethnicity status abc123
"""

import click
import asyncio
from pathlib import Path
from typing import Optional
import structlog

from ..core.ethnicity_confirmation_uploader import EthnicityConfirmationUploader
from ..core.ethnicity_confirmation_database import EthnicityConfirmationDatabase

logger = structlog.get_logger(__name__)


@click.group()
def ethnicity():
    """Manage ethnicity confirmation workflow for dialler teams."""
    pass


@ethnicity.command("upload-confirmations")
@click.option('--file', '-f', 'file_path', type=click.Path(exists=True), required=True,
              help='Excel file with confirmed ethnicities')
@click.option('--job-id', '-j', required=True,
              help='Job ID to associate confirmations with')
@click.option('--validate-only', is_flag=True,
              help='Validate file without uploading confirmations')
@click.option('--skip-duplicates', is_flag=True,
              help='Skip records that are already confirmed')
@click.option('--force', is_flag=True,
              help='Force upload even if validation warnings exist')
def upload_confirmations(file_path: str, job_id: str, validate_only: bool,
                        skip_duplicates: bool, force: bool):
    """Upload ethnicity confirmations from Excel file.
    
    This command processes Excel files filled by the dialler team with confirmed
    ethnicities and uploads them to the learning system.
    
    The Excel file must contain these columns:
    - source_row_number: Original row number for precise matching
    - DirectorName: Director name for validation
    - director_ethnicity: AI-predicted ethnicity
    - confirmed_ethnicity: Human-confirmed ethnicity (required)
    - confirmation_notes: Optional notes from dialler team
    
    Args:
        file_path: Path to Excel file with confirmations
        job_id: Job ID to associate confirmations with
        validate_only: Only validate the file, don't upload
        skip_duplicates: Skip records already confirmed
        force: Force upload despite validation warnings
    
    Examples:
        leadscout ethnicity upload-confirmations -f confirmed_leads.xlsx -j job_abc123
        leadscout ethnicity upload-confirmations -f leads.xlsx -j abc123 --validate-only
        leadscout ethnicity upload-confirmations -f leads.xlsx -j abc123 --skip-duplicates
    """
    
    click.echo(f"🔄 Processing ethnicity confirmations: {file_path}")
    click.echo(f"   Job ID: {job_id}")
    click.echo(f"   Mode: {'Validation only' if validate_only else 'Upload confirmations'}")
    if skip_duplicates:
        click.echo(f"   Skip duplicates: Enabled")
    if force:
        click.echo(f"   Force mode: Enabled")
    
    async def run_upload():
        try:
            # Initialize uploader
            uploader = EthnicityConfirmationUploader()
            
            # Upload or validate confirmations
            result = await uploader.upload_confirmations_from_excel(
                file_path=Path(file_path),
                job_id=job_id,
                validate_only=validate_only,
                skip_duplicates=skip_duplicates,
                force=force
            )
            
            # Display results
            if validate_only:
                click.echo(f"\n📋 Validation Results:")
            else:
                click.echo(f"\n📊 Upload Results:")
            
            click.echo(f"   Total records processed: {result['total_records']}")
            click.echo(f"   Valid confirmations: {result['valid_confirmations']}")
            click.echo(f"   Invalid records: {result['invalid_records']}")
            
            if result.get('warnings'):
                click.echo(f"   Warnings: {len(result['warnings'])}")
                for warning in result['warnings'][:5]:  # Show first 5 warnings
                    click.echo(f"     - {warning}")
                if len(result['warnings']) > 5:
                    click.echo(f"     ... and {len(result['warnings']) - 5} more warnings")
            
            if result.get('errors'):
                click.echo(f"   Errors: {len(result['errors'])}")
                for error in result['errors'][:5]:  # Show first 5 errors
                    click.echo(f"     - {error}")
                if len(result['errors']) > 5:
                    click.echo(f"     ... and {len(result['errors']) - 5} more errors")
            
            if not validate_only and result['valid_confirmations'] > 0:
                click.echo(f"   Successfully uploaded: {result['uploaded_count']} confirmations")
                click.echo(f"   Learning patterns updated: {result.get('learning_patterns_updated', 0)}")
            
            # Show status
            if result['invalid_records'] == 0 and not result.get('errors'):
                click.echo(f"✅ {'Validation' if validate_only else 'Upload'} completed successfully!")
            elif result['valid_confirmations'] > 0:
                click.echo(f"⚠️  {'Validation' if validate_only else 'Upload'} completed with warnings")
            else:
                click.echo(f"❌ {'Validation' if validate_only else 'Upload'} failed")
                
        except Exception as e:
            click.echo(f"❌ Upload failed: {e}")
            logger.error("Confirmation upload failed",
                        file_path=file_path,
                        job_id=job_id,
                        error=str(e))
    
    # Run async upload
    asyncio.run(run_upload())


@ethnicity.command("confirm")
@click.option('--job-id', '-j', required=True,
              help='Job ID containing the lead to confirm')
@click.option('--row-number', '-r', type=int, required=True,
              help='Source row number of the lead to confirm')
@click.option('--ethnicity', '-e', required=True,
              help='Confirmed ethnicity (must be from canonical list)')
@click.option('--notes', '-n', default='',
              help='Optional confirmation notes')
@click.option('--director-name', '-d',
              help='Director name for validation (optional)')
def confirm_single(job_id: str, row_number: int, ethnicity: str,
                  notes: str, director_name: Optional[str]):
    """Confirm ethnicity for a single lead record.
    
    This command allows manual confirmation of a single lead's ethnicity
    using the job ID and source row number for precise identification.
    
    Args:
        job_id: Job ID containing the lead
        row_number: Source row number (1-based Excel row)
        ethnicity: Confirmed ethnicity from canonical list
        notes: Optional confirmation notes
        director_name: Director name for validation
    
    Examples:
        leadscout ethnicity confirm -j abc123 -r 25 -e "African"
        leadscout ethnicity confirm -j abc123 -r 10 -e "White" -n "High confidence"
        leadscout ethnicity confirm -j abc123 -r 5 -e "Indian" -d "Raj Patel"
    """
    
    click.echo(f"🔄 Confirming ethnicity for lead:")
    click.echo(f"   Job ID: {job_id}")
    click.echo(f"   Row number: {row_number}")
    click.echo(f"   Confirmed ethnicity: {ethnicity}")
    if notes:
        click.echo(f"   Notes: {notes}")
    if director_name:
        click.echo(f"   Director name: {director_name}")
    
    async def run_confirmation():
        try:
            # Initialize uploader
            uploader = EthnicityConfirmationUploader()
            
            # Create single confirmation
            result = await uploader.confirm_single_lead(
                job_id=job_id,
                source_row_number=row_number,
                confirmed_ethnicity=ethnicity,
                confirmation_notes=notes,
                director_name_validation=director_name
            )
            
            if result['success']:
                click.echo(f"✅ Ethnicity confirmation successful!")
                click.echo(f"   Confirmation ID: {result['confirmation_id']}")
                if result.get('previous_prediction'):
                    prev = result['previous_prediction']
                    click.echo(f"   Previous AI prediction: {prev['ethnicity']} (confidence: {prev['confidence']:.2f})")
                if result.get('learning_updated'):
                    click.echo(f"   Learning patterns updated: Yes")
            else:
                click.echo(f"❌ Confirmation failed: {result['error']}")
                
        except Exception as e:
            click.echo(f"❌ Confirmation failed: {e}")
            logger.error("Single confirmation failed",
                        job_id=job_id,
                        row_number=row_number,
                        error=str(e))
    
    # Run async confirmation
    asyncio.run(run_confirmation())


@ethnicity.command("bulk-confirm")
@click.option('--csv', '-c', 'csv_path', type=click.Path(exists=True), required=True,
              help='CSV file with bulk confirmations')
@click.option('--validate-only', is_flag=True,
              help='Validate CSV without uploading confirmations')
def bulk_confirm(csv_path: str, validate_only: bool):
    """Bulk confirm ethnicities from CSV file.
    
    This command processes CSV files with bulk ethnicity confirmations.
    Useful for batch processing and integration with external systems.
    
    The CSV file must contain these columns:
    - job_id: Job ID containing the lead
    - source_row_number: Original row number
    - director_name: Director name for validation
    - confirmed_ethnicity: Confirmed ethnicity
    - confirmation_notes: Optional notes
    
    Args:
        csv_path: Path to CSV file with confirmations
        validate_only: Only validate the file, don't upload
    
    Examples:
        leadscout ethnicity bulk-confirm -c confirmations.csv
        leadscout ethnicity bulk-confirm -c data.csv --validate-only
    """
    
    click.echo(f"🔄 Processing bulk confirmations: {csv_path}")
    click.echo(f"   Mode: {'Validation only' if validate_only else 'Upload confirmations'}")
    
    async def run_bulk_confirmation():
        try:
            # Initialize uploader
            uploader = EthnicityConfirmationUploader()
            
            # Process bulk confirmations
            result = await uploader.bulk_confirm_from_csv(
                csv_path=Path(csv_path),
                validate_only=validate_only
            )
            
            # Display results
            click.echo(f"\n📊 Bulk Confirmation Results:")
            click.echo(f"   Total records processed: {result['total_records']}")
            click.echo(f"   Valid confirmations: {result['valid_confirmations']}")
            click.echo(f"   Invalid records: {result['invalid_records']}")
            
            if result.get('errors'):
                click.echo(f"   Errors: {len(result['errors'])}")
                for error in result['errors'][:3]:  # Show first 3 errors
                    click.echo(f"     - {error}")
                if len(result['errors']) > 3:
                    click.echo(f"     ... and {len(result['errors']) - 3} more errors")
            
            if not validate_only and result['valid_confirmations'] > 0:
                click.echo(f"   Successfully uploaded: {result['uploaded_count']} confirmations")
                click.echo(f"   Learning patterns updated: {result.get('learning_patterns_updated', 0)}")
            
            # Show status
            if result['invalid_records'] == 0:
                click.echo(f"✅ Bulk {'validation' if validate_only else 'confirmation'} completed successfully!")
            elif result['valid_confirmations'] > 0:
                click.echo(f"⚠️  Bulk {'validation' if validate_only else 'confirmation'} completed with warnings")
            else:
                click.echo(f"❌ Bulk {'validation' if validate_only else 'confirmation'} failed")
                
        except Exception as e:
            click.echo(f"❌ Bulk confirmation failed: {e}")
            logger.error("Bulk confirmation failed",
                        csv_path=csv_path,
                        error=str(e))
    
    # Run async bulk confirmation
    asyncio.run(run_bulk_confirmation())


@ethnicity.command("status")
@click.argument('job_id')
@click.option('--detailed', '-d', is_flag=True,
              help='Show detailed confirmation breakdown')
@click.option('--export', '-e', type=click.Path(),
              help='Export status report to file')
def confirmation_status(job_id: str, detailed: bool, export: Optional[str]):
    """Show confirmation status and analytics for a job.
    
    This command provides comprehensive confirmation statistics including:
    - Confirmation coverage (confirmed vs total leads)
    - Ethnicity distribution of confirmations
    - Confidence accuracy validation (AI vs confirmed)
    - Learning system integration status
    
    Args:
        job_id: Job ID to analyze
        detailed: Show detailed breakdown by ethnicity
        export: Export status report to file
    
    Examples:
        leadscout ethnicity status abc123
        leadscout ethnicity status abc123 --detailed
        leadscout ethnicity status abc123 --export status_report.json
    """
    
    click.echo(f"📊 Ethnicity Confirmation Status: {job_id}")
    
    async def run_status():
        try:
            # Initialize database
            db = EthnicityConfirmationDatabase()
            
            # Get comprehensive status
            status = await db.get_confirmation_status(job_id, detailed=detailed)
            
            if not status:
                click.echo(f"❌ No status found for job: {job_id}")
                return
            
            # Display overview
            click.echo(f"\n📋 Overview:")
            click.echo(f"   Total leads processed: {status['total_leads']}")
            click.echo(f"   Confirmed leads: {status['confirmed_leads']}")
            click.echo(f"   Confirmation coverage: {status['confirmation_percentage']:.1f}%")
            click.echo(f"   Pending confirmations: {status['pending_confirmations']}")
            
            # Display accuracy metrics
            if status.get('accuracy_metrics'):
                metrics = status['accuracy_metrics']
                click.echo(f"\n🎯 Accuracy Metrics:")
                click.echo(f"   AI-Human agreement: {metrics['agreement_percentage']:.1f}%")
                click.echo(f"   High confidence correct: {metrics['high_confidence_correct']:.1f}%")
                click.echo(f"   Low confidence correct: {metrics['low_confidence_correct']:.1f}%")
            
            # Display ethnicity distribution
            if status.get('ethnicity_distribution'):
                click.echo(f"\n🏷️  Confirmed Ethnicity Distribution:")
                for ethnicity, count in status['ethnicity_distribution'].items():
                    percentage = (count / status['confirmed_leads'] * 100) if status['confirmed_leads'] > 0 else 0
                    click.echo(f"   {ethnicity}: {count} ({percentage:.1f}%)")
            
            # Display detailed breakdown if requested
            if detailed and status.get('detailed_breakdown'):
                click.echo(f"\n📈 Detailed Breakdown:")
                breakdown = status['detailed_breakdown']
                for method, data in breakdown.items():
                    click.echo(f"   {method}:")
                    click.echo(f"     Total: {data['total']}")
                    click.echo(f"     Confirmed: {data['confirmed']}")
                    click.echo(f"     Accuracy: {data['accuracy']:.1f}%")
            
            # Display learning integration
            if status.get('learning_integration'):
                learning = status['learning_integration']
                click.echo(f"\n🧠 Learning Integration:")
                click.echo(f"   Patterns updated: {learning['patterns_updated']}")
                click.echo(f"   Spatial contexts: {learning['spatial_contexts']}")
                click.echo(f"   Learning contribution: {learning['contribution_score']:.2f}")
            
            # Export if requested
            if export:
                with open(export, 'w') as f:
                    import json
                    json.dump(status, f, indent=2, default=str)
                click.echo(f"📄 Status report exported to: {export}")
            
            click.echo(f"✅ Status analysis completed!")
                
        except Exception as e:
            click.echo(f"❌ Status analysis failed: {e}")
            logger.error("Status analysis failed",
                        job_id=job_id,
                        error=str(e))
    
    # Run async status
    asyncio.run(run_status())