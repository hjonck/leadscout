"""
Ethnicity confirmation database management for LeadScout.

This module implements SQLite-based ethnicity confirmation tracking with precise
record tracing, spatial context analysis, and learning system integration.

Key Features:
- Complete confirmation lifecycle management
- Precise source file and row tracking
- Canonical ethnicity validation
- Spatial pattern learning integration
- File identification system for uniqueness
- Excel export/import validation

Architecture:
- EthnicityConfirmationDatabase: Main database interface
- File identification system for precise tracking
- Canonical ethnicity management
- Spatial context hashing for correlation analysis

Usage:
    db = EthnicityConfirmationDatabase()
    confirmation_id = db.store_confirmation_record(record)
    confirmations = db.get_confirmations_for_job(job_id)
"""

import sqlite3
import json
import hashlib
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class EthnicityConfirmation:
    """Ethnicity confirmation record with complete traceability.
    
    This class represents a complete ethnicity confirmation record including
    source tracking, AI predictions, human confirmations, and spatial context.
    
    Attributes:
        confirmation_id: Unique identifier for the confirmation record
        source_file_identifier: Unique file identifier (filename + hash)
        source_row_number: 1-based Excel row number
        source_job_id: Associated processing job identifier
        original_entity_name: Company/entity name from source data
        original_director_name: Director name being classified
        original_registered_address: Full registered address
        original_registered_city: Registered city
        original_registered_province: Registered province
        canonical_suburb: Cleaned suburb name for spatial analysis
        canonical_city: Cleaned city name
        canonical_province: Cleaned province name
        spatial_context_hash: Hash for spatial context lookups
        ai_predicted_ethnicity: AI classification result
        ai_confidence_score: AI confidence level (0.0-1.0)
        ai_classification_method: Method used (rule_based|phonetic|llm|cache)
        confirmed_ethnicity: Human-confirmed ethnicity (canonical)
        confirmed_by: Sales rep or confirmer identifier
        confirmed_at: Confirmation timestamp
        confirmation_notes: Optional notes from confirmation
        confirmation_source: Source of confirmation (phone_call|meeting|email)
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    confirmation_id: str
    source_file_identifier: str
    source_row_number: int
    source_job_id: str
    original_entity_name: str
    original_director_name: str
    original_registered_address: Optional[str] = None
    original_registered_city: Optional[str] = None
    original_registered_province: Optional[str] = None
    canonical_suburb: Optional[str] = None
    canonical_city: Optional[str] = None
    canonical_province: Optional[str] = None
    spatial_context_hash: Optional[str] = None
    ai_predicted_ethnicity: str = 'unknown'
    ai_confidence_score: float = 0.0
    ai_classification_method: str = 'unknown'
    confirmed_ethnicity: Optional[str] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    confirmation_notes: Optional[str] = None
    confirmation_source: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class CanonicalEthnicity:
    """Canonical ethnicity definition for validation.
    
    Represents a valid ethnicity option with display information
    and ordering for dropdown presentation.
    
    Attributes:
        ethnicity_code: System identifier (lowercase, underscore)
        ethnicity_display_name: Human-readable name
        ethnicity_order: Order for dropdown display (lower = first)
        ethnicity_description: Optional description
        is_active: Whether ethnicity is currently active
        created_at: Creation timestamp
    """
    ethnicity_code: str
    ethnicity_display_name: str
    ethnicity_order: int
    ethnicity_description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

class EthnicityConfirmationDatabase:
    """SQLite database manager for ethnicity confirmations.
    
    This class provides complete database operations for ethnicity confirmation
    lifecycle management, including source tracking, validation, and learning
    integration.
    
    Features:
    - Precise source file and row tracking
    - Canonical ethnicity validation
    - Spatial context analysis and hashing
    - File identification system
    - Excel export/import support
    - Learning system integration
    
    Database Schema:
    - ethnicity_confirmations: Main confirmation records
    - canonical_ethnicities: Valid ethnicity definitions
    - spatial_ethnicity_patterns: Learning patterns with confirmations
    - file_processing_sessions: File tracking metadata
    """
    
    def __init__(self, db_path: Path = Path("cache/ethnicity_confirmations.db")):
        """Initialize ethnicity confirmation database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
        logger.info("EthnicityConfirmationDatabase initialized", db_path=str(self.db_path))
    
    def _initialize_database(self):
        """Create database tables if they don't exist.
        
        Creates the complete schema for ethnicity confirmation management,
        including confirmation tracking, canonical validation, and spatial
        pattern learning integration.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript('''
                -- Core ethnicity confirmation lifecycle table
                CREATE TABLE IF NOT EXISTS ethnicity_confirmations (
                    confirmation_id TEXT PRIMARY KEY,
                    
                    -- Source tracing (exact record identification)
                    source_file_identifier TEXT NOT NULL,
                    source_row_number INTEGER NOT NULL,
                    source_job_id TEXT NOT NULL,
                    
                    -- Original data preservation
                    original_entity_name TEXT NOT NULL,
                    original_director_name TEXT NOT NULL,
                    original_registered_address TEXT,
                    original_registered_city TEXT,
                    original_registered_province TEXT,
                    
                    -- Spatial context for correlation analysis
                    canonical_suburb TEXT,
                    canonical_city TEXT,
                    canonical_province TEXT,
                    spatial_context_hash TEXT,
                    
                    -- AI prediction data
                    ai_predicted_ethnicity TEXT NOT NULL,
                    ai_confidence_score REAL NOT NULL,
                    ai_classification_method TEXT NOT NULL,
                    
                    -- Human confirmation data
                    confirmed_ethnicity TEXT,
                    confirmed_by TEXT,
                    confirmed_at TIMESTAMP,
                    confirmation_notes TEXT,
                    confirmation_source TEXT,
                    
                    -- Metadata
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Constraints
                    UNIQUE(source_file_identifier, source_row_number),
                    FOREIGN KEY (confirmed_ethnicity) REFERENCES canonical_ethnicities(ethnicity_code)
                );
                
                -- Canonical ethnicity definitions with strict validation
                CREATE TABLE IF NOT EXISTS canonical_ethnicities (
                    ethnicity_code TEXT PRIMARY KEY,
                    ethnicity_display_name TEXT NOT NULL,
                    ethnicity_order INTEGER NOT NULL,
                    ethnicity_description TEXT,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Enhanced spatial ethnicity patterns with confirmation tracking
                CREATE TABLE IF NOT EXISTS spatial_ethnicity_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    
                    -- Pattern definition
                    name_component TEXT NOT NULL,
                    suburb TEXT,
                    city TEXT,
                    province TEXT,
                    
                    -- Pattern effectiveness
                    ethnicity_code TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    confirmation_count INTEGER DEFAULT 0,
                    total_applications INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    
                    -- Pattern lifecycle
                    created_from_job_id TEXT,
                    last_confirmed_at TIMESTAMP,
                    last_applied_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (ethnicity_code) REFERENCES canonical_ethnicities(ethnicity_code)
                );
                
                -- File processing tracking for precise record management
                CREATE TABLE IF NOT EXISTS file_processing_sessions (
                    session_id TEXT PRIMARY KEY,
                    source_file_path TEXT NOT NULL,
                    source_file_identifier TEXT NOT NULL,
                    source_file_size INTEGER,
                    source_file_modified_time INTEGER,
                    total_rows INTEGER,
                    processed_rows INTEGER DEFAULT 0,
                    
                    -- Processing metadata
                    job_id TEXT NOT NULL,
                    processing_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_completed_at TIMESTAMP,
                    processing_status TEXT DEFAULT 'running'
                );
                
                -- Performance indexes
                CREATE INDEX IF NOT EXISTS idx_ethnicity_confirmations_source 
                ON ethnicity_confirmations(source_file_identifier, source_row_number);
                
                CREATE INDEX IF NOT EXISTS idx_ethnicity_confirmations_job 
                ON ethnicity_confirmations(source_job_id);
                
                CREATE INDEX IF NOT EXISTS idx_ethnicity_confirmations_spatial 
                ON ethnicity_confirmations(canonical_suburb, canonical_city, original_director_name);
                
                CREATE INDEX IF NOT EXISTS idx_spatial_patterns_lookup 
                ON spatial_ethnicity_patterns(name_component, suburb, city);
                
                CREATE INDEX IF NOT EXISTS idx_spatial_patterns_effectiveness 
                ON spatial_ethnicity_patterns(success_rate DESC, confirmation_count DESC);
                
                CREATE INDEX IF NOT EXISTS idx_file_sessions_identifier 
                ON file_processing_sessions(source_file_identifier);
            ''')
            logger.info("Ethnicity confirmation database schema initialized")
    
    def initialize_canonical_ethnicities(self) -> None:
        """Initialize canonical ethnicity data with South African-specific values.
        
        Loads the standard South African ethnicity classifications in order
        of frequency/importance for dropdown presentation.
        """
        canonical_ethnicities = [
            CanonicalEthnicity('african', 'African', 1, 'African/Black ethnicity'),
            CanonicalEthnicity('white', 'White', 2, 'White/Caucasian ethnicity'),
            CanonicalEthnicity('coloured', 'Coloured', 3, 'Coloured ethnicity'),
            CanonicalEthnicity('indian', 'Indian', 4, 'Indian ethnicity'),
            CanonicalEthnicity('asian', 'Asian', 5, 'Asian ethnicity (non-Indian)'),
            CanonicalEthnicity('cape_malay', 'Cape Malay', 6, 'Cape Malay ethnicity'),
            CanonicalEthnicity('other', 'Other', 7, 'Other ethnicity not listed'),
            CanonicalEthnicity('unknown', 'Unknown', 8, 'Ethnicity unknown or unclear'),
            CanonicalEthnicity('declined', 'Declined to State', 9, 'Declined to provide ethnicity')
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            for ethnicity in canonical_ethnicities:
                try:
                    conn.execute('''
                        INSERT OR IGNORE INTO canonical_ethnicities 
                        (ethnicity_code, ethnicity_display_name, ethnicity_order, 
                         ethnicity_description, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        ethnicity.ethnicity_code,
                        ethnicity.ethnicity_display_name,
                        ethnicity.ethnicity_order,
                        ethnicity.ethnicity_description,
                        ethnicity.is_active,
                        datetime.now()
                    ))
                except sqlite3.IntegrityError as e:
                    logger.warning("Canonical ethnicity already exists", 
                                 ethnicity_code=ethnicity.ethnicity_code,
                                 error=str(e))
        
        logger.info("Canonical ethnicities initialized", count=len(canonical_ethnicities))
    
    def get_canonical_ethnicities_for_dropdown(self) -> List[str]:
        """Get ordered list of ethnicity display names for dropdown validation.
        
        Returns:
            List of ethnicity display names ordered by ethnicity_order
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT ethnicity_display_name 
                FROM canonical_ethnicities 
                WHERE is_active = true 
                ORDER BY ethnicity_order
            ''')
            return [row[0] for row in cursor.fetchall()]
    
    def validate_ethnicity(self, ethnicity_display_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Validate ethnicity display name and return canonical code.
        
        Args:
            ethnicity_display_name: Human-readable ethnicity name
            
        Returns:
            Tuple of (ethnicity_code, error_message). If valid, error_message is None.
        """
        if not ethnicity_display_name or not ethnicity_display_name.strip():
            return None, "Ethnicity cannot be empty"
        
        ethnicity_name = ethnicity_display_name.strip()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT ethnicity_code 
                FROM canonical_ethnicities 
                WHERE ethnicity_display_name = ? AND is_active = true
            ''', (ethnicity_name,))
            
            result = cursor.fetchone()
            if result:
                return result[0], None
            else:
                # Get available options for error message
                cursor = conn.execute('''
                    SELECT ethnicity_display_name 
                    FROM canonical_ethnicities 
                    WHERE is_active = true 
                    ORDER BY ethnicity_order
                ''')
                valid_options = [row[0] for row in cursor.fetchall()]
                return None, f"Invalid ethnicity '{ethnicity_name}'. Valid options: {', '.join(valid_options)}"
    
    def store_confirmation_record(self, confirmation: EthnicityConfirmation) -> str:
        """Store ethnicity confirmation record.
        
        Args:
            confirmation: EthnicityConfirmation instance to store
            
        Returns:
            confirmation_id: The stored confirmation identifier
            
        Raises:
            ValueError: If confirmation data is invalid
            sqlite3.IntegrityError: If confirmation already exists
        """
        # Validate confirmed ethnicity if provided
        if confirmation.confirmed_ethnicity:
            ethnicity_code, error = self.validate_ethnicity(confirmation.confirmed_ethnicity)
            if error:
                raise ValueError(f"Invalid confirmed ethnicity: {error}")
            confirmation.confirmed_ethnicity = ethnicity_code
        
        # Generate spatial context hash
        if not confirmation.spatial_context_hash:
            confirmation.spatial_context_hash = generate_spatial_context_hash(
                confirmation.original_director_name,
                confirmation.canonical_suburb,
                confirmation.canonical_city,
                confirmation.canonical_province
            )
        
        # Set timestamps
        now = datetime.now()
        if not confirmation.created_at:
            confirmation.created_at = now
        confirmation.updated_at = now
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO ethnicity_confirmations (
                        confirmation_id, source_file_identifier, source_row_number, source_job_id,
                        original_entity_name, original_director_name, original_registered_address,
                        original_registered_city, original_registered_province,
                        canonical_suburb, canonical_city, canonical_province, spatial_context_hash,
                        ai_predicted_ethnicity, ai_confidence_score, ai_classification_method,
                        confirmed_ethnicity, confirmed_by, confirmed_at, 
                        confirmation_notes, confirmation_source,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    confirmation.confirmation_id,
                    confirmation.source_file_identifier,
                    confirmation.source_row_number,
                    confirmation.source_job_id,
                    confirmation.original_entity_name,
                    confirmation.original_director_name,
                    confirmation.original_registered_address,
                    confirmation.original_registered_city,
                    confirmation.original_registered_province,
                    confirmation.canonical_suburb,
                    confirmation.canonical_city,
                    confirmation.canonical_province,
                    confirmation.spatial_context_hash,
                    confirmation.ai_predicted_ethnicity,
                    confirmation.ai_confidence_score,
                    confirmation.ai_classification_method,
                    confirmation.confirmed_ethnicity,
                    confirmation.confirmed_by,
                    confirmation.confirmed_at,
                    confirmation.confirmation_notes,
                    confirmation.confirmation_source,
                    confirmation.created_at,
                    confirmation.updated_at
                ))
                
                logger.info("Confirmation record stored",
                           confirmation_id=confirmation.confirmation_id,
                           source_file=confirmation.source_file_identifier,
                           row_number=confirmation.source_row_number,
                           director_name=confirmation.original_director_name)
                
                return confirmation.confirmation_id
                
        except sqlite3.IntegrityError as e:
            logger.error("Confirmation record storage failed",
                        confirmation_id=confirmation.confirmation_id,
                        error=str(e))
            raise ValueError(f"Failed to store confirmation record: {e}")
    
    def get_confirmations_for_job(self, job_id: str) -> List[EthnicityConfirmation]:
        """Get all confirmation records for a specific job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            List of EthnicityConfirmation instances
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM ethnicity_confirmations 
                WHERE source_job_id = ?
                ORDER BY source_row_number
            ''', (job_id,))
            
            confirmations = []
            for row in cursor.fetchall():
                confirmation = EthnicityConfirmation(
                    confirmation_id=row['confirmation_id'],
                    source_file_identifier=row['source_file_identifier'],
                    source_row_number=row['source_row_number'],
                    source_job_id=row['source_job_id'],
                    original_entity_name=row['original_entity_name'],
                    original_director_name=row['original_director_name'],
                    original_registered_address=row['original_registered_address'],
                    original_registered_city=row['original_registered_city'],
                    original_registered_province=row['original_registered_province'],
                    canonical_suburb=row['canonical_suburb'],
                    canonical_city=row['canonical_city'],
                    canonical_province=row['canonical_province'],
                    spatial_context_hash=row['spatial_context_hash'],
                    ai_predicted_ethnicity=row['ai_predicted_ethnicity'],
                    ai_confidence_score=row['ai_confidence_score'],
                    ai_classification_method=row['ai_classification_method'],
                    confirmed_ethnicity=row['confirmed_ethnicity'],
                    confirmed_by=row['confirmed_by'],
                    confirmed_at=datetime.fromisoformat(row['confirmed_at']) if row['confirmed_at'] else None,
                    confirmation_notes=row['confirmation_notes'],
                    confirmation_source=row['confirmation_source'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                )
                confirmations.append(confirmation)
            
            logger.debug("Retrieved confirmations for job",
                        job_id=job_id,
                        count=len(confirmations))
            
            return confirmations
    
    def get_canonical_ethnicities_list(self) -> List[str]:
        """Get list of canonical ethnicity display names for validation.
        
        Returns:
            List of ethnicity display names
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT ethnicity_display_name 
                FROM canonical_ethnicities 
                WHERE is_active = true 
                ORDER BY ethnicity_order
            ''')
            return [row[0] for row in cursor.fetchall()]
    
    def bulk_store_confirmations(self, confirmations: List[EthnicityConfirmation]) -> int:
        """Bulk store confirmation records with transaction safety.
        
        Args:
            confirmations: List of EthnicityConfirmation instances to store
            
        Returns:
            Number of successfully stored confirmations
            
        Raises:
            RuntimeError: If bulk storage fails
        """
        if not confirmations:
            return 0
        
        stored_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Use transaction for bulk insert
                conn.execute('BEGIN TRANSACTION')
                
                for confirmation in confirmations:
                    try:
                        # Validate confirmed ethnicity if provided
                        if confirmation.confirmed_ethnicity:
                            ethnicity_code, error = self.validate_ethnicity(confirmation.confirmed_ethnicity)
                            if error:
                                logger.warning("Invalid ethnicity in bulk insert",
                                             confirmation_id=confirmation.confirmation_id,
                                             ethnicity=confirmation.confirmed_ethnicity,
                                             error=error)
                                continue
                            confirmation.confirmed_ethnicity = ethnicity_code
                        
                        # Set timestamps
                        now = datetime.now()
                        if not confirmation.created_at:
                            confirmation.created_at = now
                        confirmation.updated_at = now
                        
                        # Insert confirmation
                        conn.execute('''
                            INSERT INTO ethnicity_confirmations (
                                confirmation_id, source_file_identifier, source_row_number, source_job_id,
                                original_entity_name, original_director_name, original_registered_address,
                                original_registered_city, original_registered_province,
                                canonical_suburb, canonical_city, canonical_province, spatial_context_hash,
                                ai_predicted_ethnicity, ai_confidence_score, ai_classification_method,
                                confirmed_ethnicity, confirmed_by, confirmed_at, 
                                confirmation_notes, confirmation_source,
                                created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            confirmation.confirmation_id,
                            confirmation.source_file_identifier,
                            confirmation.source_row_number,
                            confirmation.source_job_id,
                            confirmation.original_entity_name,
                            confirmation.original_director_name,
                            confirmation.original_registered_address,
                            confirmation.original_registered_city,
                            confirmation.original_registered_province,
                            confirmation.canonical_suburb,
                            confirmation.canonical_city,
                            confirmation.canonical_province,
                            confirmation.spatial_context_hash,
                            confirmation.ai_predicted_ethnicity,
                            confirmation.ai_confidence_score,
                            confirmation.ai_classification_method,
                            confirmation.confirmed_ethnicity,
                            confirmation.confirmed_by,
                            confirmation.confirmed_at,
                            confirmation.confirmation_notes,
                            confirmation.confirmation_source,
                            confirmation.created_at,
                            confirmation.updated_at
                        ))
                        
                        stored_count += 1
                        
                    except sqlite3.IntegrityError as e:
                        logger.warning("Duplicate confirmation skipped in bulk insert",
                                     confirmation_id=confirmation.confirmation_id,
                                     error=str(e))
                        continue
                    except Exception as e:
                        logger.error("Failed to store confirmation in bulk insert",
                                   confirmation_id=confirmation.confirmation_id,
                                   error=str(e))
                        continue
                
                # Commit transaction
                conn.execute('COMMIT')
                
                logger.info("Bulk confirmation storage completed",
                           requested_count=len(confirmations),
                           stored_count=stored_count)
                
                return stored_count
                
        except Exception as e:
            logger.error("Bulk confirmation storage failed",
                        confirmation_count=len(confirmations),
                        error=str(e))
            raise RuntimeError(f"Bulk storage failed: {e}")
    
    async def get_confirmation_status(self, job_id: str, detailed: bool = False) -> Optional[Dict[str, Any]]:
        """Get comprehensive confirmation status for a job.
        
        Args:
            job_id: Job identifier
            detailed: Whether to include detailed breakdown
            
        Returns:
            Dictionary with confirmation status and analytics
        """
        try:
            # Need to connect to job database to get lead counts
            job_db_path = Path("cache/jobs.db")
            
            with sqlite3.connect(job_db_path) as job_conn:
                job_conn.row_factory = sqlite3.Row
                # Get job totals from job database
                job_cursor = job_conn.execute('''
                    SELECT COUNT(*) as total_leads 
                    FROM lead_processing_results 
                    WHERE job_id = ? AND processing_status = 'success'
                ''', (job_id,))
                job_result = job_cursor.fetchone()
                total_leads = job_result['total_leads'] if job_result else 0
                
                if total_leads == 0:
                    return None
            
            # Now connect to confirmation database
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get confirmation counts
                confirmation_cursor = conn.execute('''
                    SELECT COUNT(*) as confirmed_leads
                    FROM ethnicity_confirmations 
                    WHERE source_job_id = ?
                ''', (job_id,))
                confirmation_result = confirmation_cursor.fetchone()
                confirmed_leads = confirmation_result['confirmed_leads'] if confirmation_result else 0
                
                # Calculate coverage
                confirmation_percentage = (confirmed_leads / total_leads * 100) if total_leads > 0 else 0
                pending_confirmations = total_leads - confirmed_leads
                
                # Get ethnicity distribution
                ethnicity_cursor = conn.execute('''
                    SELECT confirmed_ethnicity, COUNT(*) as count
                    FROM ethnicity_confirmations 
                    WHERE source_job_id = ?
                    GROUP BY confirmed_ethnicity
                    ORDER BY count DESC
                ''', (job_id,))
                ethnicity_distribution = {row['confirmed_ethnicity']: row['count'] 
                                        for row in ethnicity_cursor.fetchall()}
                
                # Get accuracy metrics
                accuracy_cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_confirmed,
                        SUM(CASE WHEN ai_predicted_ethnicity = confirmed_ethnicity THEN 1 ELSE 0 END) as correct_predictions,
                        SUM(CASE WHEN ai_confidence_score >= 0.8 AND ai_predicted_ethnicity = confirmed_ethnicity THEN 1 ELSE 0 END) as high_confidence_correct,
                        SUM(CASE WHEN ai_confidence_score >= 0.8 THEN 1 ELSE 0 END) as high_confidence_total,
                        SUM(CASE WHEN ai_confidence_score < 0.6 AND ai_predicted_ethnicity = confirmed_ethnicity THEN 1 ELSE 0 END) as low_confidence_correct,
                        SUM(CASE WHEN ai_confidence_score < 0.6 THEN 1 ELSE 0 END) as low_confidence_total
                    FROM ethnicity_confirmations 
                    WHERE source_job_id = ? AND ai_predicted_ethnicity IS NOT NULL
                ''', (job_id,))
                accuracy_result = accuracy_cursor.fetchone()
                
                accuracy_metrics = {}
                if accuracy_result and accuracy_result['total_confirmed'] > 0:
                    accuracy_metrics = {
                        'agreement_percentage': (accuracy_result['correct_predictions'] / accuracy_result['total_confirmed'] * 100),
                        'high_confidence_correct': (accuracy_result['high_confidence_correct'] / accuracy_result['high_confidence_total'] * 100) if accuracy_result['high_confidence_total'] > 0 else 0,
                        'low_confidence_correct': (accuracy_result['low_confidence_correct'] / accuracy_result['low_confidence_total'] * 100) if accuracy_result['low_confidence_total'] > 0 else 0
                    }
                
                # Build status response
                status = {
                    'job_id': job_id,
                    'total_leads': total_leads,
                    'confirmed_leads': confirmed_leads,
                    'confirmation_percentage': confirmation_percentage,
                    'pending_confirmations': pending_confirmations,
                    'ethnicity_distribution': ethnicity_distribution,
                    'accuracy_metrics': accuracy_metrics
                }
                
                # Add detailed breakdown if requested
                if detailed:
                    method_cursor = conn.execute('''
                        SELECT 
                            ai_classification_method,
                            COUNT(*) as total,
                            SUM(CASE WHEN ai_predicted_ethnicity = confirmed_ethnicity THEN 1 ELSE 0 END) as correct
                        FROM ethnicity_confirmations 
                        WHERE source_job_id = ? AND ai_classification_method IS NOT NULL
                        GROUP BY ai_classification_method
                    ''', (job_id,))
                    
                    detailed_breakdown = {}
                    for row in method_cursor.fetchall():
                        method = row['ai_classification_method']
                        total = row['total']
                        correct = row['correct']
                        accuracy = (correct / total * 100) if total > 0 else 0
                        
                        detailed_breakdown[method] = {
                            'total': total,
                            'confirmed': total,  # All are confirmed since they're in confirmations table
                            'accuracy': accuracy
                        }
                    
                    status['detailed_breakdown'] = detailed_breakdown
                
                # Add learning integration info
                learning_cursor = conn.execute('''
                    SELECT 
                        COUNT(DISTINCT spatial_context_hash) as spatial_contexts,
                        COUNT(*) as patterns_updated
                    FROM ethnicity_confirmations 
                    WHERE source_job_id = ?
                ''', (job_id,))
                learning_result = learning_cursor.fetchone()
                
                if learning_result:
                    status['learning_integration'] = {
                        'patterns_updated': learning_result['patterns_updated'] or 0,
                        'spatial_contexts': learning_result['spatial_contexts'] or 0,
                        'contribution_score': 0.0  # Would be calculated if field existed
                    }
                
                logger.info("Generated confirmation status",
                           job_id=job_id,
                           total_leads=total_leads,
                           confirmed_leads=confirmed_leads,
                           confirmation_percentage=confirmation_percentage)
                
                return status
                
        except Exception as e:
            logger.error("Failed to get confirmation status",
                        job_id=job_id,
                        error=str(e))
            return None

def generate_file_identifier(file_path: Path) -> str:
    """Generate unique identifier for source file tracking.
    
    Creates a unique identifier combining filename and content hash
    for precise file tracking across processing sessions.
    
    Args:
        file_path: Path to the source file
        
    Returns:
        Unique file identifier in format: filename_hash
    """
    file_name = file_path.stem  # Filename without extension
    
    # Generate MD5 hash of file content for uniqueness
    with open(file_path, 'rb') as f:
        content_hash = hashlib.md5(f.read()).hexdigest()[:8]
    
    # Format: filename_hash (e.g., "leads_2024_a1b2c3d4")
    identifier = f"{file_name}_{content_hash}"
    
    logger.debug("Generated file identifier",
                file_path=str(file_path),
                identifier=identifier)
    
    return identifier

def generate_spatial_context_hash(director_name: str, suburb: Optional[str], 
                                 city: Optional[str], province: Optional[str]) -> str:
    """Generate hash for spatial context lookups.
    
    Creates a hash of the spatial context for efficient pattern matching
    and correlation analysis.
    
    Args:
        director_name: Director name to include in context
        suburb: Suburb/area name (optional)
        city: City name (optional)
        province: Province name (optional)
        
    Returns:
        16-character spatial context hash
    """
    def normalize_name(name: str) -> str:
        """Normalize name for consistent hashing."""
        return name.lower().strip() if name else ''
    
    def normalize_place(place: str) -> str:
        """Normalize place name for consistent hashing."""
        return place.lower().strip().replace(' ', '') if place else ''
    
    components = [
        normalize_name(director_name),
        normalize_place(suburb) if suburb else '',
        normalize_place(city) if city else '',
        normalize_place(province) if province else ''
    ]
    
    context_string = '|'.join(filter(None, components))
    context_hash = hashlib.sha256(context_string.encode()).hexdigest()[:16]
    
    logger.debug("Generated spatial context hash",
                director_name=director_name,
                context_string=context_string,
                hash=context_hash)
    
    return context_hash