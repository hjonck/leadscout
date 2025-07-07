"""
Persistent LLM learning database for intelligent name classification.

This SQLite database stores every LLM classification to build a self-improving
classification system that reduces LLM dependency over time.
"""

import json
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import structlog

from .models import Classification, ClassificationMethod, EthnicityType

logger = structlog.get_logger(__name__)


@dataclass
class LLMClassificationRecord:
    """Complete record of an LLM classification for learning."""

    name: str
    normalized_name: str
    ethnicity: str
    confidence: float
    llm_provider: str
    processing_time_ms: float
    cost_usd: float
    phonetic_codes: Dict[str, str]
    linguistic_patterns: List[str]
    structural_features: Dict[str, Any]
    classification_timestamp: datetime
    session_id: str


@dataclass
class LearnedPattern:
    """A pattern learned from LLM classifications."""

    pattern_id: str
    pattern_type: str  # 'phonetic', 'structural', 'linguistic', 'ngram'
    pattern_value: str
    target_ethnicity: str
    confidence_score: float
    evidence_count: int
    success_rate: float
    first_learned: datetime
    last_validated: datetime
    is_active: bool


class LLMLearningDatabase:
    """Persistent SQLite database for LLM classification learning."""

    # Class-level lock to prevent concurrent database access
    _db_lock = threading.RLock()

    def __init__(self, db_path: Path = None):
        if db_path is None:
            db_path = Path("cache") / "llm_learning.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

        logger.info("LLM Learning Database initialized", db_path=str(self.db_path))

    def _initialize_database(self):
        """Create database tables for LLM learning."""

        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.executescript(
                """
                -- Core LLM classifications storage
                CREATE TABLE IF NOT EXISTS llm_classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    normalized_name TEXT NOT NULL,
                    ethnicity TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    llm_provider TEXT NOT NULL,
                    processing_time_ms REAL,
                    cost_usd REAL,
                    phonetic_codes JSON,  -- All phonetic algorithm codes
                    linguistic_patterns JSON,  -- Detected SA linguistic patterns
                    structural_features JSON,  -- Name structure analysis
                    classification_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    
                    -- Performance indexes
                    UNIQUE(name, ethnicity) -- Prevent duplicates but allow confidence updates
                );
                
                -- Learned patterns from LLM successes
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,  -- 'phonetic_soundex', 'phonetic_metaphone', 'linguistic_marker', 'structural', 'ngram'
                    pattern_value TEXT NOT NULL,
                    target_ethnicity TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    evidence_count INTEGER DEFAULT 1,
                    success_rate REAL DEFAULT 1.0,
                    first_learned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_validated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT true,
                    
                    -- Ensure pattern uniqueness per ethnicity
                    UNIQUE(pattern_type, pattern_value, target_ethnicity)
                );
                
                -- Pattern application tracking (for measuring success)
                CREATE TABLE IF NOT EXISTS pattern_applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id TEXT,
                    applied_to_name TEXT,
                    predicted_ethnicity TEXT,
                    actual_ethnicity TEXT,  -- From LLM if available
                    was_correct BOOLEAN,
                    confidence_used REAL,
                    application_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (pattern_id) REFERENCES learned_patterns(pattern_id)
                );
                
                -- Phonetic families (groups of names with same phonetic codes)
                CREATE TABLE IF NOT EXISTS phonetic_families (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    soundex_code TEXT,
                    metaphone_code TEXT,
                    double_metaphone_primary TEXT,
                    double_metaphone_secondary TEXT,
                    ethnicity TEXT,
                    confidence REAL,
                    member_count INTEGER DEFAULT 1,
                    representative_names JSON,  -- Sample names in this family
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Indexes for fast phonetic lookups
                CREATE INDEX IF NOT EXISTS idx_soundex ON phonetic_families(soundex_code, ethnicity);
                CREATE INDEX IF NOT EXISTS idx_metaphone ON phonetic_families(metaphone_code, ethnicity);
                CREATE INDEX IF NOT EXISTS idx_dmetaphone ON phonetic_families(double_metaphone_primary, ethnicity);
                
                -- Fast lookup cache for classification results
                CREATE TABLE IF NOT EXISTS classification_cache (
                    name_hash TEXT PRIMARY KEY,  -- SHA256 of normalized name
                    original_name TEXT,
                    best_ethnicity TEXT,
                    confidence REAL,
                    classification_method TEXT,  -- 'learned_pattern', 'phonetic_family', 'llm_cached'
                    cached_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cache_ttl_hours INTEGER DEFAULT 8760,  -- 1 year default TTL
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Linguistic pattern recognition rules
                CREATE TABLE IF NOT EXISTS linguistic_rules (
                    rule_id TEXT PRIMARY KEY,
                    rule_name TEXT,
                    pattern_regex TEXT,
                    target_ethnicity TEXT,
                    confidence_boost REAL,
                    evidence_names JSON,  -- Names that support this rule
                    created_from_llm_analysis BOOLEAN DEFAULT true,
                    rule_accuracy REAL DEFAULT 1.0,
                    times_applied INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT true
                );
                
                -- Performance analytics
                CREATE TABLE IF NOT EXISTS learning_analytics (
                    date DATE PRIMARY KEY,
                    total_classifications INTEGER,
                    llm_classifications INTEGER,
                    learned_classifications INTEGER,
                    phonetic_classifications INTEGER,
                    average_confidence REAL,
                    cost_saved_usd REAL,
                    learning_rate REAL  -- new patterns learned per day
                );
            """
            )

    def store_llm_classification(self, record: LLMClassificationRecord) -> bool:
        """Store an LLM classification for learning."""

        with self._db_lock:
            try:
                with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO llm_classifications 
                        (name, normalized_name, ethnicity, confidence, llm_provider, 
                         processing_time_ms, cost_usd, phonetic_codes, linguistic_patterns, 
                         structural_features, classification_timestamp, session_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            record.name,
                            record.normalized_name,
                            record.ethnicity,
                            record.confidence,
                            record.llm_provider,
                            record.processing_time_ms,
                            record.cost_usd,
                            json.dumps(record.phonetic_codes),
                            json.dumps(record.linguistic_patterns),
                            json.dumps(record.structural_features),
                            record.classification_timestamp.isoformat(),
                            record.session_id,
                        ),
                    )

                    # Immediately extract patterns for learning
                    self._extract_and_store_patterns(conn, record)

                    logger.info(
                        "LLM classification stored and learned",
                        extra={
                            "stored_name": record.name,
                            "stored_ethnicity": record.ethnicity,
                            "stored_confidence": record.confidence,
                        },
                    )

                    return True

            except Exception as e:
                logger.error(
                    "Failed to store LLM classification",
                    extra={"failed_name": record.name, "error": str(e)},
                )
                return False

    def _extract_and_store_patterns(
        self, conn: sqlite3.Connection, record: LLMClassificationRecord
    ):
        """Extract learnable patterns from LLM classification."""

        if record.confidence < 0.8:  # Only learn from high-confidence LLM results
            return

        # Use the provided connection instead of creating a new one
        # 1. Store phonetic family information
        self._store_phonetic_family(conn, record)

        # 2. Extract and store structural patterns
        self._store_structural_patterns(conn, record)

        # 3. Extract and store linguistic patterns
        self._store_linguistic_patterns(conn, record)

        # 4. Update classification cache
        self._update_classification_cache(conn, record)

    def _store_structural_patterns(
        self, conn: sqlite3.Connection, record: LLMClassificationRecord
    ):
        """Store structural patterns for learning."""

        features = record.structural_features

        # Store prefix patterns
        for prefix_key in ["prefix_2", "prefix_3"]:
            if prefix_key in features:
                prefix_value = features[prefix_key]
                if len(prefix_value) >= 2:
                    pattern_id = (
                        f"structural_{prefix_key}_{prefix_value}_{record.ethnicity}"
                    )

                    conn.execute(
                        """
                        INSERT OR IGNORE INTO learned_patterns 
                        (pattern_id, pattern_type, pattern_value, target_ethnicity, 
                         confidence_score, evidence_count)
                        VALUES (?, ?, ?, ?, ?, 1)
                    """,
                        (
                            pattern_id,
                            f"structural_{prefix_key}",
                            prefix_value,
                            record.ethnicity,
                            record.confidence,
                        ),
                    )

                    # Update evidence count if pattern already exists
                    conn.execute(
                        """
                        UPDATE learned_patterns 
                        SET evidence_count = evidence_count + 1,
                            confidence_score = (confidence_score * evidence_count + ?) / (evidence_count + 1),
                            last_validated = CURRENT_TIMESTAMP
                        WHERE pattern_id = ?
                    """,
                        (record.confidence, pattern_id),
                    )

    def _store_phonetic_family(
        self, conn: sqlite3.Connection, record: LLMClassificationRecord
    ):
        """Store phonetic family information for future matching."""

        phonetic_codes = record.phonetic_codes

        # Update or create phonetic family entries
        for code_type, code_value in phonetic_codes.items():
            if not code_value or len(code_value) < 2:
                continue

            # Check if family exists
            existing = conn.execute(
                """
                SELECT id, member_count, representative_names, confidence 
                FROM phonetic_families 
                WHERE soundex_code = ? AND ethnicity = ?
            """,
                (phonetic_codes.get("soundex", ""), record.ethnicity),
            ).fetchone()

            if existing:
                # Update existing family
                family_id, member_count, names_json, old_confidence = existing
                names = json.loads(names_json) if names_json else []

                if record.name not in names:
                    names.append(record.name)
                    names = names[-10:]  # Keep last 10 representative names

                # Update confidence with weighted average
                new_confidence = (old_confidence * member_count + record.confidence) / (
                    member_count + 1
                )

                conn.execute(
                    """
                    UPDATE phonetic_families 
                    SET member_count = member_count + 1,
                        representative_names = ?,
                        confidence = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (json.dumps(names), new_confidence, family_id),
                )

            else:
                # Create new phonetic family
                conn.execute(
                    """
                    INSERT INTO phonetic_families 
                    (soundex_code, metaphone_code, double_metaphone_primary, 
                     double_metaphone_secondary, ethnicity, confidence, 
                     representative_names)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        phonetic_codes.get("soundex", ""),
                        phonetic_codes.get("metaphone", ""),
                        phonetic_codes.get(
                            "nysiis", ""
                        ),  # Use nysiis instead of double_metaphone_primary
                        phonetic_codes.get(
                            "match_rating_codex", ""
                        ),  # Use match_rating instead of double_metaphone_secondary
                        record.ethnicity,
                        record.confidence,
                        json.dumps([record.name]),
                    ),
                )

    def _store_linguistic_patterns(
        self, conn: sqlite3.Connection, record: LLMClassificationRecord
    ):
        """Store linguistic patterns for pattern matching."""

        for pattern in record.linguistic_patterns:
            pattern_id = f"linguistic_{pattern}_{record.ethnicity}"

            conn.execute(
                """
                INSERT OR IGNORE INTO learned_patterns 
                (pattern_id, pattern_type, pattern_value, target_ethnicity, 
                 confidence_score, evidence_count)
                VALUES (?, 'linguistic_marker', ?, ?, ?, 1)
            """,
                (pattern_id, pattern, record.ethnicity, record.confidence),
            )

            # Update evidence count if pattern already exists
            conn.execute(
                """
                UPDATE learned_patterns 
                SET evidence_count = evidence_count + 1,
                    confidence_score = (confidence_score * evidence_count + ?) / (evidence_count + 1),
                    last_validated = CURRENT_TIMESTAMP
                WHERE pattern_id = ?
            """,
                (record.confidence, pattern_id),
            )

    def find_learned_classification(self, name: str) -> Optional[Classification]:
        """Find classification using learned patterns."""

        start_time = time.time()

        with self._db_lock:
            try:
                with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                    # 1. Check direct cache hit
                    cache_result = self._check_classification_cache(conn, name)
                    if cache_result:
                        return cache_result

                    # 2. Check phonetic family matches
                    phonetic_result = self._find_phonetic_family_match(conn, name)
                    if phonetic_result:
                        return phonetic_result

                    # 3. Check linguistic pattern matches
                    linguistic_result = self._find_linguistic_pattern_match(conn, name)
                    if linguistic_result:
                        return linguistic_result

                    return None

            except Exception as e:
                logger.error(
                    "Error in learned classification lookup",
                    extra={"lookup_name": name, "error": str(e)},
                )
                return None

            finally:
                processing_time = (time.time() - start_time) * 1000
                logger.debug(
                    "Learned classification lookup completed",
                    extra={"lookup_name": name, "processing_time_ms": processing_time},
                )

    def _check_classification_cache(
        self, conn: sqlite3.Connection, name: str
    ) -> Optional[Classification]:
        """Check direct cache hit for previously learned classifications."""

        import hashlib

        name_hash = hashlib.sha256(name.lower().strip().encode()).hexdigest()

        result = conn.execute(
            """
            SELECT best_ethnicity, confidence, classification_method
            FROM classification_cache 
            WHERE name_hash = ? 
                AND cached_timestamp > datetime('now', '-' || cache_ttl_hours || ' hours')
        """,
            (name_hash,),
        ).fetchone()

        if result:
            ethnicity, confidence, method = result

            # Update access count and timestamp
            conn.execute(
                """
                UPDATE classification_cache 
                SET access_count = access_count + 1,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE name_hash = ?
            """,
                (name_hash,),
            )

            logger.info(
                "Direct cache hit found",
                extra={"cached_name": name, "cached_ethnicity": ethnicity},
            )

            return Classification(
                name=name,
                ethnicity=EthnicityType(ethnicity),
                confidence=confidence,
                method=ClassificationMethod.CACHE,
                processing_time_ms=0.1,
            )

        return None

    def _update_classification_cache(
        self, conn: sqlite3.Connection, record: LLMClassificationRecord
    ):
        """Update classification cache with new LLM result."""

        import hashlib

        name_hash = hashlib.sha256(record.normalized_name.encode()).hexdigest()

        conn.execute(
            """
            INSERT OR REPLACE INTO classification_cache 
            (name_hash, original_name, best_ethnicity, confidence, 
             classification_method, cache_ttl_hours)
            VALUES (?, ?, ?, ?, 'llm_cached', 8760)
        """,
            (name_hash, record.name, record.ethnicity, record.confidence),
        )

    def _normalize_name_for_phonetics(self, name: str) -> str:
        """Normalize name for phonetic algorithms that require alphabetical characters only."""
        # Remove common prefixes/suffixes that can interfere
        normalized = name.strip().lower()

        # Handle South African specific patterns
        # Remove common prefixes
        prefixes_to_remove = ["van der ", "van ", "de ", "du ", "le "]
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix) :]
                break

        # Handle apostrophes (common in some SA names)
        normalized = normalized.replace("'", "")

        # Remove hyphens and spaces for core phonetic matching
        normalized = normalized.replace("-", "").replace(" ", "")

        # Ensure we have something to work with
        if not normalized:
            normalized = name.strip().replace(" ", "")

        return normalized

    def _find_phonetic_family_match(
        self, conn: sqlite3.Connection, name: str
    ) -> Optional[Classification]:
        """Find classification using phonetic family matching."""

        # Normalize name for phonetic algorithms
        normalized_name = self._normalize_name_for_phonetics(name)

        # Generate phonetic codes for input name using jellyfish directly
        try:
            import jellyfish

            soundex_code = jellyfish.soundex(normalized_name)
            metaphone_code = jellyfish.metaphone(normalized_name)
            nysiis_code = jellyfish.nysiis(normalized_name)
            match_rating_code = jellyfish.match_rating_codex(normalized_name)
        except ImportError:
            logger.warning("Jellyfish not available for phonetic matching")
            return None
        except Exception as e:
            logger.warning(
                f"Error generating phonetic codes for '{name}' (normalized: '{normalized_name}'): {e}"
            )
            return None

        # Find matching phonetic families
        families = conn.execute(
            """
            SELECT ethnicity, confidence, member_count, representative_names
            FROM phonetic_families 
            WHERE (soundex_code = ? OR metaphone_code = ?)
                AND confidence > 0.6
            ORDER BY confidence DESC, member_count DESC
            LIMIT 5
        """,
            (soundex_code, metaphone_code),
        ).fetchall()

        if families:
            # Use best matching family
            ethnicity, confidence, member_count, names_json = families[0]

            # Adjust confidence based on family size and phonetic match quality
            adjusted_confidence = confidence * min(
                1.0, member_count / 5.0
            )  # Boost for larger families

            if adjusted_confidence >= 0.5:
                logger.info(
                    "Phonetic family match found",
                    extra={
                        "matched_name": name,
                        "matched_ethnicity": ethnicity,
                        "family_confidence": confidence,
                        "adjusted_confidence": adjusted_confidence,
                        "family_size": member_count,
                    },
                )

                return Classification(
                    name=name,
                    ethnicity=EthnicityType(ethnicity),
                    confidence=adjusted_confidence,
                    method=ClassificationMethod.PHONETIC,
                    processing_time_ms=1.0,  # Very fast phonetic lookup
                )

        return None

    def _find_linguistic_pattern_match(
        self, conn: sqlite3.Connection, name: str
    ) -> Optional[Classification]:
        """Find classification using learned linguistic patterns."""

        # Get active linguistic patterns
        patterns = conn.execute(
            """
            SELECT pattern_value, target_ethnicity, confidence_score, evidence_count
            FROM learned_patterns 
            WHERE pattern_type = 'linguistic_marker' 
                AND is_active = true 
                AND confidence_score > 0.7
            ORDER BY confidence_score DESC
        """
        ).fetchall()

        name_upper = name.upper()
        best_match = None
        best_confidence = 0.0

        for pattern_value, ethnicity, confidence, evidence_count in patterns:
            # Check if linguistic pattern applies to this name
            pattern_applies = False

            if pattern_value == "tsonga_hl_prefix" and name_upper.startswith("HL"):
                pattern_applies = True
            elif pattern_value == "venda_vh_pattern" and "VH" in name_upper:
                pattern_applies = True
            elif pattern_value == "click_consonant" and name_upper.startswith("NX"):
                pattern_applies = True
            elif pattern_value == "tswana_mma_prefix" and name_upper.startswith("MMA"):
                pattern_applies = True
            # Add more pattern matching logic as needed

            if pattern_applies:
                # Boost confidence based on evidence count
                evidence_boost = min(0.1, evidence_count * 0.01)
                adjusted_confidence = confidence + evidence_boost

                if adjusted_confidence > best_confidence:
                    best_confidence = adjusted_confidence
                    best_match = (ethnicity, adjusted_confidence)

        if best_match and best_confidence >= 0.6:
            ethnicity, confidence = best_match

            logger.info(
                "Linguistic pattern match found",
                extra={
                    "matched_name": name,
                    "pattern_ethnicity": ethnicity,
                    "pattern_confidence": confidence,
                },
            )

            return Classification(
                name=name,
                ethnicity=EthnicityType(ethnicity),
                confidence=confidence,
                method=ClassificationMethod.RULE,
                processing_time_ms=0.5,  # Very fast pattern matching
            )

        return None

    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning system performance statistics."""

        with self._db_lock:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                stats = {}

                # Total stored classifications
                total_llm = conn.execute(
                    "SELECT COUNT(*) FROM llm_classifications"
                ).fetchone()[0]
                stats["total_llm_classifications"] = total_llm

                # Learned patterns count
                active_patterns = conn.execute(
                    "SELECT COUNT(*) FROM learned_patterns WHERE is_active = true"
                ).fetchone()[0]
                stats["active_learned_patterns"] = active_patterns

                # Phonetic families
                phonetic_families = conn.execute(
                    "SELECT COUNT(*) FROM phonetic_families"
                ).fetchone()[0]
                stats["phonetic_families"] = phonetic_families

                # Recent performance (last 30 days)
                recent_performance = conn.execute(
                    """
                    SELECT 
                        COUNT(*) as total_recent,
                        AVG(confidence) as avg_confidence,
                        SUM(cost_usd) as total_cost
                    FROM llm_classifications 
                    WHERE classification_timestamp > datetime('now', '-30 days')
                """
                ).fetchone()

                if recent_performance:
                    stats["recent_30_days"] = {
                        "total_classifications": recent_performance[0],
                        "average_confidence": recent_performance[1] or 0.0,
                        "total_cost_usd": recent_performance[2] or 0.0,
                    }

                # Learning efficiency (patterns per LLM call)
                if total_llm > 0:
                    stats["learning_efficiency"] = active_patterns / total_llm
                else:
                    stats["learning_efficiency"] = 0.0

                return stats

    def cleanup_old_data(self, days_to_keep: int = 365):
        """Clean up old learning data to manage database size."""

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            # Remove old classification cache entries
            conn.execute(
                """
                DELETE FROM classification_cache 
                WHERE cached_timestamp < ? AND access_count < 5
            """,
                (cutoff_date.isoformat(),),
            )

            # Remove old pattern applications
            conn.execute(
                """
                DELETE FROM pattern_applications 
                WHERE application_timestamp < ?
            """,
                (cutoff_date.isoformat(),),
            )

            # Deactivate low-performing patterns
            conn.execute(
                """
                UPDATE learned_patterns 
                SET is_active = false 
                WHERE last_validated < ? AND success_rate < 0.3
            """,
                (cutoff_date.isoformat(),),
            )

            logger.info(
                "Learning database cleanup completed",
                extra={"cutoff_date": cutoff_date.isoformat()},
            )
