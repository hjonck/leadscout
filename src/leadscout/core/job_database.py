"""
Resumable job database management for LeadScout.

This module implements SQLite-based job tracking, locking, and progress management
for large-scale lead processing with conservative resume capability and auto-learning
enhancement that reduces LLM dependency over time.

Key Features:
- Conservative resume from any interruption point
- SQLite-based job metadata and progress tracking  
- Automatic job locking to prevent concurrent processing
- Auto-learning pattern extraction from LLM successes
- Cost optimization through accumulated learning
- Comprehensive job validation and integrity checking

Architecture:
- JobExecution: Tracks overall job metadata and progress
- LeadResult: Individual lead processing results with learning data
- JobDatabase: Main database interface with full CRUD operations
- Auto-learning: Pattern extraction and rule generation from LLM classifications

Usage:
    db = JobDatabase()
    job = JobExecution(job_id="uuid", input_file_path="leads.xlsx", ...)
    job_id = db.create_job(job)
    # Process leads...
    db.save_lead_results(results)
    db.complete_job(job_id, success=True)
"""

import sqlite3
import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class JobExecution:
    """Job execution metadata and progress tracking.
    
    This class represents the overall job state including progress tracking,
    performance metrics, and error handling. Used for conservative resume
    logic and job lifecycle management.
    
    Attributes:
        job_id: Unique identifier for the job
        input_file_path: Path to source Excel file
        input_file_modified_time: File modification time for change detection
        output_file_path: Optional path for output file
        total_rows: Total number of leads to process
        batch_size: Configured batch size for processing
        last_committed_batch: Last successfully completed batch (for resume)
        processed_leads_count: Total successfully processed leads
        failed_leads_count: Total failed lead classifications
        status: Job status ('running', 'completed', 'failed', 'paused')
        start_time: Job start timestamp
        completion_time: Job completion timestamp
        api_costs_total: Total API costs incurred
        processing_time_total_ms: Total processing time in milliseconds
        error_summary: Summary of any errors encountered
        created_by: Process/session identifier that created the job
    """
    job_id: str
    input_file_path: str
    input_file_modified_time: int
    output_file_path: Optional[str]
    total_rows: int
    batch_size: int
    last_committed_batch: int = 0
    processed_leads_count: int = 0
    failed_leads_count: int = 0
    status: str = 'running'
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    api_costs_total: float = 0.0
    processing_time_total_ms: float = 0.0
    error_summary: Optional[str] = None
    created_by: Optional[str] = None

@dataclass
class LeadResult:
    """Individual lead processing result with auto-learning capabilities.
    
    This class stores the complete result of processing a single lead,
    including classification results, error details, performance metrics,
    and auto-learning data for pattern extraction and rule generation.
    
    Attributes:
        job_id: Associated job identifier
        row_index: Source row index in Excel file
        batch_number: Batch number this lead was processed in
        entity_name: Company/entity name from source data
        director_name: Director name being classified
        classification_result: Complete classification output (JSON)
        processing_status: Processing outcome ('success', 'failed', 'retry_exhausted')
        retry_count: Number of retry attempts made
        error_message: Detailed error message if processing failed
        error_type: Category of error ('rate_limit', 'api_error', 'validation_error', 'timeout')
        processing_time_ms: Time taken to process this lead
        api_provider: Provider used ('openai', 'anthropic', 'rule_based', 'phonetic')
        api_cost: Cost incurred for this classification
        created_at: Processing timestamp
        phonetic_codes: Generated phonetic variants for auto-learning
        learned_patterns: Extracted patterns for rule generation
        confidence_factors: Factors that influenced LLM confidence
    """
    job_id: str
    row_index: int
    batch_number: int
    entity_name: str
    director_name: str
    classification_result: Optional[Dict[str, Any]]
    processing_status: str  # 'success', 'failed', 'retry_exhausted'
    retry_count: int = 0
    error_message: Optional[str] = None
    error_type: Optional[str] = None  # 'rate_limit', 'api_error', 'validation_error', 'timeout'
    processing_time_ms: float = 0.0
    api_provider: Optional[str] = None
    api_cost: float = 0.0
    created_at: Optional[datetime] = None
    
    # Auto-learning enhancement fields
    phonetic_codes: Optional[Dict[str, Any]] = None  # Generated phonetic variants
    learned_patterns: Optional[Dict[str, Any]] = None  # Extracted patterns for rule generation
    confidence_factors: Optional[Dict[str, Any]] = None  # Factors that influenced LLM confidence

class JobDatabase:
    """SQLite database manager for resumable jobs.
    
    This class provides the core database operations for job management,
    including job creation, progress tracking, resume logic, and auto-learning
    pattern extraction. Implements conservative resume strategies and
    comprehensive job validation.
    
    Features:
    - Atomic batch commits for data consistency
    - Exclusive job locking to prevent concurrent processing
    - Conservative resume from last committed batch
    - Auto-learning pattern extraction from LLM successes
    - Comprehensive job validation and integrity checking
    - Performance metrics tracking and cost optimization
    
    Database Schema:
    - job_executions: Main job metadata and progress
    - lead_processing_results: Individual lead results
    - job_locks: File-based processing locks
    - auto_generated_rules: Learning-based classification rules
    - pattern_learning_analytics: Pattern analysis and validation
    """
    
    def __init__(self, db_path: Path = Path("cache/jobs.db")):
        """Initialize job database with schema creation.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
        logger.info("JobDatabase initialized", db_path=str(self.db_path))
    
    def _initialize_database(self):
        """Create database tables if they don't exist.
        
        Creates the complete schema for resumable job processing,
        including tables for job tracking, result storage, locking,
        and auto-learning enhancement.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS job_executions (
                    job_id TEXT PRIMARY KEY,
                    input_file_path TEXT NOT NULL,
                    input_file_modified_time INTEGER NOT NULL,
                    output_file_path TEXT,
                    total_rows INTEGER,
                    batch_size INTEGER DEFAULT 100,
                    last_committed_batch INTEGER DEFAULT 0,
                    processed_leads_count INTEGER DEFAULT 0,
                    failed_leads_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'running',
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completion_time TIMESTAMP,
                    api_costs_total REAL DEFAULT 0.0,
                    processing_time_total_ms REAL DEFAULT 0.0,
                    error_summary TEXT,
                    created_by TEXT
                );
                
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_running_job 
                ON job_executions(input_file_path) WHERE status = 'running';
                
                CREATE TABLE IF NOT EXISTS lead_processing_results (
                    job_id TEXT,
                    row_index INTEGER,
                    batch_number INTEGER,
                    entity_name TEXT,
                    director_name TEXT,
                    classification_result JSON,
                    processing_status TEXT,
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    error_type TEXT,
                    processing_time_ms REAL,
                    api_provider TEXT,
                    api_cost REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    phonetic_codes JSON,
                    learned_patterns JSON,
                    confidence_factors JSON,
                    PRIMARY KEY (job_id, row_index),
                    FOREIGN KEY (job_id) REFERENCES job_executions(job_id)
                );
                
                CREATE TABLE IF NOT EXISTS job_locks (
                    input_file_path TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    locked_by TEXT,
                    FOREIGN KEY (job_id) REFERENCES job_executions(job_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_job_results_status 
                ON lead_processing_results(job_id, processing_status);
                
                CREATE INDEX IF NOT EXISTS idx_job_batch 
                ON lead_processing_results(job_id, batch_number);
                
                -- Auto-learning enhancement tables
                CREATE TABLE IF NOT EXISTS auto_generated_rules (
                    rule_id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    source_job_id TEXT,
                    rule_type TEXT,
                    rule_pattern TEXT,
                    target_ethnicity TEXT,
                    confidence_score REAL,
                    usage_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT true,
                    FOREIGN KEY (source_job_id) REFERENCES job_executions(job_id)
                );
                
                CREATE TABLE IF NOT EXISTS pattern_learning_analytics (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT,
                    pattern_value TEXT,
                    ethnicity TEXT,
                    confidence_score REAL,
                    sample_names JSON,
                    validation_names JSON,
                    created_from_job_id TEXT,
                    accuracy_rate REAL DEFAULT 0.0,
                    total_applications INTEGER DEFAULT 0,
                    FOREIGN KEY (created_from_job_id) REFERENCES job_executions(job_id)
                );
                
                -- Enhanced learning analytics tables for job-level tracking
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
                    learning_efficiency REAL DEFAULT 0.0,
                    cost_savings_percent REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES job_executions(job_id)
                );
                
                -- Batch-level learning metrics for detailed tracking
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
            ''')
            logger.info("Database schema initialized")
    
    def create_job(self, job: JobExecution) -> str:
        """Create new job execution record.
        
        Args:
            job: JobExecution instance with job metadata
            
        Returns:
            job_id: The created job identifier
            
        Raises:
            ValueError: If job creation fails due to validation
            sqlite3.IntegrityError: If job already exists or file is locked
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Insert job record
                conn.execute('''
                    INSERT INTO job_executions (
                        job_id, input_file_path, input_file_modified_time,
                        output_file_path, total_rows, batch_size, 
                        processed_leads_count, failed_leads_count, status,
                        start_time, api_costs_total, processing_time_total_ms,
                        error_summary, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job.job_id, job.input_file_path, job.input_file_modified_time,
                    job.output_file_path, job.total_rows, job.batch_size,
                    job.processed_leads_count, job.failed_leads_count, job.status,
                    job.start_time or datetime.now(), job.api_costs_total,
                    job.processing_time_total_ms, job.error_summary, job.created_by
                ))
                
                logger.info("Job created successfully", 
                           job_id=job.job_id,
                           input_file=job.input_file_path,
                           total_rows=job.total_rows,
                           batch_size=job.batch_size)
                
                return job.job_id
                
        except sqlite3.IntegrityError as e:
            logger.error("Job creation failed", 
                        job_id=job.job_id,
                        error=str(e))
            raise ValueError(f"Job creation failed: {e}")
    
    def acquire_lock(self, input_file_path: str, job_id: str) -> bool:
        """Acquire exclusive lock for input file processing.
        
        Prevents multiple jobs from processing the same input file
        simultaneously. Uses SQLite UNIQUE constraint for atomicity.
        
        Args:
            input_file_path: Path to input file to lock
            job_id: Job ID requesting the lock
            
        Returns:
            bool: True if lock acquired successfully, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO job_locks (input_file_path, job_id, locked_by)
                    VALUES (?, ?, ?)
                ''', (input_file_path, job_id, f"process_{time.time()}"))
                
                logger.info("File lock acquired", 
                           file_path=input_file_path,
                           job_id=job_id)
                return True
                
        except sqlite3.IntegrityError:
            # Lock already exists
            logger.warning("File lock acquisition failed - file already locked",
                          file_path=input_file_path,
                          job_id=job_id)
            return False
    
    def release_lock(self, input_file_path: str) -> None:
        """Release lock for input file.
        
        Args:
            input_file_path: Path to input file to unlock
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                DELETE FROM job_locks WHERE input_file_path = ?
            ''', (input_file_path,))
            
            if cursor.rowcount > 0:
                logger.info("File lock released", file_path=input_file_path)
            else:
                logger.warning("No lock found to release", file_path=input_file_path)
    
    def force_clear_lock(self, input_file_path: str) -> bool:
        """Force clear any existing lock for input file.
        
        This method clears locks regardless of which job holds them.
        Useful for clearing stale locks after interrupted jobs.
        
        Args:
            input_file_path: Path to input file to force unlock
            
        Returns:
            bool: True if a lock was cleared, False if no lock existed
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                DELETE FROM job_locks WHERE input_file_path = ?
            ''', (input_file_path,))
            
            locks_cleared = cursor.rowcount > 0
            
            if locks_cleared:
                logger.warning("Force cleared stale lock", 
                             file_path=input_file_path,
                             locks_cleared=cursor.rowcount)
            else:
                logger.debug("No locks found to clear", file_path=input_file_path)
            
            return locks_cleared
    
    def get_existing_job(self, input_file_path: str) -> Optional[JobExecution]:
        """Get existing running job for input file.
        
        Checks for existing running jobs for the same input file,
        enabling resume functionality.
        
        Args:
            input_file_path: Path to input file
            
        Returns:
            JobExecution if running job exists, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM job_executions 
                WHERE input_file_path = ? AND status = 'running'
                ORDER BY start_time DESC
                LIMIT 1
            ''', (input_file_path,))
            
            row = cursor.fetchone()
            if row:
                job = JobExecution(
                    job_id=row['job_id'],
                    input_file_path=row['input_file_path'],
                    input_file_modified_time=row['input_file_modified_time'],
                    output_file_path=row['output_file_path'],
                    total_rows=row['total_rows'],
                    batch_size=row['batch_size'],
                    last_committed_batch=row['last_committed_batch'],
                    processed_leads_count=row['processed_leads_count'],
                    failed_leads_count=row['failed_leads_count'],
                    status=row['status'],
                    start_time=datetime.fromisoformat(row['start_time']) if row['start_time'] else None,
                    completion_time=datetime.fromisoformat(row['completion_time']) if row['completion_time'] else None,
                    api_costs_total=row['api_costs_total'],
                    processing_time_total_ms=row['processing_time_total_ms'],
                    error_summary=row['error_summary'],
                    created_by=row['created_by']
                )
                
                logger.info("Existing job found", 
                           job_id=job.job_id,
                           last_committed_batch=job.last_committed_batch,
                           processed_count=job.processed_leads_count)
                return job
        
        return None
    
    def update_job_progress(self, job_id: str, batch_number: int, 
                          processed_count: int, failed_count: int) -> None:
        """Update job progress after batch completion.
        
        Updates job metadata after successfully processing a batch.
        Uses conservative tracking to ensure resume safety.
        
        Args:
            job_id: Job identifier
            batch_number: Completed batch number
            processed_count: Total processed leads count
            failed_count: Total failed leads count
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE job_executions 
                SET last_committed_batch = ?,
                    processed_leads_count = ?,
                    failed_leads_count = ?
                WHERE job_id = ?
            ''', (batch_number, processed_count, failed_count, job_id))
            
            logger.debug("Job progress updated",
                        job_id=job_id,
                        batch_number=batch_number,
                        processed_count=processed_count,
                        failed_count=failed_count)
    
    def save_lead_results(self, results: List[LeadResult]) -> None:
        """Save batch of lead processing results.
        
        Atomically saves a complete batch of lead results,
        including auto-learning data extraction.
        
        Args:
            results: List of LeadResult instances to save
        """
        if not results:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            # Prepare data for batch insert
            insert_data = []
            for result in results:
                insert_data.append((
                    result.job_id, result.row_index, result.batch_number,
                    result.entity_name, result.director_name,
                    json.dumps(result.classification_result) if result.classification_result else None,
                    result.processing_status, result.retry_count,
                    result.error_message, result.error_type,
                    result.processing_time_ms, result.api_provider,
                    result.api_cost, result.created_at or datetime.now(),
                    json.dumps(result.phonetic_codes) if result.phonetic_codes else None,
                    json.dumps(result.learned_patterns) if result.learned_patterns else None,
                    json.dumps(result.confidence_factors) if result.confidence_factors else None
                ))
            
            # Batch insert all results
            conn.executemany('''
                INSERT OR REPLACE INTO lead_processing_results (
                    job_id, row_index, batch_number, entity_name, director_name,
                    classification_result, processing_status, retry_count,
                    error_message, error_type, processing_time_ms, api_provider,
                    api_cost, created_at, phonetic_codes, learned_patterns,
                    confidence_factors
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', insert_data)
            
            # Extract learning patterns from successful LLM classifications
            for result in results:
                if (result.processing_status == 'success' and 
                    result.api_provider in ['openai', 'anthropic'] and
                    result.classification_result):
                    self.extract_learning_patterns(result)
            
            logger.debug("Lead results saved",
                        batch_size=len(results),
                        job_id=results[0].job_id,
                        batch_number=results[0].batch_number)
    
    def get_resume_position(self, job_id: str, current_batch_size: Optional[int] = None) -> int:
        """Get safe resume position using actual processed count.
        
        Uses the actual processed_leads_count for resume position instead of
        calculated position to handle batch size changes safely.
        
        Args:
            job_id: Job identifier
            current_batch_size: Current batch size (for batch size change detection)
            
        Returns:
            int: Row index to resume processing from (actual processed count)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT last_committed_batch, batch_size, processed_leads_count 
                FROM job_executions 
                WHERE job_id = ?
            ''', (job_id,))
            
            row = cursor.fetchone()
            if row:
                last_batch, stored_batch_size, processed_count = row
                
                # Check for batch size change and warn if detected
                if current_batch_size and stored_batch_size != current_batch_size:
                    logger.warning(
                        "Batch size changed - using actual processed count for safe resume",
                        job_id=job_id,
                        old_batch_size=stored_batch_size,
                        new_batch_size=current_batch_size,
                        resume_from_row=processed_count
                    )
                
                # Always use actual processed count for resume position
                resume_row = processed_count
                
                logger.info("Resume position calculated",
                           job_id=job_id,
                           last_committed_batch=last_batch,
                           batch_size=stored_batch_size,
                           current_batch_size=current_batch_size,
                           processed_count=processed_count,
                           resume_row=resume_row)
                
                return resume_row
        
        logger.warning("Cannot determine resume position", job_id=job_id)
        return 0
    
    def complete_job(self, job_id: str, success: bool, error_summary: str = None) -> None:
        """Mark job as completed or failed.
        
        Args:
            job_id: Job identifier
            success: Whether job completed successfully
            error_summary: Optional error summary if job failed
        """
        status = 'completed' if success else 'failed'
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE job_executions 
                SET status = ?, 
                    completion_time = ?,
                    error_summary = ?
                WHERE job_id = ?
            ''', (status, datetime.now(), error_summary, job_id))
            
            logger.info("Job completion recorded",
                       job_id=job_id,
                       success=success,
                       status=status)
    
    def validate_job_integrity(self, job_id: str) -> Dict[str, Any]:
        """Validate job data integrity and return validation report.
        
        Performs comprehensive validation of job data consistency,
        including row count verification and result validation.
        
        Args:
            job_id: Job identifier
            
        Returns:
            dict: Validation report with status and details
        """
        with sqlite3.connect(self.db_path) as conn:
            # Get job metadata
            cursor = conn.execute('''
                SELECT total_rows, processed_leads_count, failed_leads_count
                FROM job_executions WHERE job_id = ?
            ''', (job_id,))
            
            job_row = cursor.fetchone()
            if not job_row:
                return {
                    'is_valid': False,
                    'errors': ['Job not found'],
                    'warnings': []
                }
            
            total_rows, processed_count, failed_count = job_row
            
            # Count actual results
            cursor = conn.execute('''
                SELECT COUNT(*) FROM lead_processing_results WHERE job_id = ?
            ''', (job_id,))
            
            actual_result_count = cursor.fetchone()[0]
            
            # Validation checks
            errors = []
            warnings = []
            
            # Check row count consistency
            expected_total = processed_count + failed_count
            if actual_result_count != expected_total:
                errors.append(f"Result count mismatch: {actual_result_count} actual vs {expected_total} expected")
            
            # Check against source file row count
            if actual_result_count != total_rows:
                warnings.append(f"Processed {actual_result_count} of {total_rows} total rows")
            
            # Check for duplicate row indices
            cursor = conn.execute('''
                SELECT row_index, COUNT(*) as count
                FROM lead_processing_results 
                WHERE job_id = ? 
                GROUP BY row_index 
                HAVING count > 1
            ''', (job_id,))
            
            duplicates = cursor.fetchall()
            if duplicates:
                errors.append(f"Duplicate row indices found: {len(duplicates)} conflicts")
            
            is_valid = len(errors) == 0
            
            logger.info("Job validation completed",
                       job_id=job_id,
                       is_valid=is_valid,
                       errors=len(errors),
                       warnings=len(warnings))
            
            return {
                'is_valid': is_valid,
                'errors': errors,
                'warnings': warnings,
                'total_rows': total_rows,
                'processed_count': processed_count,
                'failed_count': failed_count,
                'actual_result_count': actual_result_count
            }
    
    def extract_learning_patterns(self, lead_result: LeadResult) -> None:
        """Extract and store learnable patterns from successful LLM classification.
        
        Analyzes successful LLM classifications to extract patterns that can
        be used to generate automatic classification rules, reducing future
        LLM dependency and costs.
        
        Args:
            lead_result: Successfully processed lead result with LLM classification
        """
        if (lead_result.processing_status != 'success' or 
            lead_result.api_provider not in ['openai', 'anthropic'] or
            not lead_result.classification_result):
            return
        
        try:
            # Extract patterns from successful LLM classification
            patterns = self._analyze_name_patterns(
                lead_result.director_name,
                lead_result.classification_result
            )
            
            # Generate auto-rules from patterns
            auto_rules = self._generate_auto_rules(patterns, lead_result)
            
            # Store auto-generated rules with confidence scores
            self._store_auto_rules(auto_rules, lead_result.job_id)
            
            logger.info("Learning patterns extracted",
                       name=lead_result.director_name,
                       patterns_found=len(patterns),
                       rules_generated=len(auto_rules),
                       ethnicity=lead_result.classification_result.get('ethnicity'))
            
        except Exception as e:
            logger.warning("Pattern extraction failed",
                          name=lead_result.director_name,
                          error=str(e))
    
    def _analyze_name_patterns(self, name: str, classification: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze name to extract learnable patterns.
        
        Args:
            name: Director name to analyze
            classification: LLM classification result
            
        Returns:
            List of extracted patterns with confidence scores
        """
        patterns = []
        
        if not name or len(name.strip()) < 2:
            return patterns
        
        clean_name = name.strip().lower()
        ethnicity = classification.get('ethnicity', 'unknown')
        confidence = classification.get('confidence', 0.0)
        
        # Only extract patterns from high-confidence classifications
        if confidence < 0.8:
            return patterns
        
        # Extract prefix patterns (first 2-4 characters)
        for prefix_len in [2, 3, 4]:
            if len(clean_name) >= prefix_len:
                prefix = clean_name[:prefix_len]
                patterns.append({
                    'type': 'prefix',
                    'value': prefix,
                    'ethnicity': ethnicity,
                    'confidence': confidence,
                    'length': prefix_len
                })
        
        # Extract suffix patterns (last 2-4 characters)
        for suffix_len in [2, 3, 4]:
            if len(clean_name) >= suffix_len:
                suffix = clean_name[-suffix_len:]
                patterns.append({
                    'type': 'suffix',
                    'value': suffix,
                    'ethnicity': ethnicity,
                    'confidence': confidence,
                    'length': suffix_len
                })
        
        # Extract phonetic codes using multiple algorithms
        try:
            import jellyfish
            
            phonetic_patterns = [
                ('soundex', jellyfish.soundex(clean_name)),
                ('metaphone', jellyfish.metaphone(clean_name)),
                ('nysiis', jellyfish.nysiis(clean_name)),
            ]
            
            for algo_name, code in phonetic_patterns:
                if code:
                    patterns.append({
                        'type': 'phonetic',
                        'algorithm': algo_name,
                        'value': code,
                        'ethnicity': ethnicity,
                        'confidence': confidence * 0.9  # Slightly lower confidence for phonetic
                    })
                    
        except ImportError:
            logger.warning("Jellyfish not available for phonetic pattern extraction")
        
        return patterns
    
    def _generate_auto_rules(self, patterns: List[Dict[str, Any]], lead_result: LeadResult) -> List[Dict[str, Any]]:
        """Generate auto-classification rules from extracted patterns.
        
        Args:
            patterns: Extracted patterns from name analysis
            lead_result: Original lead result for context
            
        Returns:
            List of auto-generated rules with confidence scores
        """
        rules = []
        
        for pattern in patterns:
            # Generate rule based on pattern type
            rule = {
                'rule_id': str(uuid.uuid4()),
                'source_name': lead_result.director_name,
                'source_job_id': lead_result.job_id,
                'rule_type': pattern['type'],
                'rule_pattern': pattern['value'],
                'target_ethnicity': pattern['ethnicity'],
                'confidence_score': pattern['confidence'],
                'pattern_metadata': pattern
            }
            
            # Validate rule against existing data
            if self._validate_auto_rule(rule):
                rules.append(rule)
        
        return rules
    
    def _validate_auto_rule(self, rule: Dict[str, Any]) -> bool:
        """Validate auto-generated rule against existing successful classifications.
        
        Args:
            rule: Auto-generated rule to validate
            
        Returns:
            bool: True if rule appears valid, False otherwise
        """
        # Simple validation - in production, this would be more sophisticated
        # Check confidence threshold
        if rule['confidence_score'] < 0.8:
            return False
            
        # Check pattern length (avoid overly short patterns)
        if rule['rule_type'] in ['prefix', 'suffix'] and len(rule['rule_pattern']) < 2:
            return False
            
        return True
    
    def _store_auto_rules(self, rules: List[Dict[str, Any]], job_id: str) -> None:
        """Store auto-generated rules in database.
        
        Args:
            rules: List of auto-generated rules to store
            job_id: Associated job identifier
        """
        if not rules:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            for rule in rules:
                try:
                    conn.execute('''
                        INSERT OR IGNORE INTO auto_generated_rules (
                            rule_id, source_name, source_job_id, rule_type,
                            rule_pattern, target_ethnicity, confidence_score
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        rule['rule_id'],
                        rule['source_name'],
                        rule['source_job_id'],
                        rule['rule_type'],
                        rule['rule_pattern'],
                        rule['target_ethnicity'],
                        rule['confidence_score']
                    ))
                    
                except sqlite3.IntegrityError:
                    # Rule already exists, update usage count
                    conn.execute('''
                        UPDATE auto_generated_rules 
                        SET usage_count = usage_count + 1,
                            last_used_at = CURRENT_TIMESTAMP
                        WHERE rule_pattern = ? AND rule_type = ? AND target_ethnicity = ?
                    ''', (rule['rule_pattern'], rule['rule_type'], rule['target_ethnicity']))
            
            logger.debug("Auto-generated rules stored",
                        rules_count=len(rules),
                        job_id=job_id)
    
    def get_job_statistics(self, job_id: str) -> Dict[str, Any]:
        """Get comprehensive job statistics and performance metrics.
        
        Args:
            job_id: Job identifier
            
        Returns:
            dict: Complete job statistics and performance data
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get job metadata
            cursor = conn.execute('''
                SELECT * FROM job_executions WHERE job_id = ?
            ''', (job_id,))
            job_data = cursor.fetchone()
            
            if not job_data:
                return {}
            
            # Get processing method breakdown
            cursor = conn.execute('''
                SELECT api_provider, COUNT(*) as count, 
                       AVG(processing_time_ms) as avg_time,
                       SUM(api_cost) as total_cost
                FROM lead_processing_results 
                WHERE job_id = ? AND processing_status = 'success'
                GROUP BY api_provider
            ''', (job_id,))
            
            method_stats = {row['api_provider']: dict(row) for row in cursor.fetchall()}
            
            # Get error breakdown
            cursor = conn.execute('''
                SELECT error_type, COUNT(*) as count
                FROM lead_processing_results 
                WHERE job_id = ? AND processing_status = 'failed'
                GROUP BY error_type
            ''', (job_id,))
            
            error_stats = {row['error_type']: row['count'] for row in cursor.fetchall()}
            
            return {
                'job_metadata': dict(job_data),
                'method_breakdown': method_stats,
                'error_breakdown': error_stats,
                'llm_usage_percentage': self._calculate_llm_usage_percentage(method_stats),
                'cost_optimization_score': self._calculate_cost_optimization_score(method_stats)
            }
    
    def _calculate_llm_usage_percentage(self, method_stats: Dict[str, Any]) -> float:
        """Calculate percentage of classifications that used LLM providers."""
        total_successful = sum(stats['count'] for stats in method_stats.values())
        llm_count = sum(
            stats['count'] for provider, stats in method_stats.items()
            if provider in ['openai', 'anthropic']
        )
        
        return (llm_count / total_successful * 100) if total_successful > 0 else 0.0
    
    def _calculate_cost_optimization_score(self, method_stats: Dict[str, Any]) -> float:
        """Calculate cost optimization score based on method distribution."""
        total_successful = sum(stats['count'] for stats in method_stats.values())
        free_methods = ['rule_based', 'phonetic']
        free_count = sum(
            stats['count'] for provider, stats in method_stats.items()
            if provider in free_methods
        )
        
        return (free_count / total_successful * 100) if total_successful > 0 else 0.0
    
    def store_batch_learning_metrics(self, job_id: str, batch_number: int, 
                                   llm_calls: int, learned_pattern_hits: int, 
                                   new_patterns_generated: int, cost_saved: float,
                                   processing_time_ms: float) -> None:
        """Store learning metrics for a specific batch.
        
        Args:
            job_id: Job identifier
            batch_number: Batch number
            llm_calls: Number of LLM API calls made
            learned_pattern_hits: Number of learned pattern matches
            new_patterns_generated: Number of new patterns generated
            cost_saved: Estimated cost saved through learning
            processing_time_ms: Batch processing time
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO batch_learning_metrics 
                    (job_id, batch_number, llm_calls, learned_pattern_hits, 
                     new_patterns_generated, cost_saved, processing_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (job_id, batch_number, llm_calls, learned_pattern_hits,
                      new_patterns_generated, cost_saved, processing_time_ms))
                
                logger.debug("Batch learning metrics stored",
                           job_id=job_id,
                           batch_number=batch_number,
                           llm_calls=llm_calls,
                           learned_hits=learned_pattern_hits)
                
        except Exception as e:
            logger.error("Failed to store batch learning metrics",
                        job_id=job_id,
                        batch_number=batch_number,
                        error=str(e))
    
    def update_job_learning_analytics(self, job_id: str, 
                                    total_classifications: int,
                                    llm_classifications: int,
                                    learned_classifications: int,
                                    rule_classifications: int,
                                    phonetic_classifications: int,
                                    patterns_generated: int,
                                    estimated_cost_saved: float,
                                    actual_llm_cost: float) -> None:
        """Update job-level learning analytics.
        
        Args:
            job_id: Job identifier
            total_classifications: Total number of classifications performed
            llm_classifications: Number of LLM classifications
            learned_classifications: Number of learned pattern matches
            rule_classifications: Number of rule-based classifications
            phonetic_classifications: Number of phonetic classifications
            patterns_generated: Number of new patterns generated
            estimated_cost_saved: Estimated cost saved through learning
            actual_llm_cost: Actual LLM API costs incurred
        """
        try:
            learning_efficiency = (patterns_generated / max(llm_classifications, 1))
            cost_savings_percent = (estimated_cost_saved / max(estimated_cost_saved + actual_llm_cost, 0.001)) * 100
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO job_learning_analytics 
                    (job_id, total_classifications, llm_classifications, 
                     learned_classifications, rule_classifications, 
                     phonetic_classifications, patterns_generated,
                     estimated_cost_saved, actual_llm_cost, learning_efficiency,
                     cost_savings_percent, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (job_id, total_classifications, llm_classifications,
                      learned_classifications, rule_classifications,
                      phonetic_classifications, patterns_generated,
                      estimated_cost_saved, actual_llm_cost, learning_efficiency,
                      cost_savings_percent))
                
                logger.info("Job learning analytics updated",
                           job_id=job_id,
                           total_classifications=total_classifications,
                           llm_usage_percent=(llm_classifications / max(total_classifications, 1)) * 100,
                           cost_savings_percent=cost_savings_percent)
                
        except Exception as e:
            logger.error("Failed to update job learning analytics",
                        job_id=job_id,
                        error=str(e))
    
    def get_job_learning_analytics(self, job_id: str) -> Dict[str, Any]:
        """Get learning analytics for a specific job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Dictionary containing learning analytics or empty dict if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get job-level analytics
                result = conn.execute('''
                    SELECT * FROM job_learning_analytics WHERE job_id = ?
                ''', (job_id,)).fetchone()
                
                if result:
                    analytics = dict(result)
                    
                    # Get batch-level metrics summary
                    batch_summary = conn.execute('''
                        SELECT 
                            COUNT(*) as total_batches,
                            SUM(llm_calls) as total_llm_calls,
                            SUM(learned_pattern_hits) as total_learned_hits,
                            SUM(new_patterns_generated) as total_patterns_generated,
                            SUM(cost_saved) as total_cost_saved,
                            AVG(processing_time_ms) as avg_batch_time
                        FROM batch_learning_metrics 
                        WHERE job_id = ?
                    ''', (job_id,)).fetchone()
                    
                    if batch_summary:
                        analytics['batch_summary'] = dict(batch_summary)
                    
                    return analytics
                else:
                    logger.warning("No learning analytics found for job", job_id=job_id)
                    return {}
                    
        except Exception as e:
            logger.error("Failed to get job learning analytics",
                        job_id=job_id,
                        error=str(e))
            return {}