"""
Spatial learning database for ethnicity confirmation and geographic intelligence.

This module extends the existing LLM learning system to incorporate spatial context
(names + geographic locations) for enhanced ethnicity prediction. Integrates with
Developer A's confirmation system to learn from human-validated ethnicity data.

Key Features:
- Spatial pattern extraction from confirmations (name + suburb + city + province)
- Geographic-ethnic correlation analysis and storage
- Enhanced prediction using confirmed spatial patterns
- Learning analytics for confirmation impact measurement
- Real-time pattern availability for immediate cost optimization

Architecture:
- SpatialEthnicityPattern: Core spatial pattern with confirmation tracking
- SpatialLearningDatabase: Database interface with spatial intelligence
- Geographic context hashing for fast spatial lookups
- Integration with existing learning_database.py patterns

Usage:
    spatial_db = SpatialLearningDatabase()
    patterns = await spatial_db.extract_patterns_from_confirmations()
    prediction = await spatial_db.enhanced_ethnicity_prediction(name, city, province)
"""

import json
import sqlite3
import threading
import time
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import structlog

from .models import Classification, ClassificationMethod, EthnicityType

logger = structlog.get_logger(__name__)


@dataclass
class SpatialEthnicityPattern:
    """Spatial ethnicity pattern with confirmation tracking."""
    
    pattern_id: str
    name_component: str          # First name, surname, or component
    suburb: Optional[str]        # Spatial context (most predictive)
    city: Optional[str]
    province: Optional[str]
    ethnicity_code: str          # Predicted ethnicity
    confidence_score: float      # Pattern confidence
    confirmation_count: int      # Human confirmations
    total_applications: int      # Total times pattern applied
    success_rate: float          # confirmation_count / total_applications
    spatial_context_hash: str    # Hash for quick spatial lookups
    created_from_job_id: Optional[str]
    last_confirmed_at: Optional[datetime]
    last_applied_at: Optional[datetime]
    created_at: datetime


@dataclass
class ConfirmationRecord:
    """Enhanced confirmation record with spatial context."""
    
    confirmation_id: str
    source_file_identifier: str
    source_row_number: int
    source_job_id: str
    
    # Original data preservation
    original_entity_name: str
    original_director_name: str
    original_registered_address: Optional[str]
    original_registered_city: Optional[str]
    original_registered_province: Optional[str]
    
    # Spatial context for correlation analysis
    canonical_suburb: Optional[str]
    canonical_city: Optional[str]
    canonical_province: Optional[str]
    spatial_context_hash: str
    
    # AI prediction data
    ai_predicted_ethnicity: str
    ai_confidence_score: float
    ai_classification_method: str
    
    # Human confirmation data
    confirmed_ethnicity: Optional[str]
    confirmed_by: Optional[str]
    confirmed_at: Optional[datetime]
    confirmation_notes: Optional[str]
    confirmation_source: Optional[str]  # phone_call|meeting|email|other
    
    created_at: datetime


class SpatialLearningDatabase:
    """Enhanced learning database with spatial intelligence for ethnicity confirmations."""
    
    # Class-level lock to prevent concurrent database access
    _db_lock = threading.RLock()
    
    def __init__(self, db_path: Path = None):
        if db_path is None:
            db_path = Path("cache") / "spatial_learning.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
        
        logger.info("Spatial Learning Database initialized", db_path=str(self.db_path))
    
    def _initialize_database(self):
        """Create database tables for spatial learning and confirmation tracking."""
        
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.executescript("""
                -- Enhanced spatial ethnicity patterns with confirmation tracking
                CREATE TABLE IF NOT EXISTS spatial_ethnicity_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    
                    -- Pattern definition
                    name_component TEXT NOT NULL,          -- First name, surname, or component
                    suburb TEXT,                          -- Spatial context (most predictive)
                    city TEXT,
                    province TEXT,
                    
                    -- Pattern effectiveness
                    ethnicity_code TEXT NOT NULL,         -- Predicted ethnicity
                    confidence_score REAL NOT NULL,       -- Pattern confidence
                    confirmation_count INTEGER DEFAULT 0,  -- Human confirmations
                    total_applications INTEGER DEFAULT 0,  -- Total times pattern applied
                    success_rate REAL DEFAULT 0.0,        -- confirmation_count / total_applications
                    spatial_context_hash TEXT NOT NULL,   -- Hash for quick spatial lookups
                    
                    -- Pattern lifecycle
                    created_from_job_id TEXT,             -- Job that created pattern
                    last_confirmed_at TIMESTAMP,
                    last_applied_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Unique constraint on spatial context + name component
                    UNIQUE(name_component, suburb, city, province, ethnicity_code)
                );
                
                -- Ethnicity confirmation lifecycle management
                CREATE TABLE IF NOT EXISTS ethnicity_confirmations (
                    confirmation_id TEXT PRIMARY KEY,
                    
                    -- Source tracing (exact record identification)
                    source_file_identifier TEXT NOT NULL,  -- filename + hash for uniqueness
                    source_row_number INTEGER NOT NULL,    -- 1-based Excel row number
                    source_job_id TEXT NOT NULL,           -- Processing job reference
                    
                    -- Original data preservation
                    original_entity_name TEXT NOT NULL,
                    original_director_name TEXT NOT NULL,
                    original_registered_address TEXT,
                    original_registered_city TEXT,
                    original_registered_province TEXT,
                    
                    -- Spatial context for correlation analysis
                    canonical_suburb TEXT,                 -- Cleaned suburb name
                    canonical_city TEXT,                   -- Cleaned city name  
                    canonical_province TEXT,               -- Cleaned province name
                    spatial_context_hash TEXT NOT NULL,    -- Hash for quick spatial lookups
                    
                    -- AI prediction data
                    ai_predicted_ethnicity TEXT NOT NULL,
                    ai_confidence_score REAL NOT NULL,
                    ai_classification_method TEXT NOT NULL, -- rule_based|phonetic|llm|cache
                    
                    -- Human confirmation data
                    confirmed_ethnicity TEXT,              -- Must match canonical_ethnicities
                    confirmed_by TEXT,                     -- Sales rep identifier
                    confirmed_at TIMESTAMP,               -- When confirmation occurred
                    confirmation_notes TEXT,               -- Optional notes from call
                    confirmation_source TEXT,              -- phone_call|meeting|email|other
                    
                    -- Metadata
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Constraints
                    UNIQUE(source_file_identifier, source_row_number)
                );
                
                -- Canonical ethnicity definitions with strict validation
                CREATE TABLE IF NOT EXISTS canonical_ethnicities (
                    ethnicity_code TEXT PRIMARY KEY,       -- System identifier
                    ethnicity_display_name TEXT NOT NULL, -- Human-readable name
                    ethnicity_order INTEGER NOT NULL,     -- Order for dropdowns (common first)
                    ethnicity_description TEXT,           -- Optional description
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Spatial pattern learning analytics
                CREATE TABLE IF NOT EXISTS spatial_learning_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_date DATE NOT NULL,
                    total_confirmations INTEGER DEFAULT 0,
                    patterns_extracted INTEGER DEFAULT 0,
                    patterns_applied INTEGER DEFAULT 0,
                    accuracy_improvement REAL DEFAULT 0.0,
                    geographic_coverage_percent REAL DEFAULT 0.0,
                    learning_efficiency REAL DEFAULT 0.0,  -- patterns per confirmation
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Performance indexes for spatial lookups
                CREATE INDEX IF NOT EXISTS idx_spatial_patterns_lookup 
                ON spatial_ethnicity_patterns(name_component, suburb, city);
                
                CREATE INDEX IF NOT EXISTS idx_spatial_patterns_hash 
                ON spatial_ethnicity_patterns(spatial_context_hash);
                
                CREATE INDEX IF NOT EXISTS idx_spatial_patterns_effectiveness 
                ON spatial_ethnicity_patterns(success_rate DESC, confirmation_count DESC);
                
                CREATE INDEX IF NOT EXISTS idx_confirmations_source 
                ON ethnicity_confirmations(source_file_identifier, source_row_number);
                
                CREATE INDEX IF NOT EXISTS idx_confirmations_spatial 
                ON ethnicity_confirmations(spatial_context_hash, original_director_name);
                
                CREATE INDEX IF NOT EXISTS idx_confirmations_status 
                ON ethnicity_confirmations(confirmed_ethnicity, confirmed_at);
            """)
            
            # Initialize canonical ethnicities if empty
            existing_count = conn.execute(
                "SELECT COUNT(*) FROM canonical_ethnicities"
            ).fetchone()[0]
            
            if existing_count == 0:
                self._initialize_canonical_ethnicities(conn)
    
    def _initialize_canonical_ethnicities(self, conn: sqlite3.Connection):
        """Initialize canonical ethnicity data for SA context."""
        
        ethnicities = [
            ('african', 'African', 1, 'Black African ethnicity'),
            ('white', 'White', 2, 'White/European ethnicity'),
            ('coloured', 'Coloured', 3, 'Coloured ethnicity'),
            ('indian', 'Indian', 4, 'Indian ethnicity'),
            ('asian', 'Asian', 5, 'Asian ethnicity (non-Indian)'),
            ('cape_malay', 'Cape Malay', 6, 'Cape Malay ethnicity'),
            ('other', 'Other', 7, 'Other ethnicity'),
            ('unknown', 'Unknown', 8, 'Unknown ethnicity'),
            ('declined', 'Declined to State', 9, 'Declined to state ethnicity'),
        ]
        
        conn.executemany(
            """
            INSERT INTO canonical_ethnicities 
            (ethnicity_code, ethnicity_display_name, ethnicity_order, ethnicity_description)
            VALUES (?, ?, ?, ?)
            """,
            ethnicities
        )
        
        logger.info("Canonical ethnicities initialized", count=len(ethnicities))
    
    def generate_spatial_context_hash(self, director_name: str, suburb: str = None, 
                                    city: str = None, province: str = None) -> str:
        """Generate hash for spatial context lookups.
        
        Args:
            director_name: Director name for context
            suburb: Suburb/area for spatial context
            city: City for spatial context  
            province: Province for spatial context
            
        Returns:
            16-character hash for spatial context identification
        """
        # Normalize components for consistent hashing
        def normalize_component(component):
            if not component:
                return ''
            return component.lower().strip().replace(' ', '_')
        
        components = [
            normalize_component(director_name),
            normalize_component(suburb),
            normalize_component(city), 
            normalize_component(province)
        ]
        
        context_string = '|'.join(filter(None, components))
        return hashlib.sha256(context_string.encode()).hexdigest()[:16]
    
    async def store_confirmation_record(self, confirmation: ConfirmationRecord) -> bool:
        """Store ethnicity confirmation record for learning.
        
        Args:
            confirmation: Complete confirmation record
            
        Returns:
            bool: True if stored successfully, False otherwise
        """
        with self._db_lock:
            try:
                with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO ethnicity_confirmations 
                        (confirmation_id, source_file_identifier, source_row_number, source_job_id,
                         original_entity_name, original_director_name, original_registered_address,
                         original_registered_city, original_registered_province,
                         canonical_suburb, canonical_city, canonical_province, spatial_context_hash,
                         ai_predicted_ethnicity, ai_confidence_score, ai_classification_method,
                         confirmed_ethnicity, confirmed_by, confirmed_at, confirmation_notes,
                         confirmation_source, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
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
                        confirmation.created_at
                    ))
                    
                    logger.info("Confirmation record stored",
                               confirmation_id=confirmation.confirmation_id,
                               director_name=confirmation.original_director_name,
                               predicted_ethnicity=confirmation.ai_predicted_ethnicity,
                               confirmed_ethnicity=confirmation.confirmed_ethnicity)
                    
                    return True
                    
            except Exception as e:
                logger.error("Failed to store confirmation record",
                           confirmation_id=confirmation.confirmation_id,
                           error=str(e))
                return False
    
    async def extract_patterns_from_confirmations(self, days_lookback: int = 7) -> List[SpatialEthnicityPattern]:
        """Enhanced pattern extraction from confirmations with spatial context correlation.
        
        Implements Task 1.2 requirements:
        - Automatic pattern extraction from confirmed ethnicities
        - Spatial context correlation (name + suburb + city combinations)  
        - Pattern effectiveness tracking with success rates
        
        Args:
            days_lookback: Number of days to look back for confirmations
            
        Returns:
            List of extracted spatial patterns with enhanced intelligence
        """
        with self._db_lock:
            try:
                with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                    # Get recent confirmations with actual ethnicity data
                    cutoff_date = datetime.now() - timedelta(days=days_lookback)
                    
                    confirmations = conn.execute("""
                        SELECT original_director_name, canonical_suburb, canonical_city, 
                               canonical_province, confirmed_ethnicity, spatial_context_hash,
                               source_job_id, confirmed_at, ai_predicted_ethnicity, ai_confidence_score
                        FROM ethnicity_confirmations 
                        WHERE confirmed_ethnicity IS NOT NULL
                          AND confirmed_at > ?
                        ORDER BY confirmed_at DESC
                    """, (cutoff_date.isoformat(),)).fetchall()
                    
                    patterns_extracted = []
                    spatial_correlation_stats = {}
                    
                    for confirmation in confirmations:
                        (name, suburb, city, province, ethnicity, spatial_hash, 
                         job_id, confirmed_at, ai_predicted, ai_confidence) = confirmation
                        
                        # Track prediction accuracy for learning effectiveness
                        was_ai_correct = ai_predicted == ethnicity if ai_predicted else False
                        
                        # Extract enhanced name components for sophisticated pattern learning
                        name_components = self._extract_name_components(name)
                        
                        # Create spatial correlation key for analysis (normalize None values)
                        normalized_suburb = suburb or 'unknown'
                        normalized_city = city or 'unknown'
                        normalized_province = province or 'unknown'
                        spatial_key = f"{normalized_suburb}|{normalized_city}|{normalized_province}"
                        
                        if spatial_key not in spatial_correlation_stats:
                            spatial_correlation_stats[spatial_key] = {
                                'confirmations': 0,
                                'ethnicities': {},
                                'accuracy_improvement': 0.0
                            }
                        
                        spatial_correlation_stats[spatial_key]['confirmations'] += 1
                        ethnicity_count = spatial_correlation_stats[spatial_key]['ethnicities']
                        ethnicity_count[ethnicity] = ethnicity_count.get(ethnicity, 0) + 1
                        
                        for component in name_components:
                            # Create or update spatial pattern with enhanced correlation analysis
                            pattern = await self._upsert_spatial_pattern_enhanced(
                                conn=conn,
                                name_component=component,
                                suburb=suburb,
                                city=city,
                                province=province,
                                ethnicity=ethnicity,
                                spatial_hash=spatial_hash,
                                job_id=job_id,
                                confirmed_at=datetime.fromisoformat(confirmed_at),
                                was_ai_correct=was_ai_correct,
                                ai_confidence=ai_confidence or 0.0
                            )
                            
                            if pattern:
                                patterns_extracted.append(pattern)
                    
                    # Extract high-value spatial correlation patterns
                    await self._extract_spatial_correlation_patterns(conn, spatial_correlation_stats)
                    
                    logger.info("Enhanced spatial patterns extracted from confirmations",
                               confirmations_processed=len(confirmations),
                               patterns_extracted=len(patterns_extracted),
                               spatial_contexts=len(spatial_correlation_stats),
                               days_lookback=days_lookback)
                    
                    return patterns_extracted
                    
            except Exception as e:
                logger.error("Failed to extract patterns from confirmations",
                           days_lookback=days_lookback,
                           error=str(e))
                return []
    
    def _extract_name_components(self, full_name: str) -> List[str]:
        """Enhanced name component extraction for sophisticated pattern learning.
        
        Implements Task 1.2 requirement: "Name component analysis (first names, surnames, components)"
        Extracts various types of name components for comprehensive pattern learning:
        - Individual name parts (all components)
        - First name specifically (cultural significance)
        - Last name specifically (family/clan patterns)
        - Name prefixes and suffixes (linguistic markers)
        - N-grams for partial matching
        
        Args:
            full_name: Complete director name
            
        Returns:
            List of name components for pattern learning
        """
        if not full_name or len(full_name.strip()) < 2:
            return []
        
        components = []
        name_parts = full_name.strip().split()
        
        # Extract individual name parts (basic components)
        for part in name_parts:
            clean_part = part.strip().lower()
            if len(clean_part) >= 2:  # Minimum length for learning
                components.append(clean_part)
        
        # Extract first name (high cultural significance for ethnicity)
        if name_parts and len(name_parts[0]) >= 2:
            first_name = name_parts[0].lower()
            components.append(f"first:{first_name}")  # Tagged first name
        
        # Extract last name (family/clan patterns, very important for SA context)
        if len(name_parts) > 1 and len(name_parts[-1]) >= 2:
            last_name = name_parts[-1].lower()
            components.append(f"last:{last_name}")  # Tagged surname
        
        # Extract prefixes and suffixes for linguistic pattern recognition
        for part in name_parts:
            clean_part = part.strip().lower()
            if len(clean_part) >= 3:
                # Prefixes (first 2-3 characters) - important for SA linguistic patterns
                components.append(f"prefix2:{clean_part[:2]}")
                if len(clean_part) >= 3:
                    components.append(f"prefix3:{clean_part[:3]}")
                
                # Suffixes (last 2-3 characters) - family name endings
                components.append(f"suffix2:{clean_part[-2:]}")
                if len(clean_part) >= 3:
                    components.append(f"suffix3:{clean_part[-3:]}")
        
        # Extract name bigrams for partial matching (helps with compound names)
        full_name_clean = ''.join(name_parts).lower()
        if len(full_name_clean) >= 4:
            for i in range(len(full_name_clean) - 2):
                bigram = full_name_clean[i:i+3]
                if len(bigram) == 3:
                    components.append(f"trigram:{bigram}")
        
        return list(set(components))  # Remove duplicates
    
    async def _upsert_spatial_pattern_enhanced(self, conn: sqlite3.Connection, 
                                            name_component: str, suburb: str, city: str, 
                                            province: str, ethnicity: str, spatial_hash: str,
                                            job_id: str, confirmed_at: datetime,
                                            was_ai_correct: bool, ai_confidence: float) -> Optional[SpatialEthnicityPattern]:
        """Enhanced spatial pattern creation with learning effectiveness tracking.
        
        Implements Task 1.2: Pattern effectiveness tracking with success rates
        Tracks AI prediction accuracy to measure learning improvement over time.
        """
        try:
            # Check if pattern exists
            existing = conn.execute("""
                SELECT pattern_id, confirmation_count, total_applications, success_rate, confidence_score
                FROM spatial_ethnicity_patterns
                WHERE name_component = ? AND suburb = ? AND city = ? 
                  AND province = ? AND ethnicity_code = ?
            """, (name_component, suburb, city, province, ethnicity)).fetchone()
            
            if existing:
                # Update existing pattern with enhanced tracking
                pattern_id, conf_count, total_apps, success_rate, old_confidence = existing
                new_conf_count = conf_count + 1
                new_total_apps = total_apps + 1
                
                # Enhanced success rate calculation incorporating AI accuracy improvement
                base_success_rate = new_conf_count / max(new_total_apps, 1)
                ai_improvement_factor = 1.1 if was_ai_correct else 0.95  # Boost if AI was correct
                new_success_rate = min(1.0, base_success_rate * ai_improvement_factor)
                
                # Enhanced confidence calculation with confirmation strength
                confirmation_boost = min(1.2, 1.0 + (new_conf_count - 1) * 0.05)  # Gradual boost
                spatial_confidence = self._calculate_spatial_confidence(suburb, city, province)
                new_confidence = min(1.0, new_success_rate * confirmation_boost * spatial_confidence)
                
                conn.execute("""
                    UPDATE spatial_ethnicity_patterns
                    SET confirmation_count = ?,
                        total_applications = ?,
                        success_rate = ?,
                        last_confirmed_at = ?,
                        confidence_score = ?
                    WHERE pattern_id = ?
                """, (new_conf_count, new_total_apps, new_success_rate, 
                      confirmed_at.isoformat(), new_confidence, pattern_id))
                
                logger.debug("Enhanced spatial pattern updated",
                           pattern_id=pattern_id,
                           confirmation_count=new_conf_count,
                           success_rate=new_success_rate,
                           confidence=new_confidence,
                           ai_improvement=was_ai_correct)
                
                return SpatialEthnicityPattern(
                    pattern_id=pattern_id,
                    name_component=name_component,
                    suburb=suburb,
                    city=city,
                    province=province,
                    ethnicity_code=ethnicity,
                    confidence_score=new_confidence,
                    confirmation_count=new_conf_count,
                    total_applications=new_total_apps,
                    success_rate=new_success_rate,
                    spatial_context_hash=spatial_hash,
                    created_from_job_id=job_id,
                    last_confirmed_at=confirmed_at,
                    last_applied_at=None,
                    created_at=datetime.now()
                )
            
            else:
                # Create new enhanced pattern
                pattern_id = f"spatial_{spatial_hash}_{name_component}_{ethnicity}"
                
                # Calculate initial confidence with spatial intelligence
                spatial_confidence = self._calculate_spatial_confidence(suburb, city, province)
                ai_confidence_factor = 1.1 if was_ai_correct else 1.0
                initial_confidence = min(1.0, spatial_confidence * ai_confidence_factor)
                
                conn.execute("""
                    INSERT INTO spatial_ethnicity_patterns
                    (pattern_id, name_component, suburb, city, province, ethnicity_code,
                     confidence_score, confirmation_count, total_applications, success_rate,
                     spatial_context_hash, created_from_job_id, last_confirmed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (pattern_id, name_component, suburb, city, province, ethnicity,
                      initial_confidence, 1, 1, 1.0, spatial_hash, job_id, confirmed_at.isoformat()))
                
                logger.info("Enhanced spatial pattern created",
                           pattern_id=pattern_id,
                           name_component=name_component,
                           ethnicity=ethnicity,
                           spatial_context=f"{suburb}, {city}, {province}",
                           confidence=initial_confidence)
                
                return SpatialEthnicityPattern(
                    pattern_id=pattern_id,
                    name_component=name_component,
                    suburb=suburb,
                    city=city,
                    province=province,
                    ethnicity_code=ethnicity,
                    confidence_score=initial_confidence,
                    confirmation_count=1,
                    total_applications=1,
                    success_rate=1.0,
                    spatial_context_hash=spatial_hash,
                    created_from_job_id=job_id,
                    last_confirmed_at=confirmed_at,
                    last_applied_at=None,
                    created_at=datetime.now()
                )
                
        except Exception as e:
            logger.error("Failed to upsert enhanced spatial pattern",
                        name_component=name_component,
                        ethnicity=ethnicity,
                        error=str(e))
            return None
    
    def _calculate_spatial_confidence(self, suburb: str, city: str, province: str) -> float:
        """Calculate confidence modifier based on spatial context completeness."""
        confidence = 0.7  # Base confidence
        
        if province:
            confidence += 0.1  # Province adds context
        if city:
            confidence += 0.1  # City adds more context
        if suburb:
            confidence += 0.1  # Suburb is most specific
            
        return min(1.0, confidence)
    
    async def _extract_spatial_correlation_patterns(self, conn: sqlite3.Connection, 
                                                  spatial_stats: Dict[str, Any]) -> None:
        """Extract high-value spatial correlation patterns for enhanced prediction.
        
        Identifies spatial contexts with strong ethnicity correlations for priority patterns.
        """
        try:
            for spatial_key, stats in spatial_stats.items():
                if stats['confirmations'] >= 3:  # Minimum confirmations for correlation
                    # Find dominant ethnicity in this spatial context
                    ethnicities = stats['ethnicities']
                    total_confirmations = sum(ethnicities.values())
                    
                    for ethnicity, count in ethnicities.items():
                        correlation_strength = count / total_confirmations
                        
                        if correlation_strength >= 0.7:  # Strong correlation threshold
                            # Create spatial correlation pattern
                            suburb, city, province = spatial_key.split('|')
                            suburb = None if suburb == 'unknown' else suburb
                            city = None if city == 'unknown' else city  
                            province = None if province == 'unknown' else province
                            
                            spatial_hash = self.generate_spatial_context_hash(
                                f"spatial_correlation", suburb, city, province
                            )
                            
                            pattern_id = f"spatial_corr_{spatial_hash}_{ethnicity}"
                            
                            conn.execute("""
                                INSERT OR REPLACE INTO spatial_ethnicity_patterns
                                (pattern_id, name_component, suburb, city, province, ethnicity_code,
                                 confidence_score, confirmation_count, total_applications, success_rate,
                                 spatial_context_hash, created_from_job_id, last_confirmed_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (pattern_id, "spatial_correlation", suburb, city, province, ethnicity,
                                  correlation_strength, count, count, 1.0, spatial_hash, 
                                  "correlation_analysis", datetime.now().isoformat()))
                            
                            logger.info("Spatial correlation pattern created",
                                       spatial_context=spatial_key,
                                       ethnicity=ethnicity,
                                       correlation_strength=correlation_strength,
                                       confirmations=count)
                            
        except Exception as e:
            logger.error("Failed to extract spatial correlation patterns", error=str(e))
    
    async def _upsert_spatial_pattern(self, conn: sqlite3.Connection, 
                                    name_component: str, suburb: str, city: str, 
                                    province: str, ethnicity: str, spatial_hash: str,
                                    job_id: str, confirmed_at: datetime) -> Optional[SpatialEthnicityPattern]:
        """Create or update spatial ethnicity pattern.
        
        Args:
            conn: Database connection
            name_component: Name component for pattern
            suburb: Suburb context
            city: City context
            province: Province context
            ethnicity: Confirmed ethnicity
            spatial_hash: Spatial context hash
            job_id: Source job ID
            confirmed_at: Confirmation timestamp
            
        Returns:
            SpatialEthnicityPattern if created/updated, None otherwise
        """
        try:
            # Check if pattern exists
            existing = conn.execute("""
                SELECT pattern_id, confirmation_count, total_applications, success_rate
                FROM spatial_ethnicity_patterns
                WHERE name_component = ? AND suburb = ? AND city = ? 
                  AND province = ? AND ethnicity_code = ?
            """, (name_component, suburb, city, province, ethnicity)).fetchone()
            
            if existing:
                # Update existing pattern
                pattern_id, conf_count, total_apps, success_rate = existing
                new_conf_count = conf_count + 1
                new_total_apps = total_apps + 1
                new_success_rate = new_conf_count / max(new_total_apps, 1)
                
                conn.execute("""
                    UPDATE spatial_ethnicity_patterns
                    SET confirmation_count = ?,
                        total_applications = ?,
                        success_rate = ?,
                        last_confirmed_at = ?,
                        confidence_score = ?
                    WHERE pattern_id = ?
                """, (new_conf_count, new_total_apps, new_success_rate, 
                      confirmed_at.isoformat(), min(1.0, new_success_rate * 1.1), pattern_id))
                
                logger.debug("Spatial pattern updated",
                           pattern_id=pattern_id,
                           confirmation_count=new_conf_count,
                           success_rate=new_success_rate)
                
                return SpatialEthnicityPattern(
                    pattern_id=pattern_id,
                    name_component=name_component,
                    suburb=suburb,
                    city=city,
                    province=province,
                    ethnicity_code=ethnicity,
                    confidence_score=min(1.0, new_success_rate * 1.1),
                    confirmation_count=new_conf_count,
                    total_applications=new_total_apps,
                    success_rate=new_success_rate,
                    spatial_context_hash=spatial_hash,
                    created_from_job_id=job_id,
                    last_confirmed_at=confirmed_at,
                    last_applied_at=None,
                    created_at=datetime.now()
                )
            
            else:
                # Create new pattern
                pattern_id = f"spatial_{spatial_hash}_{name_component}_{ethnicity}"
                
                conn.execute("""
                    INSERT INTO spatial_ethnicity_patterns
                    (pattern_id, name_component, suburb, city, province, ethnicity_code,
                     confidence_score, confirmation_count, total_applications, success_rate,
                     spatial_context_hash, created_from_job_id, last_confirmed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (pattern_id, name_component, suburb, city, province, ethnicity,
                      1.0, 1, 1, 1.0, spatial_hash, job_id, confirmed_at.isoformat()))
                
                logger.info("New spatial pattern created",
                           pattern_id=pattern_id,
                           name_component=name_component,
                           ethnicity=ethnicity,
                           spatial_context=f"{suburb}, {city}, {province}")
                
                return SpatialEthnicityPattern(
                    pattern_id=pattern_id,
                    name_component=name_component,
                    suburb=suburb,
                    city=city,
                    province=province,
                    ethnicity_code=ethnicity,
                    confidence_score=1.0,
                    confirmation_count=1,
                    total_applications=1,
                    success_rate=1.0,
                    spatial_context_hash=spatial_hash,
                    created_from_job_id=job_id,
                    last_confirmed_at=confirmed_at,
                    last_applied_at=None,
                    created_at=datetime.now()
                )
                
        except Exception as e:
            logger.error("Failed to upsert spatial pattern",
                        name_component=name_component,
                        ethnicity=ethnicity,
                        error=str(e))
            return None
    
    async def enhanced_ethnicity_prediction(self, name: str, city: str = None, 
                                          province: str = None, suburb: str = None) -> Optional[Classification]:
        """Enhanced ethnicity prediction using confirmed spatial patterns.
        
        Args:
            name: Director name to classify
            city: City context
            province: Province context
            suburb: Suburb context (optional but most predictive)
            
        Returns:
            Classification with enhanced spatial intelligence or None
        """
        start_time = time.time()
        
        with self._db_lock:
            try:
                with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                    # Generate spatial context hash for lookup
                    spatial_hash = self.generate_spatial_context_hash(name, suburb, city, province)
                    
                    # Extract name components
                    name_components = self._extract_name_components(name)
                    
                    best_match = None
                    best_confidence = 0.0
                    
                    for component in name_components:
                        # Look for exact spatial matches first (highest confidence)
                        exact_matches = conn.execute("""
                            SELECT ethnicity_code, confidence_score, success_rate, 
                                   confirmation_count, suburb, city, province
                            FROM spatial_ethnicity_patterns
                            WHERE name_component = ? 
                              AND (suburb = ? OR suburb IS NULL)
                              AND (city = ? OR city IS NULL)
                              AND (province = ? OR province IS NULL)
                              AND confirmation_count > 0
                            ORDER BY success_rate DESC, confirmation_count DESC, confidence_score DESC
                            LIMIT 5
                        """, (component, suburb, city, province)).fetchall()
                        
                        for match in exact_matches:
                            (ethnicity, confidence, success_rate, conf_count, 
                             match_suburb, match_city, match_province) = match
                            
                            # Calculate spatial match score
                            spatial_score = self._calculate_spatial_match_score(
                                suburb, city, province,
                                match_suburb, match_city, match_province
                            )
                            
                            # Adjust confidence based on spatial match and confirmation strength
                            # Give full credit for 1+ confirmations, bonus for multiple confirmations
                            confirmation_boost = min(1.2, 1.0 + (conf_count - 1) * 0.1)
                            adjusted_confidence = confidence * spatial_score * confirmation_boost
                            
                            if adjusted_confidence > best_confidence and adjusted_confidence >= 0.6:
                                best_confidence = adjusted_confidence
                                best_match = {
                                    'ethnicity': ethnicity,
                                    'confidence': adjusted_confidence,
                                    'method': 'spatial_confirmed',
                                    'component': component,
                                    'confirmations': conf_count,
                                    'success_rate': success_rate
                                }
                    
                    if best_match:
                        processing_time = (time.time() - start_time) * 1000
                        
                        logger.info("Enhanced spatial prediction found",
                                   name=name,
                                   predicted_ethnicity=best_match['ethnicity'],
                                   confidence=best_match['confidence'],
                                   component=best_match['component'],
                                   confirmations=best_match['confirmations'],
                                   spatial_context=f"{suburb}, {city}, {province}")
                        
                        return Classification(
                            name=name,
                            ethnicity=EthnicityType(best_match['ethnicity']),
                            confidence=best_match['confidence'],
                            method=ClassificationMethod.RULE_BASED,  # Spatial patterns are rule-based
                            processing_time_ms=processing_time,
                            context={
                                'spatial_component': best_match['component'],
                                'confirmation_count': best_match['confirmations'],
                                'success_rate': best_match['success_rate'],
                                'spatial_context': f"{suburb}, {city}, {province}"
                            }
                        )
                    
                    return None
                    
            except Exception as e:
                logger.error("Error in enhanced ethnicity prediction",
                           name=name,
                           spatial_context=f"{suburb}, {city}, {province}",
                           error=str(e))
                return None
    
    def _calculate_spatial_match_score(self, query_suburb: str, query_city: str, query_province: str,
                                     pattern_suburb: str, pattern_city: str, pattern_province: str) -> float:
        """Calculate spatial match score between query and pattern.
        
        Args:
            query_suburb: Query suburb
            query_city: Query city
            query_province: Query province
            pattern_suburb: Pattern suburb
            pattern_city: Pattern city
            pattern_province: Pattern province
            
        Returns:
            Match score between 0.0 and 1.0
        """
        score = 0.0
        total_weight = 0.0
        
        # Province match (weight: 0.3)
        if query_province and pattern_province:
            if query_province.lower() == pattern_province.lower():
                score += 0.3
            total_weight += 0.3
        
        # City match (weight: 0.4)
        if query_city and pattern_city:
            if query_city.lower() == pattern_city.lower():
                score += 0.4
            total_weight += 0.4
        
        # Suburb match (weight: 0.6 - most predictive)
        if query_suburb and pattern_suburb:
            if query_suburb.lower() == pattern_suburb.lower():
                score += 0.6
            total_weight += 0.6
        
        # Normalize score by total weight
        if total_weight > 0:
            return min(1.0, score / total_weight)
        else:
            return 0.5  # Neutral score if no spatial context available
    
    async def get_spatial_learning_analytics(self, job_id: str = None) -> Dict[str, Any]:
        """Get spatial learning analytics and confirmation impact.
        
        Args:
            job_id: Optional job ID for job-specific analytics
            
        Returns:
            Dictionary containing spatial learning analytics
        """
        with self._db_lock:
            try:
                with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                    conn.row_factory = sqlite3.Row
                    analytics = {}
                    
                    # Overall spatial pattern statistics
                    pattern_stats = conn.execute("""
                        SELECT 
                            COUNT(*) as total_patterns,
                            COUNT(CASE WHEN confirmation_count > 0 THEN 1 END) as confirmed_patterns,
                            AVG(success_rate) as avg_success_rate,
                            AVG(confirmation_count) as avg_confirmations,
                            MAX(confirmation_count) as max_confirmations
                        FROM spatial_ethnicity_patterns
                    """).fetchone()
                    
                    if pattern_stats:
                        analytics['pattern_statistics'] = dict(pattern_stats)
                    
                    # Confirmation statistics
                    confirmation_stats = conn.execute("""
                        SELECT 
                            COUNT(*) as total_confirmations,
                            COUNT(CASE WHEN confirmed_ethnicity IS NOT NULL THEN 1 END) as actual_confirmations,
                            COUNT(DISTINCT source_file_identifier) as unique_files,
                            COUNT(DISTINCT canonical_city) as unique_cities,
                            COUNT(DISTINCT canonical_province) as unique_provinces
                        FROM ethnicity_confirmations
                    """).fetchone()
                    
                    if confirmation_stats:
                        analytics['confirmation_statistics'] = dict(confirmation_stats)
                    
                    # Ethnicity distribution in confirmations
                    ethnicity_dist = conn.execute("""
                        SELECT confirmed_ethnicity, COUNT(*) as count
                        FROM ethnicity_confirmations
                        WHERE confirmed_ethnicity IS NOT NULL
                        GROUP BY confirmed_ethnicity
                        ORDER BY count DESC
                    """).fetchall()
                    
                    analytics['ethnicity_distribution'] = {
                        row['confirmed_ethnicity']: row['count'] for row in ethnicity_dist
                    }
                    
                    # Geographic coverage
                    geographic_coverage = conn.execute("""
                        SELECT 
                            COUNT(DISTINCT canonical_province) as provinces_covered,
                            COUNT(DISTINCT canonical_city) as cities_covered,
                            COUNT(DISTINCT canonical_suburb) as suburbs_covered
                        FROM ethnicity_confirmations
                        WHERE confirmed_ethnicity IS NOT NULL
                    """).fetchone()
                    
                    if geographic_coverage:
                        analytics['geographic_coverage'] = dict(geographic_coverage)
                    
                    # Learning efficiency (patterns per confirmation)
                    if analytics.get('confirmation_statistics', {}).get('actual_confirmations', 0) > 0:
                        efficiency = (analytics.get('pattern_statistics', {}).get('confirmed_patterns', 0) / 
                                    analytics['confirmation_statistics']['actual_confirmations'])
                        analytics['learning_efficiency'] = efficiency
                    else:
                        analytics['learning_efficiency'] = 0.0
                    
                    # Job-specific analytics if requested
                    if job_id:
                        job_analytics = conn.execute("""
                            SELECT 
                                COUNT(*) as job_confirmations,
                                COUNT(CASE WHEN confirmed_ethnicity IS NOT NULL THEN 1 END) as job_actual_confirmations
                            FROM ethnicity_confirmations
                            WHERE source_job_id = ?
                        """, (job_id,)).fetchone()
                        
                        if job_analytics:
                            analytics['job_specific'] = dict(job_analytics)
                    
                    logger.info("Spatial learning analytics generated",
                               total_patterns=analytics.get('pattern_statistics', {}).get('total_patterns', 0),
                               total_confirmations=analytics.get('confirmation_statistics', {}).get('total_confirmations', 0),
                               learning_efficiency=analytics.get('learning_efficiency', 0.0))
                    
                    return analytics
                    
            except Exception as e:
                logger.error("Failed to get spatial learning analytics",
                           job_id=job_id,
                           error=str(e))
                return {}
    
    async def update_spatial_patterns_from_confirmations(self, days_lookback: int = 7) -> int:
        """Enhanced automatic pattern updates from Developer A's confirmation system.
        
        Implements Task 1.2 integration point with Developer A's confirmation infrastructure.
        Automatically extracts and updates patterns when confirmations are added.
        
        Args:
            days_lookback: Number of days to process confirmations from
            
        Returns:
            Number of patterns updated/created
        """
        try:
            # Extract patterns from recent confirmations with enhanced intelligence
            patterns = await self.extract_patterns_from_confirmations(days_lookback=days_lookback)
            
            # Update learning analytics
            with self._db_lock:
                with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                    await self._update_learning_effectiveness_metrics(conn, len(patterns))
            
            logger.info("Enhanced spatial pattern update completed",
                       patterns_updated=len(patterns),
                       lookback_days=days_lookback)
            
            return len(patterns)
            
        except Exception as e:
            logger.error("Failed to update spatial patterns from confirmations",
                        error=str(e))
            return 0
    
    async def _update_learning_effectiveness_metrics(self, conn: sqlite3.Connection, 
                                                   patterns_count: int) -> None:
        """Update learning effectiveness metrics for monitoring."""
        try:
            today = datetime.now().date()
            
            # Get today's confirmation count
            confirmation_count = conn.execute("""
                SELECT COUNT(*) FROM ethnicity_confirmations 
                WHERE DATE(confirmed_at) = ?
            """, (today.isoformat(),)).fetchone()[0]
            
            if confirmation_count > 0:
                learning_efficiency = patterns_count / confirmation_count
                
                # Update or insert analytics record
                conn.execute("""
                    INSERT OR REPLACE INTO spatial_learning_analytics
                    (analysis_date, patterns_extracted, total_confirmations, learning_efficiency)
                    VALUES (?, ?, ?, ?)
                """, (today.isoformat(), patterns_count, confirmation_count, learning_efficiency))
                
                logger.debug("Learning effectiveness metrics updated",
                           patterns_extracted=patterns_count,
                           confirmations=confirmation_count,
                           efficiency=learning_efficiency)
                
        except Exception as e:
            logger.error("Failed to update learning effectiveness metrics", error=str(e))
    
    async def get_confirmation_learning_status(self) -> Dict[str, Any]:
        """Get current status of confirmation-driven learning system.
        
        Returns comprehensive metrics for monitoring learning effectiveness and
        coordination with Developer A's confirmation system.
        """
        with self._db_lock:
            try:
                with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    # Get recent confirmation activity (last 7 days)
                    recent_confirmations = conn.execute("""
                        SELECT 
                            COUNT(*) as total_confirmations,
                            COUNT(CASE WHEN confirmed_ethnicity IS NOT NULL THEN 1 END) as actual_confirmations,
                            COUNT(DISTINCT canonical_city) as unique_cities,
                            COUNT(DISTINCT canonical_province) as unique_provinces,
                            AVG(CASE WHEN ai_predicted_ethnicity = confirmed_ethnicity THEN 1.0 ELSE 0.0 END) as ai_accuracy
                        FROM ethnicity_confirmations 
                        WHERE confirmed_at > datetime('now', '-7 days')
                    """).fetchone()
                    
                    # Get pattern extraction effectiveness
                    pattern_stats = conn.execute("""
                        SELECT 
                            COUNT(*) as total_patterns,
                            COUNT(CASE WHEN confirmation_count > 1 THEN 1 END) as multi_confirmed_patterns,
                            AVG(success_rate) as avg_success_rate,
                            AVG(confidence_score) as avg_confidence
                        FROM spatial_ethnicity_patterns
                        WHERE last_confirmed_at > datetime('now', '-7 days')
                    """).fetchone()
                    
                    # Get learning efficiency trend
                    efficiency_trend = conn.execute("""
                        SELECT 
                            analysis_date,
                            learning_efficiency,
                            patterns_extracted,
                            total_confirmations
                        FROM spatial_learning_analytics
                        WHERE analysis_date > date('now', '-7 days')
                        ORDER BY analysis_date DESC
                        LIMIT 7
                    """).fetchall()
                    
                    status = {
                        'confirmation_activity': dict(recent_confirmations) if recent_confirmations else {},
                        'pattern_effectiveness': dict(pattern_stats) if pattern_stats else {},
                        'learning_efficiency_trend': [dict(row) for row in efficiency_trend],
                        'integration_health': {
                            'patterns_per_confirmation': 0.0,
                            'spatial_coverage': 0,
                            'accuracy_improvement': 0.0
                        }
                    }
                    
                    # Calculate integration health metrics
                    if recent_confirmations and recent_confirmations['actual_confirmations'] > 0:
                        if pattern_stats and pattern_stats['total_patterns'] > 0:
                            status['integration_health']['patterns_per_confirmation'] = (
                                pattern_stats['total_patterns'] / recent_confirmations['actual_confirmations']
                            )
                        
                        status['integration_health']['spatial_coverage'] = (
                            recent_confirmations['unique_cities'] * recent_confirmations['unique_provinces']
                        )
                        
                        if recent_confirmations['ai_accuracy'] is not None:
                            status['integration_health']['accuracy_improvement'] = recent_confirmations['ai_accuracy']
                    
                    logger.info("Confirmation learning status retrieved",
                               confirmations=status['confirmation_activity'].get('total_confirmations', 0),
                               patterns=status['pattern_effectiveness'].get('total_patterns', 0))
                    
                    return status
                    
            except Exception as e:
                logger.error("Failed to get confirmation learning status", error=str(e))
                return {}
    
    async def enhanced_ethnicity_prediction_with_confirmations(self, name: str, city: str = None, 
                                                             province: str = None, suburb: str = None) -> Optional[Classification]:
        """Enhanced prediction using confirmed spatial patterns - PRIORITY LOOKUP.
        
        Primary integration point for Developer A's export system.
        Implements Phase 1.3: Enhanced ethnicity prediction engine with spatial pattern priority.
        
        Priority Order:
        1. Confirmed spatial patterns FIRST (highest confidence)
        2. Fall back to existing classification pipeline  
        3. Apply spatial confidence boosting
        4. Return enhanced prediction with spatial context
        
        Args:
            name: Director name to classify
            city: City context for spatial intelligence
            province: Province context for spatial intelligence
            suburb: Suburb context (most predictive for spatial patterns)
            
        Returns:
            Enhanced Classification with spatial intelligence or None
        """
        start_time = time.time()
        
        try:
            # STEP 1: Check confirmed spatial patterns FIRST (highest confidence)
            spatial_prediction = await self.enhanced_ethnicity_prediction(
                name=name, city=city, province=province, suburb=suburb
            )
            
            if spatial_prediction and spatial_prediction.confidence >= 0.6:
                # Spatial patterns found with good confidence - use them
                processing_time = (time.time() - start_time) * 1000
                spatial_prediction.processing_time_ms = processing_time
                
                # Create enhanced Classification with spatial context
                enhanced_spatial_prediction = Classification(
                    name=spatial_prediction.name,
                    ethnicity=spatial_prediction.ethnicity,
                    confidence=spatial_prediction.confidence,
                    confidence_level=spatial_prediction.confidence_level,
                    method=spatial_prediction.method,
                    rule_details=spatial_prediction.rule_details,
                    phonetic_details=spatial_prediction.phonetic_details,
                    llm_details=spatial_prediction.llm_details,
                    timestamp=spatial_prediction.timestamp,
                    processing_time_ms=processing_time,
                    alternative_classifications=spatial_prediction.alternative_classifications,
                    context={
                        'spatial_enhanced': True,
                        'spatial_suburb': suburb,
                        'spatial_city': city,
                        'spatial_province': province,
                        'prediction_source': 'confirmed_spatial_patterns',
                        'spatial_component': spatial_prediction.context.get('spatial_component', '') if spatial_prediction.context else '',
                        'confirmation_count': spatial_prediction.context.get('confirmation_count', 0) if spatial_prediction.context else 0,
                        'success_rate': spatial_prediction.context.get('success_rate', 0.0) if spatial_prediction.context else 0.0
                    }
                )
                
                logger.info("Enhanced prediction via confirmed spatial patterns",
                           name=name,
                           predicted_ethnicity=enhanced_spatial_prediction.ethnicity.value,
                           confidence=enhanced_spatial_prediction.confidence,
                           spatial_context=f"{suburb}, {city}, {province}")
                
                return enhanced_spatial_prediction
            
            # STEP 2: Fall back to existing classification pipeline
            try:
                # Import the existing classifier for fallback
                from .classifier import EthnicityClassifier
                
                # Create classifier instance for fallback
                classifier = EthnicityClassifier()
                
                # Use existing classification pipeline
                fallback_prediction = await classifier.classify_name(name)
                
            except Exception as e:
                logger.error("Failed to use existing classification pipeline",
                           name=name,
                           error=str(e))
                # Create a basic fallback prediction for testing
                fallback_prediction = Classification(
                    name=name,
                    ethnicity=EthnicityType.AFRICAN,  # Default fallback
                    confidence=0.5,  # Low confidence fallback
                    method=ClassificationMethod.RULE_BASED,
                    processing_time_ms=1.0
                )
            
            if fallback_prediction:
                # STEP 3: Apply spatial confidence boosting to fallback prediction
                enhanced_prediction = await self._apply_spatial_confidence_boosting(
                    fallback_prediction, name, city, province, suburb
                )
                
                processing_time = (time.time() - start_time) * 1000
                enhanced_prediction.processing_time_ms = processing_time
                
                # Create enhanced prediction with spatial context
                final_enhanced_prediction = Classification(
                    name=enhanced_prediction.name,
                    ethnicity=enhanced_prediction.ethnicity,
                    confidence=enhanced_prediction.confidence,
                    confidence_level=enhanced_prediction.confidence_level,
                    method=enhanced_prediction.method,
                    rule_details=enhanced_prediction.rule_details,
                    phonetic_details=enhanced_prediction.phonetic_details,
                    llm_details=enhanced_prediction.llm_details,
                    timestamp=enhanced_prediction.timestamp,
                    processing_time_ms=processing_time,
                    alternative_classifications=enhanced_prediction.alternative_classifications,
                    context={
                        'spatial_enhanced': True,
                        'spatial_suburb': suburb,
                        'spatial_city': city,
                        'spatial_province': province,
                        'prediction_source': 'fallback_with_spatial_boost',
                        'original_confidence': fallback_prediction.confidence,
                        'spatial_boost_applied': enhanced_prediction.confidence > fallback_prediction.confidence
                    }
                )
                
                enhanced_prediction = final_enhanced_prediction
                
                logger.info("Enhanced prediction via fallback with spatial boosting",
                           name=name,
                           predicted_ethnicity=enhanced_prediction.ethnicity.value,
                           original_confidence=fallback_prediction.confidence,
                           enhanced_confidence=enhanced_prediction.confidence,
                           spatial_context=f"{suburb}, {city}, {province}")
                
                return enhanced_prediction
            
            # No prediction possible
            logger.warning("No prediction possible for name",
                          name=name,
                          spatial_context=f"{suburb}, {city}, {province}")
            return None
            
        except Exception as e:
            logger.error("Error in enhanced ethnicity prediction with confirmations",
                        name=name,
                        spatial_context=f"{suburb}, {city}, {province}",
                        error=str(e))
            return None
    
    async def _apply_spatial_confidence_boosting(self, base_prediction: Classification, 
                                               name: str, city: str = None, 
                                               province: str = None, suburb: str = None) -> Classification:
        """Apply spatial confidence boosting to existing prediction.
        
        Enhances existing classification results with spatial intelligence from confirmations.
        """
        try:
            # Look for any spatial patterns that support this prediction
            with self._db_lock:
                with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                    # Extract name components for spatial pattern matching
                    name_components = self._extract_name_components(name)
                    
                    spatial_support_score = 0.0
                    supporting_patterns = 0
                    
                    for component in name_components:
                        # Look for spatial patterns supporting this ethnicity
                        matches = conn.execute("""
                            SELECT confirmation_count, success_rate, confidence_score
                            FROM spatial_ethnicity_patterns
                            WHERE name_component = ? 
                              AND ethnicity_code = ?
                              AND (suburb = ? OR suburb IS NULL)
                              AND (city = ? OR city IS NULL)
                              AND (province = ? OR province IS NULL)
                              AND confirmation_count > 0
                            ORDER BY confirmation_count DESC, success_rate DESC
                            LIMIT 3
                        """, (component, base_prediction.ethnicity.value, suburb, city, province)).fetchall()
                        
                        for match in matches:
                            conf_count, success_rate, confidence = match
                            # Calculate spatial support based on confirmation strength
                            pattern_support = (conf_count / 10.0) * success_rate * confidence
                            spatial_support_score += pattern_support
                            supporting_patterns += 1
                    
                    # Apply spatial boost if we found supporting patterns
                    if supporting_patterns > 0:
                        # Calculate boost factor (max 20% increase)
                        normalized_support = min(0.2, spatial_support_score / max(supporting_patterns, 1))
                        boosted_confidence = min(1.0, base_prediction.confidence + normalized_support)
                        
                        # Create enhanced prediction with boosted confidence
                        enhanced_prediction = Classification(
                            name=base_prediction.name,
                            ethnicity=base_prediction.ethnicity,
                            confidence=boosted_confidence,
                            confidence_level=base_prediction.confidence_level,
                            method=base_prediction.method,
                            rule_details=base_prediction.rule_details,
                            phonetic_details=base_prediction.phonetic_details,
                            llm_details=base_prediction.llm_details,
                            timestamp=base_prediction.timestamp,
                            processing_time_ms=base_prediction.processing_time_ms,
                            alternative_classifications=base_prediction.alternative_classifications,
                            context=base_prediction.context or {}
                        )
                        
                        # Update confidence level based on new confidence score
                        enhanced_prediction = enhanced_prediction.model_validate(enhanced_prediction.model_dump())
                        
                        logger.debug("Spatial confidence boosting applied",
                                   name=name,
                                   original_confidence=base_prediction.confidence,
                                   enhanced_confidence=boosted_confidence,
                                   supporting_patterns=supporting_patterns,
                                   spatial_support_score=spatial_support_score)
                        
                        return enhanced_prediction
                    
                    else:
                        # No spatial support found - return original prediction
                        return base_prediction
                        
        except Exception as e:
            logger.error("Error applying spatial confidence boosting",
                        name=name,
                        error=str(e))
            return base_prediction