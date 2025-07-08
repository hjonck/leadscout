# Developer A - Resumable Job Processing Framework Implementation

**Date**: 2025-07-06  
**Priority**: 🚨 **CRITICAL** - Production Infrastructure  
**Context**: Transform LeadScout into production-grade resumable job system  
**Complexity**: COMPLEX - Major infrastructure implementation  

## 🎯 **MISSION CRITICAL OBJECTIVE**

Implement the complete resumable job processing framework that enables LeadScout to handle large-scale lead processing (500-50,000 leads) with bulletproof resume capability, rate limit management, and zero data loss.

## 📋 **MANDATORY READING**

**🎯 MUST READ FIRST**:
1. `CLAUDE_RULES.md` Section 7 - Complete resumable job framework requirements
2. `dev-tasks/research-name-classification-improvement.md` - Context for why this is critical
3. Current classification failure logs showing need for reliable long-running jobs

## 🏗️ **IMPLEMENTATION REQUIREMENTS**

### **Phase 1: Core Job Infrastructure (Priority 1)**

#### **1.1 SQLite Job Database Schema**
**File**: `src/leadscout/core/job_database.py` (CREATE NEW)

```python
"""
Resumable job database management for LeadScout.

Implements SQLite-based job tracking, locking, and progress management
for large-scale lead processing with conservative resume capability.
"""

import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import uuid
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class JobExecution:
    """Job execution metadata and progress tracking."""
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
    """Individual lead processing result with auto-learning capabilities."""
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
    """SQLite database manager for resumable jobs."""
    
    def __init__(self, db_path: Path = Path("cache/jobs.db")):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database tables if they don't exist."""
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
                    created_by TEXT,
                    UNIQUE(input_file_path, status) WHERE status = 'running'
                );
                
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
            ''')
    
    def create_job(self, job: JobExecution) -> str:
        """Create new job execution record."""
        # Implementation details...
        pass
    
    def acquire_lock(self, input_file_path: str, job_id: str) -> bool:
        """Acquire exclusive lock for input file processing."""
        # Implementation details...
        pass
    
    def release_lock(self, input_file_path: str) -> None:
        """Release lock for input file."""
        # Implementation details...
        pass
    
    def get_existing_job(self, input_file_path: str) -> Optional[JobExecution]:
        """Get existing running job for input file."""
        # Implementation details...
        pass
    
    def update_job_progress(self, job_id: str, batch_number: int, 
                          processed_count: int, failed_count: int) -> None:
        """Update job progress after batch completion."""
        # Implementation details...
        pass
    
    def save_lead_results(self, results: List[LeadResult]) -> None:
        """Save batch of lead processing results."""
        # Implementation details...
        pass
    
    def get_resume_position(self, job_id: str) -> int:
        """Get conservative resume position (last_committed_batch + 1)."""
        # Implementation details...
        pass
    
    def complete_job(self, job_id: str, success: bool, error_summary: str = None) -> None:
        """Mark job as completed or failed."""
        # Implementation details...
        pass
    
    def validate_job_integrity(self, job_id: str) -> Dict[str, Any]:
        """Validate job data integrity and return validation report."""
        # Implementation details...
        pass
    
    def extract_learning_patterns(self, lead_result: LeadResult) -> None:
        """Extract and store learnable patterns from successful LLM classification."""
        if (lead_result.processing_status == 'success' and 
            lead_result.api_provider in ['openai', 'anthropic'] and
            lead_result.classification_result):
            
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
                       rules_generated=len(auto_rules))
    
    def _analyze_name_patterns(self, name: str, classification: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze name to extract learnable patterns."""
        patterns = []
        
        # Extract prefix patterns (first 2-4 characters)
        # Extract suffix patterns (last 2-4 characters)
        # Extract phonetic codes using multiple algorithms
        # Extract linguistic structure patterns
        # Extract confidence-indicating features
        
        # Implementation details...
        return patterns
    
    def _generate_auto_rules(self, patterns: List[Dict[str, Any]], lead_result: LeadResult) -> List[Dict[str, Any]]:
        """Generate auto-classification rules from extracted patterns."""
        rules = []
        
        # Generate rules with confidence scores
        # Validate against existing successful classifications
        # Create rule patterns for future matching
        
        # Implementation details...
        return rules
    
    def _store_auto_rules(self, rules: List[Dict[str, Any]], job_id: str) -> None:
        """Store auto-generated rules in database."""
        # Store rules with usage tracking
        # Set up analytics for rule performance
        # Implementation details...
        pass
```

#### **1.2 Streaming Data Processor**
**File**: `src/leadscout/core/streaming_processor.py` (CREATE NEW)

```python
"""
Streaming data processor for large Excel files with batch processing.

Provides memory-efficient streaming of Excel data with configurable batch sizes
and resumable processing capability.
"""

import pandas as pd
from pathlib import Path
from typing import Iterator, List, Dict, Any, Optional
import structlog

logger = structlog.get_logger(__name__)

class StreamingExcelProcessor:
    """Memory-efficient Excel file processor with batching."""
    
    def __init__(self, file_path: Path, batch_size: int = 100):
        self.file_path = file_path
        self.batch_size = batch_size
        self.total_rows = None
        
    def get_total_rows(self) -> int:
        """Get total row count efficiently."""
        if self.total_rows is None:
            # Use efficient row counting method
            df = pd.read_excel(self.file_path, usecols=[0])  # Read only first column
            self.total_rows = len(df)
            logger.info("Total rows determined", 
                       file=str(self.file_path), 
                       total_rows=self.total_rows)
        return self.total_rows
    
    def stream_batches(self, start_row: int = 0) -> Iterator[List[Dict[str, Any]]]:
        """Stream Excel data in batches starting from specified row."""
        current_row = start_row
        total_rows = self.get_total_rows()
        
        logger.info("Starting batch streaming",
                   start_row=start_row,
                   batch_size=self.batch_size,
                   total_rows=total_rows)
        
        while current_row < total_rows:
            # Calculate chunk size for this batch
            remaining_rows = total_rows - current_row
            chunk_size = min(self.batch_size, remaining_rows)
            
            try:
                # Read specific chunk from Excel
                df_chunk = pd.read_excel(
                    self.file_path,
                    skiprows=range(1, current_row + 1),  # Skip header + previous rows
                    nrows=chunk_size
                )
                
                # Convert to list of dictionaries
                batch_data = df_chunk.to_dict('records')
                
                # Add row indices for tracking
                for i, record in enumerate(batch_data):
                    record['_source_row_index'] = current_row + i
                
                logger.debug("Batch loaded",
                           start_row=current_row,
                           end_row=current_row + len(batch_data) - 1,
                           batch_size=len(batch_data))
                
                yield batch_data
                current_row += len(batch_data)
                
            except Exception as e:
                logger.error("Error reading batch",
                           start_row=current_row,
                           chunk_size=chunk_size,
                           error=str(e))
                raise
        
        logger.info("Batch streaming completed", total_rows_processed=current_row)
```

#### **1.3 Rate Limit Management**
**File**: `src/leadscout/core/rate_limiter.py` (CREATE NEW)

```python
"""
API rate limit management with provider-specific configurations.

Implements actual API rate limits based on provider documentation,
exponential backoff, and automatic provider switching.
"""

import time
import asyncio
from typing import Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)

class ProviderType(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    RULE_BASED = "rule_based"
    PHONETIC = "phonetic"

@dataclass
class RateLimitConfig:
    """Rate limit configuration for API provider."""
    requests_per_minute: int
    requests_per_day: Optional[int] = None
    tokens_per_minute: Optional[int] = None
    initial_backoff_seconds: int = 30
    max_backoff_seconds: int = 300
    backoff_multiplier: float = 2.0

class RateLimiter:
    """Multi-provider rate limit management."""
    
    # Provider-specific rate limits (research actual current limits)
    PROVIDER_LIMITS = {
        ProviderType.OPENAI: RateLimitConfig(
            requests_per_minute=3,  # Free tier - research current limits
            tokens_per_minute=40000,  # Research current limits
            initial_backoff_seconds=60,
            max_backoff_seconds=900
        ),
        ProviderType.ANTHROPIC: RateLimitConfig(
            requests_per_minute=5,  # Research current limits
            requests_per_day=1000,  # Research current limits
            initial_backoff_seconds=30,
            max_backoff_seconds=600
        )
    }
    
    def __init__(self):
        self.request_history: Dict[ProviderType, List[float]] = {}
        self.backoff_until: Dict[ProviderType, float] = {}
        self.failure_counts: Dict[ProviderType, int] = {}
    
    async def acquire_permit(self, provider: ProviderType) -> bool:
        """Acquire rate limit permit for provider."""
        # Implementation with actual rate limit logic
        pass
    
    def handle_rate_limit_error(self, provider: ProviderType, error: Any) -> float:
        """Handle rate limit error and return backoff delay."""
        # Implementation with exponential backoff
        pass
    
    def should_switch_provider(self, provider: ProviderType) -> bool:
        """Determine if provider should be switched due to rate limits."""
        # Implementation logic
        pass
    
    def get_next_available_provider(self, exclude: List[ProviderType] = None) -> Optional[ProviderType]:
        """Get next available provider for processing."""
        # Implementation logic
        pass
```

### **Phase 2: Job Processing Engine (Priority 1)**

#### **2.1 Resumable Job Runner**
**File**: `src/leadscout/core/resumable_job_runner.py` (CREATE NEW)

```python
"""
Main resumable job processing engine.

Orchestrates streaming data processing, rate limit management,
error handling, and conservative resume logic.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
import structlog

from .job_database import JobDatabase, JobExecution, LeadResult
from .streaming_processor import StreamingExcelProcessor
from .rate_limiter import RateLimiter, ProviderType
from ..classification.classifier import NameClassifier

logger = structlog.get_logger(__name__)

class ResumableJobRunner:
    """Production-grade resumable job processing engine."""
    
    def __init__(self, 
                 input_file: Path,
                 output_file: Optional[Path] = None,
                 batch_size: int = 100):
        self.input_file = input_file
        self.output_file = output_file or self._generate_output_path()
        self.batch_size = batch_size
        
        # Initialize core components
        self.job_db = JobDatabase()
        self.rate_limiter = RateLimiter()
        self.classifier = NameClassifier()
        self.streaming_processor = StreamingExcelProcessor(input_file, batch_size)
        
    def run(self) -> str:
        """Execute or resume job processing."""
        
        # 1. Check for existing job and acquire lock
        existing_job = self._check_existing_job()
        if existing_job:
            logger.info("Resuming existing job", job_id=existing_job.job_id)
            job = existing_job
        else:
            logger.info("Starting new job")
            job = self._create_new_job()
        
        try:
            # 2. Acquire processing lock
            if not self.job_db.acquire_lock(str(self.input_file), job.job_id):
                raise RuntimeError(f"Cannot acquire lock for {self.input_file}")
            
            # 3. Process with conservative resume
            asyncio.run(self._process_job(job))
            
            # 4. Validate and complete job
            self._validate_and_complete_job(job.job_id)
            
            return job.job_id
            
        finally:
            # 5. Always release lock
            self.job_db.release_lock(str(self.input_file))
    
    async def _process_job(self, job: JobExecution):
        """Main job processing loop with batching and error handling."""
        
        # Calculate conservative resume position
        resume_row = self.job_db.get_resume_position(job.job_id)
        total_rows = self.streaming_processor.get_total_rows()
        
        logger.info("Job processing started",
                   job_id=job.job_id,
                   resume_row=resume_row,
                   total_rows=total_rows,
                   batch_size=self.batch_size)
        
        batch_number = resume_row // self.batch_size
        
        # Stream and process batches
        for batch_data in self.streaming_processor.stream_batches(resume_row):
            batch_results = await self._process_batch(batch_data, batch_number, job.job_id)
            
            # Commit batch results
            self.job_db.save_lead_results(batch_results)
            
            # Update job progress
            successful_count = sum(1 for r in batch_results if r.processing_status == 'success')
            failed_count = len(batch_results) - successful_count
            
            self.job_db.update_job_progress(
                job.job_id, 
                batch_number, 
                job.processed_leads_count + successful_count,
                job.failed_leads_count + failed_count
            )
            
            # Log progress
            progress_pct = ((batch_number + 1) * self.batch_size / total_rows) * 100
            logger.info("Batch completed",
                       job_id=job.job_id,
                       batch_number=batch_number,
                       processed=successful_count,
                       failed=failed_count,
                       progress_percent=round(progress_pct, 1))
            
            batch_number += 1
    
    async def _process_batch(self, batch_data: List[Dict[str, Any]], 
                           batch_number: int, job_id: str) -> List[LeadResult]:
        """Process single batch with error handling and retries."""
        results = []
        
        for lead_data in batch_data:
            try:
                # Process individual lead
                classification = await self.classifier.classify_name(
                    lead_data.get('DirectorName', '')
                )
                
                result = LeadResult(
                    job_id=job_id,
                    row_index=lead_data['_source_row_index'],
                    batch_number=batch_number,
                    entity_name=lead_data.get('EntityName', ''),
                    director_name=lead_data.get('DirectorName', ''),
                    classification_result=classification.to_dict() if classification else None,
                    processing_status='success' if classification else 'failed',
                    api_provider=classification.method.value if classification else None,
                    processing_time_ms=classification.processing_time_ms if classification else 0.0
                )
                
            except Exception as e:
                # Handle individual lead failure
                result = LeadResult(
                    job_id=job_id,
                    row_index=lead_data['_source_row_index'],
                    batch_number=batch_number,
                    entity_name=lead_data.get('EntityName', ''),
                    director_name=lead_data.get('DirectorName', ''),
                    classification_result=None,
                    processing_status='failed',
                    error_message=str(e),
                    error_type=self._classify_error(e)
                )
                
                logger.warning("Lead processing failed",
                             row_index=result.row_index,
                             director_name=result.director_name,
                             error=str(e))
            
            results.append(result)
        
        return results
    
    def _validate_and_complete_job(self, job_id: str):
        """Validate job integrity and mark as complete."""
        validation_report = self.job_db.validate_job_integrity(job_id)
        
        if validation_report['is_valid']:
            self.job_db.complete_job(job_id, success=True)
            logger.info("Job completed successfully", 
                       job_id=job_id,
                       validation_report=validation_report)
        else:
            self.job_db.complete_job(job_id, success=False, 
                                   error_summary=validation_report['errors'])
            logger.error("Job validation failed",
                        job_id=job_id,
                        validation_report=validation_report)
            raise RuntimeError(f"Job validation failed: {validation_report['errors']}")
```

### **Phase 3: CLI Integration (Priority 2)**

#### **3.1 Update Main Demo Script**
**File**: Update `run_logistics_demo.py` to use resumable framework

#### **3.2 Output Generation Utility**
**File**: `generate_job_output.py` (CREATE NEW)

#### **3.3 Job Management Commands**
**File**: `job_manager.py` (CREATE NEW)

## 🧪 **TESTING REQUIREMENTS**

### **Test Coverage Required:**
- [ ] SQLite database schema creation and operations
- [ ] Job locking and concurrent access prevention  
- [ ] Conservative resume from various interruption points
- [ ] Batch processing with partial failures
- [ ] Rate limit handling and provider switching
- [ ] Memory efficiency with large files
- [ ] Job validation and integrity checking

### **Integration Tests:**
- [ ] End-to-end job processing with interruption and resume
- [ ] Large file processing (1000+ leads) with memory monitoring
- [ ] Rate limit simulation and provider switching
- [ ] Concurrent job prevention testing
- [ ] Output generation from SQLite data

## 📊 **SUCCESS CRITERIA**

### **Functional Requirements:**
- [ ] Jobs can be interrupted at any point and resumed without data loss
- [ ] Memory usage remains constant regardless of file size
- [ ] Rate limits are respected with automatic provider switching
- [ ] Concurrent jobs on same file are prevented
- [ ] Post-completion validation passes for all jobs

### **Performance Requirements:**
- [ ] Batch processing overhead <5% compared to current system
- [ ] Resume time <30 seconds regardless of progress point
- [ ] Memory usage <100MB for any file size
- [ ] SQLite operations complete within 100ms

### **Business Requirements:**
- [ ] No data loss under any failure scenario
- [ ] Clear progress reporting throughout processing
- [ ] Ability to generate outputs at any processing stage
- [ ] Cost tracking and optimization metrics available

## ⚡ **CRITICAL SUCCESS FACTORS**

1. **Conservative Resume**: Never lose processed data, always resume safely
2. **Rate Limit Compliance**: Research and implement actual API limits
3. **Memory Efficiency**: Handle 50,000+ leads without memory issues
4. **Bulletproof Locking**: Prevent any possibility of concurrent processing
5. **Comprehensive Testing**: Test all failure and resume scenarios

This implementation transforms LeadScout into a production-grade system capable of handling enterprise-scale lead processing with complete reliability and resumability.

---

**Mission**: Implement bulletproof resumable job processing infrastructure  
**Timeline**: Implement in phases - core infrastructure first, then CLI integration  
**Validation**: Must demonstrate successful resume from multiple interruption points  
**Standard**: Enterprise-grade reliability required for production deployment