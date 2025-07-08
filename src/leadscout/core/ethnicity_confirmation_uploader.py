"""
Ethnicity confirmation upload system with comprehensive validation.

This module implements the complete confirmation upload workflow including:
- Excel file validation with detailed error reporting
- Canonical ethnicity validation
- Precise record matching using source tracking
- Bulk processing with transaction safety
- Integration with spatial learning system

Key Features:
- Comprehensive Excel validation (columns, data types, ethnicities)
- Row-by-row error reporting with specific messages
- Precise record matching using job_id + source_row_number
- Bulk processing with SQLite transaction safety
- Duplicate detection and handling
- Learning system integration triggers

Architecture:
- EthnicityConfirmationUploader: Main upload interface
- Comprehensive validation pipeline
- Precise record matching system
- Bulk operation optimization
- Integration with confirmation database

Usage:
    uploader = EthnicityConfirmationUploader()
    result = await uploader.upload_confirmations_from_excel(file_path, job_id)
"""

import asyncio
import sqlite3
import json
import uuid
import pandas as pd
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Set
import structlog

from .ethnicity_confirmation_database import (
    EthnicityConfirmationDatabase, 
    EthnicityConfirmation,
    generate_file_identifier,
    generate_spatial_context_hash
)
from .job_database import JobDatabase

logger = structlog.get_logger(__name__)

class EthnicityConfirmationUploader:
    """Advanced ethnicity confirmation upload system.
    
    Provides comprehensive Excel validation, precise record matching,
    and bulk processing with transaction safety for ethnicity confirmations.
    
    Features:
    - Excel validation with detailed error reporting
    - Canonical ethnicity validation
    - Precise record matching using source tracking
    - Bulk processing with SQLite transaction safety
    - Duplicate detection and smart handling
    - Learning system integration
    """
    
    def __init__(self, confirmation_db_path: Path = Path("cache/ethnicity_confirmations.db"),
                 job_db_path: Path = Path("cache/jobs.db")):
        """Initialize confirmation uploader.
        
        Args:
            confirmation_db_path: Path to confirmation database
            job_db_path: Path to job database
        """
        self.confirmation_db = EthnicityConfirmationDatabase(db_path=confirmation_db_path)
        self.job_db = JobDatabase(db_path=job_db_path)
        
        # Ensure canonical ethnicities are initialized
        self.confirmation_db.initialize_canonical_ethnicities()
        
        logger.info("EthnicityConfirmationUploader initialized",
                   confirmation_db_path=str(confirmation_db_path),
                   job_db_path=str(job_db_path))
    
    async def upload_confirmations_from_excel(self, file_path: Path, job_id: str,
                                            validate_only: bool = False,
                                            skip_duplicates: bool = False,
                                            force: bool = False) -> Dict[str, Any]:
        """Upload ethnicity confirmations from Excel file.
        
        This is the main business workflow function that processes Excel files
        filled by the dialler team with confirmed ethnicities.
        
        Args:
            file_path: Path to Excel file with confirmations
            job_id: Job ID to associate confirmations with
            validate_only: Only validate the file, don't upload
            skip_duplicates: Skip records that are already confirmed
            force: Force upload even if validation warnings exist
            
        Returns:
            Dictionary with upload results and statistics
            
        Raises:
            ValueError: If file format is invalid or job not found
            RuntimeError: If upload fails due to database errors
        """
        logger.info("Starting confirmation upload",
                   file_path=str(file_path),
                   job_id=job_id,
                   validate_only=validate_only,
                   skip_duplicates=skip_duplicates,
                   force=force)
        
        result = {
            'total_records': 0,
            'valid_confirmations': 0,
            'invalid_records': 0,
            'uploaded_count': 0,
            'skipped_count': 0,
            'warnings': [],
            'errors': [],
            'learning_patterns_updated': 0
        }
        
        try:
            # Step 1: Validate job exists
            await self._validate_job_exists(job_id)
            
            # Step 2: Validate Excel file structure
            df = await self._validate_excel_structure(file_path)
            result['total_records'] = len(df)
            
            # Step 3: Validate canonical ethnicities
            canonical_ethnicities = self.confirmation_db.get_canonical_ethnicities_list()
            
            # Step 4: Process and validate each record
            valid_confirmations = []
            for index, row in df.iterrows():
                try:
                    validation_result = await self._validate_confirmation_record(
                        row, index + 2, job_id, canonical_ethnicities  # +2 for Excel 1-based + header
                    )
                    
                    if validation_result['valid']:
                        valid_confirmations.append(validation_result['confirmation'])
                        result['valid_confirmations'] += 1
                    else:
                        result['invalid_records'] += 1
                        for error in validation_result['errors']:
                            result['errors'].append(f"Row {index + 2}: {error}")
                        for warning in validation_result.get('warnings', []):
                            result['warnings'].append(f"Row {index + 2}: {warning}")
                            
                except Exception as e:
                    result['invalid_records'] += 1
                    result['errors'].append(f"Row {index + 2}: Validation failed - {str(e)}")
                    logger.warning("Record validation failed",
                                 row_index=index + 2,
                                 error=str(e))
            
            # Step 5: Check for duplicates if skip_duplicates is enabled
            if skip_duplicates and valid_confirmations:
                valid_confirmations, skipped = await self._filter_duplicates(valid_confirmations, job_id)
                result['skipped_count'] = skipped
            
            # Step 6: Validate force requirements
            if not force and result['warnings'] and not validate_only:
                result['errors'].append("Upload blocked due to warnings. Use --force to override.")
                return result
            
            # Step 7: Upload confirmations (if not validate_only)
            if not validate_only and valid_confirmations:
                upload_result = await self._bulk_upload_confirmations(valid_confirmations, job_id)
                result['uploaded_count'] = upload_result['uploaded_count']
                result['learning_patterns_updated'] = upload_result['learning_patterns_updated']
                
                # Step 8: Trigger learning system update
                await self._trigger_learning_update(job_id, valid_confirmations)
            
            logger.info("Confirmation upload completed",
                       job_id=job_id,
                       total_records=result['total_records'],
                       valid_confirmations=result['valid_confirmations'],
                       uploaded_count=result['uploaded_count'],
                       errors=len(result['errors']))
            
            return result
            
        except Exception as e:
            logger.error("Confirmation upload failed",
                        file_path=str(file_path),
                        job_id=job_id,
                        error=str(e))
            raise RuntimeError(f"Upload failed: {e}")
    
    async def _validate_job_exists(self, job_id: str) -> None:
        """Validate that the job exists in the database."""
        with sqlite3.connect(self.job_db.db_path) as conn:
            cursor = conn.execute(
                "SELECT job_id FROM job_executions WHERE job_id = ?",
                (job_id,)
            )
            if not cursor.fetchone():
                raise ValueError(f"Job not found: {job_id}")
    
    async def _validate_excel_structure(self, file_path: Path) -> pd.DataFrame:
        """Validate Excel file structure and required columns."""
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Check for empty file
            if df.empty:
                raise ValueError("Excel file is empty")
            
            # Required columns for confirmation upload
            required_columns = {
                'source_row_number': 'Source row number for record matching',
                'DirectorName': 'Director name for validation',
                'director_ethnicity': 'AI-predicted ethnicity',
                'confirmed_ethnicity': 'Human-confirmed ethnicity (required)'
            }
            
            # Check for missing required columns
            missing_columns = []
            for column in required_columns.keys():
                if column not in df.columns:
                    missing_columns.append(f"{column} ({required_columns[column]})")
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Optional columns that enhance validation
            optional_columns = ['confirmation_notes', 'job_id', 'processed_at']
            
            logger.info("Excel structure validation passed",
                       file_path=str(file_path),
                       total_rows=len(df),
                       required_columns_found=len(required_columns),
                       optional_columns_found=len([col for col in optional_columns if col in df.columns]))
            
            return df
            
        except Exception as e:
            raise ValueError(f"Excel file validation failed: {e}")
    
    async def _validate_confirmation_record(self, row: pd.Series, excel_row_number: int,
                                          job_id: str, canonical_ethnicities: List[str]) -> Dict[str, Any]:
        """Validate individual confirmation record.
        
        Args:
            row: Pandas row with confirmation data
            excel_row_number: Excel row number for error reporting
            job_id: Job ID for record matching
            canonical_ethnicities: List of valid ethnicities
            
        Returns:
            Dictionary with validation result and confirmation record
        """
        validation_result = {
            'valid': False,
            'confirmation': None,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Extract and validate core fields
            source_row_number = row.get('source_row_number')
            director_name = row.get('DirectorName', '').strip() if pd.notna(row.get('DirectorName')) else ''
            director_ethnicity = row.get('director_ethnicity', '').strip() if pd.notna(row.get('director_ethnicity')) else ''
            confirmed_ethnicity = row.get('confirmed_ethnicity', '').strip() if pd.notna(row.get('confirmed_ethnicity')) else ''
            confirmation_notes = row.get('confirmation_notes', '').strip() if pd.notna(row.get('confirmation_notes')) else ''
            
            # Validate source_row_number
            if pd.isna(source_row_number) or not isinstance(source_row_number, (int, float)) or source_row_number <= 0:
                validation_result['errors'].append("Invalid or missing source_row_number")
            else:
                source_row_number = int(source_row_number)
            
            # Validate director_name
            if not director_name:
                validation_result['errors'].append("DirectorName is required and cannot be empty")
            
            # Validate confirmed_ethnicity (CRITICAL)
            if not confirmed_ethnicity:
                validation_result['errors'].append("confirmed_ethnicity is required and cannot be empty")
            elif confirmed_ethnicity not in canonical_ethnicities:
                validation_result['errors'].append(
                    f"Invalid confirmed_ethnicity '{confirmed_ethnicity}'. "
                    f"Must be one of: {', '.join(canonical_ethnicities)}"
                )
            
            # Warning for missing AI prediction
            if not director_ethnicity:
                validation_result['warnings'].append("Missing director_ethnicity (AI prediction)")
            
            # If basic validation passed, verify record exists in job
            if not validation_result['errors']:
                record_exists = await self._verify_record_exists_in_job(job_id, source_row_number, director_name)
                if not record_exists:
                    validation_result['errors'].append(
                        f"Record not found in job {job_id} with source_row_number {source_row_number} "
                        f"and DirectorName '{director_name}'"
                    )
            
            # If all validation passed, create confirmation record
            if not validation_result['errors']:
                confirmation = EthnicityConfirmation(
                    confirmation_id=str(uuid.uuid4()),
                    source_file_identifier='',  # Will be set during upload
                    source_row_number=source_row_number,
                    source_job_id=job_id,
                    original_entity_name='',  # Will be populated from job data
                    original_director_name=director_name,
                    ai_predicted_ethnicity=director_ethnicity,
                    ai_confidence_score=0.0,  # Will be populated from job data
                    ai_classification_method='',  # Will be populated from job data
                    confirmed_ethnicity=confirmed_ethnicity,
                    confirmation_source='dialler_team',
                    confirmation_notes=confirmation_notes,
                    confirmed_by='',  # Could be enhanced to track user
                    confirmed_at=datetime.utcnow(),
                    spatial_context_hash='',  # Will be calculated
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                validation_result['valid'] = True
                validation_result['confirmation'] = confirmation
            
            return validation_result
            
        except Exception as e:
            validation_result['errors'].append(f"Validation error: {str(e)}")
            return validation_result
    
    async def _verify_record_exists_in_job(self, job_id: str, source_row_number: int, director_name: str) -> bool:
        """Verify that a record exists in the job database for precise matching."""
        try:
            with sqlite3.connect(self.job_db.db_path) as conn:
                # Check if source tracking fields exist (for backward compatibility)
                cursor = conn.execute("PRAGMA table_info(lead_processing_results)")
                columns = [row[1] for row in cursor.fetchall()]
                has_source_tracking = 'source_row_number' in columns
                
                if has_source_tracking:
                    # Use source tracking fields for new jobs
                    query = """
                    SELECT 1 FROM lead_processing_results 
                    WHERE job_id = ? 
                    AND source_row_number = ? 
                    AND (original_director_name = ? OR director_name = ?)
                    LIMIT 1
                    """
                    cursor = conn.execute(query, (job_id, source_row_number, director_name, director_name))
                else:
                    # Fallback to row_index for older jobs (assuming source_row_number = row_index + 2)
                    row_index = source_row_number - 2  # Convert Excel 1-based to 0-based row_index
                    query = """
                    SELECT 1 FROM lead_processing_results 
                    WHERE job_id = ? 
                    AND row_index = ? 
                    AND director_name = ?
                    LIMIT 1
                    """
                    cursor = conn.execute(query, (job_id, row_index, director_name))
                
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.warning("Failed to verify record existence",
                          job_id=job_id,
                          source_row_number=source_row_number,
                          director_name=director_name,
                          error=str(e))
            return False
    
    async def _filter_duplicates(self, confirmations: List[EthnicityConfirmation], 
                               job_id: str) -> Tuple[List[EthnicityConfirmation], int]:
        """Filter out confirmations that already exist in the database."""
        try:
            existing_confirmations = set()
            
            # Get existing confirmations for this job
            with sqlite3.connect(self.confirmation_db.db_path) as conn:
                cursor = conn.execute(
                    """SELECT source_row_number FROM ethnicity_confirmations 
                       WHERE source_job_id = ?""",
                    (job_id,)
                )
                existing_confirmations = {row[0] for row in cursor.fetchall()}
            
            # Filter out duplicates
            filtered_confirmations = []
            skipped_count = 0
            
            for confirmation in confirmations:
                if confirmation.source_row_number in existing_confirmations:
                    skipped_count += 1
                else:
                    filtered_confirmations.append(confirmation)
            
            logger.info("Duplicate filtering completed",
                       job_id=job_id,
                       original_count=len(confirmations),
                       filtered_count=len(filtered_confirmations),
                       skipped_count=skipped_count)
            
            return filtered_confirmations, skipped_count
            
        except Exception as e:
            logger.warning("Duplicate filtering failed",
                          job_id=job_id,
                          error=str(e))
            return confirmations, 0
    
    async def _bulk_upload_confirmations(self, confirmations: List[EthnicityConfirmation], 
                                       job_id: str) -> Dict[str, Any]:
        """Bulk upload confirmations with transaction safety."""
        upload_result = {
            'uploaded_count': 0,
            'learning_patterns_updated': 0
        }
        
        try:
            # Enrich confirmations with job data
            enriched_confirmations = await self._enrich_confirmations_with_job_data(confirmations, job_id)
            
            # Bulk store confirmations
            upload_result['uploaded_count'] = self.confirmation_db.bulk_store_confirmations(enriched_confirmations)
            
            logger.info("Bulk upload completed",
                       job_id=job_id,
                       uploaded_count=upload_result['uploaded_count'])
            
            return upload_result
            
        except Exception as e:
            logger.error("Bulk upload failed",
                        job_id=job_id,
                        error=str(e))
            raise RuntimeError(f"Bulk upload failed: {e}")
    
    async def _enrich_confirmations_with_job_data(self, confirmations: List[EthnicityConfirmation], 
                                                job_id: str) -> List[EthnicityConfirmation]:
        """Enrich confirmation records with data from job processing results."""
        try:
            # Get job data for enrichment
            with sqlite3.connect(self.job_db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Check if source tracking fields exist (for backward compatibility)
                cursor = conn.execute("PRAGMA table_info(lead_processing_results)")
                columns = [row[1] for row in cursor.fetchall()]
                has_source_tracking = 'source_row_number' in columns
                
                if has_source_tracking:
                    query = """
                    SELECT source_row_number, entity_name, director_name,
                           classification_result, original_entity_name,
                           original_director_name, original_registered_city,
                           original_registered_province, input_file_path
                    FROM lead_processing_results lpr
                    JOIN job_executions je ON lpr.job_id = je.job_id
                    WHERE lpr.job_id = ?
                    """
                    cursor = conn.execute(query, (job_id,))
                    job_data = {row['source_row_number']: dict(row) for row in cursor.fetchall()}
                else:
                    # Fallback for older jobs
                    query = """
                    SELECT row_index, entity_name, director_name,
                           classification_result, je.input_file_path
                    FROM lead_processing_results lpr
                    JOIN job_executions je ON lpr.job_id = je.job_id
                    WHERE lpr.job_id = ?
                    """
                    cursor = conn.execute(query, (job_id,))
                    # Map row_index to source_row_number (Excel 1-based + header)
                    job_data = {}
                    for row in cursor.fetchall():
                        row_dict = dict(row)
                        source_row_number = row['row_index'] + 2  # Convert to Excel row number
                        # Add fallback values for missing fields
                        row_dict['source_row_number'] = source_row_number
                        row_dict['original_entity_name'] = row['entity_name']
                        row_dict['original_director_name'] = row['director_name']
                        row_dict['original_registered_city'] = None
                        row_dict['original_registered_province'] = None
                        job_data[source_row_number] = row_dict
            
            # Enrich each confirmation
            enriched_confirmations = []
            for confirmation in confirmations:
                if confirmation.source_row_number in job_data:
                    row_data = job_data[confirmation.source_row_number]
                    
                    # Parse AI classification data
                    classification_data = {}
                    if row_data['classification_result']:
                        try:
                            classification_data = json.loads(row_data['classification_result'])
                        except json.JSONDecodeError:
                            pass
                    
                    # Enrich confirmation with job data
                    confirmation.original_entity_name = row_data['original_entity_name'] or row_data['entity_name']
                    confirmation.ai_confidence_score = classification_data.get('confidence', 0.0)
                    confirmation.ai_classification_method = classification_data.get('method', 'unknown')
                    
                    # Generate spatial context
                    city = row_data['original_registered_city']
                    province = row_data['original_registered_province']
                    if city and province:
                        confirmation.canonical_city = city
                        confirmation.canonical_province = province
                        confirmation.spatial_context_hash = generate_spatial_context_hash(
                            confirmation.original_director_name, '', city, province
                        )
                    
                    # Generate file identifier
                    if row_data['input_file_path']:
                        confirmation.source_file_identifier = generate_file_identifier(Path(row_data['input_file_path']))
                    
                    # Note: Accuracy and learning scores would be calculated here
                    # if they were part of the dataclass definition
                
                enriched_confirmations.append(confirmation)
            
            logger.info("Confirmations enriched with job data",
                       job_id=job_id,
                       enriched_count=len(enriched_confirmations))
            
            return enriched_confirmations
            
        except Exception as e:
            logger.error("Failed to enrich confirmations",
                        job_id=job_id,
                        error=str(e))
            raise RuntimeError(f"Failed to enrich confirmations: {e}")
    
    async def _trigger_learning_update(self, job_id: str, confirmations: List[EthnicityConfirmation]) -> None:
        """Trigger learning system update with new confirmations."""
        try:
            # TODO: Integration with Developer B's spatial learning system
            # This would call Developer B's learning update function
            # 
            # Example integration:
            # from ..spatial_learning import SpatialLearningDatabase
            # spatial_db = SpatialLearningDatabase()
            # await spatial_db.update_spatial_patterns_from_confirmations(confirmations)
            
            logger.info("Learning system update triggered",
                       job_id=job_id,
                       confirmation_count=len(confirmations))
            
        except Exception as e:
            logger.warning("Failed to trigger learning update",
                          job_id=job_id,
                          error=str(e))
            # Don't fail the upload if learning update fails
    
    async def confirm_single_lead(self, job_id: str, source_row_number: int,
                                confirmed_ethnicity: str, confirmation_notes: str = '',
                                director_name_validation: Optional[str] = None) -> Dict[str, Any]:
        """Confirm ethnicity for a single lead record."""
        result = {
            'success': False,
            'confirmation_id': None,
            'error': None,
            'previous_prediction': None,
            'learning_updated': False
        }
        
        try:
            # Validate inputs
            canonical_ethnicities = self.confirmation_db.get_canonical_ethnicities_list()
            if confirmed_ethnicity not in canonical_ethnicities:
                result['error'] = f"Invalid ethnicity. Must be one of: {', '.join(canonical_ethnicities)}"
                return result
            
            # Get existing record from job
            with sqlite3.connect(self.job_db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Check if source tracking fields exist (for backward compatibility)
                cursor = conn.execute("PRAGMA table_info(lead_processing_results)")
                columns = [row[1] for row in cursor.fetchall()]
                has_source_tracking = 'source_row_number' in columns
                
                if has_source_tracking:
                    query = """
                    SELECT * FROM lead_processing_results 
                    WHERE job_id = ? AND source_row_number = ?
                    """
                    if director_name_validation:
                        query += " AND (original_director_name = ? OR director_name = ?)"
                        params = (job_id, source_row_number, director_name_validation, director_name_validation)
                    else:
                        params = (job_id, source_row_number)
                else:
                    # Fallback for older jobs
                    row_index = source_row_number - 2  # Convert Excel row to 0-based row_index
                    query = """
                    SELECT * FROM lead_processing_results 
                    WHERE job_id = ? AND row_index = ?
                    """
                    if director_name_validation:
                        query += " AND director_name = ?"
                        params = (job_id, row_index, director_name_validation)
                    else:
                        params = (job_id, row_index)
                
                cursor = conn.execute(query, params)
                record = cursor.fetchone()
            
            if not record:
                result['error'] = f"Record not found: job_id={job_id}, source_row_number={source_row_number}"
                return result
            
            # Parse existing AI prediction
            classification_data = {}
            if record['classification_result']:
                try:
                    classification_data = json.loads(record['classification_result'])
                    result['previous_prediction'] = {
                        'ethnicity': classification_data.get('ethnicity', 'unknown'),
                        'confidence': classification_data.get('confidence', 0.0),
                        'method': classification_data.get('method', 'unknown')
                    }
                except json.JSONDecodeError:
                    pass
            
            # Get job file path for file identifier
            job_file_path = ''
            if 'input_file_path' in record and record['input_file_path']:
                job_file_path = record['input_file_path']
            else:
                # Get from job_executions table for older records
                job_cursor = conn.execute('SELECT input_file_path FROM job_executions WHERE job_id = ?', (job_id,))
                job_row = job_cursor.fetchone()
                if job_row:
                    job_file_path = job_row['input_file_path']
            
            # Create confirmation record
            confirmation = EthnicityConfirmation(
                confirmation_id=str(uuid.uuid4()),
                source_file_identifier=generate_file_identifier(Path(job_file_path)) if job_file_path else '',
                source_row_number=source_row_number,
                source_job_id=job_id,
                original_entity_name=record['original_entity_name'] if 'original_entity_name' in record.keys() else record['entity_name'],
                original_director_name=record['original_director_name'] if 'original_director_name' in record.keys() else record['director_name'],
                ai_predicted_ethnicity=classification_data.get('ethnicity', ''),
                ai_confidence_score=classification_data.get('confidence', 0.0),
                ai_classification_method=classification_data.get('method', 'unknown'),
                confirmed_ethnicity=confirmed_ethnicity,
                confirmation_source='manual_cli',
                confirmation_notes=confirmation_notes,
                confirmed_by='cli_user',
                confirmed_at=datetime.utcnow(),
                canonical_city=record['original_registered_city'] if 'original_registered_city' in record.keys() else '',
                canonical_province=record['original_registered_province'] if 'original_registered_province' in record.keys() else '',
                spatial_context_hash=generate_spatial_context_hash(
                    record['original_director_name'] if 'original_director_name' in record.keys() else record['director_name'],
                    '',  # suburb
                    record['original_registered_city'] if 'original_registered_city' in record.keys() else '',
                    record['original_registered_province'] if 'original_registered_province' in record.keys() else ''
                ) if ('original_registered_city' in record.keys() and record['original_registered_city']) else '',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Store confirmation
            self.confirmation_db.store_confirmation_record(confirmation)
            
            # Trigger learning update
            await self._trigger_learning_update(job_id, [confirmation])
            
            result['success'] = True
            result['confirmation_id'] = confirmation.confirmation_id
            result['learning_updated'] = True
            
            logger.info("Single confirmation completed",
                       job_id=job_id,
                       source_row_number=source_row_number,
                       confirmed_ethnicity=confirmed_ethnicity,
                       confirmation_id=confirmation.confirmation_id)
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            logger.error("Single confirmation failed",
                        job_id=job_id,
                        source_row_number=source_row_number,
                        error=str(e))
            return result
    
    async def bulk_confirm_from_csv(self, csv_path: Path, validate_only: bool = False) -> Dict[str, Any]:
        """Bulk confirm ethnicities from CSV file."""
        result = {
            'total_records': 0,
            'valid_confirmations': 0,
            'invalid_records': 0,
            'uploaded_count': 0,
            'errors': [],
            'learning_patterns_updated': 0
        }
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_path)
            result['total_records'] = len(df)
            
            # Required columns for CSV
            required_columns = ['job_id', 'source_row_number', 'director_name', 'confirmed_ethnicity']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                result['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")
                return result
            
            # Process each record
            for index, row in df.iterrows():
                try:
                    single_result = await self.confirm_single_lead(
                        job_id=row['job_id'],
                        source_row_number=int(row['source_row_number']),
                        confirmed_ethnicity=row['confirmed_ethnicity'],
                        confirmation_notes=row.get('confirmation_notes', ''),
                        director_name_validation=row.get('director_name')
                    )
                    
                    if single_result['success']:
                        result['valid_confirmations'] += 1
                        if not validate_only:
                            result['uploaded_count'] += 1
                    else:
                        result['invalid_records'] += 1
                        result['errors'].append(f"Row {index + 2}: {single_result['error']}")
                        
                except Exception as e:
                    result['invalid_records'] += 1
                    result['errors'].append(f"Row {index + 2}: {str(e)}")
            
            logger.info("Bulk CSV confirmation completed",
                       csv_path=str(csv_path),
                       total_records=result['total_records'],
                       valid_confirmations=result['valid_confirmations'],
                       uploaded_count=result['uploaded_count'])
            
            return result
            
        except Exception as e:
            logger.error("Bulk CSV confirmation failed",
                        csv_path=str(csv_path),
                        error=str(e))
            raise RuntimeError(f"Bulk CSV confirmation failed: {e}")