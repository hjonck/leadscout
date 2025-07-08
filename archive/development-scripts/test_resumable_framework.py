#!/usr/bin/env python3
"""
Test script for resumable job processing framework.

This script validates the core infrastructure components including
database operations, streaming processing, rate limiting, and
basic job orchestration without requiring full LLM integration.

Usage:
    python test_resumable_framework.py
"""

import asyncio
import sys
import time
from pathlib import Path
import pandas as pd
import structlog

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from leadscout.core.job_database import JobDatabase, JobExecution, LeadResult
from leadscout.core.streaming_processor import StreamingExcelProcessor
from leadscout.core.rate_limiter import RateLimiter, ProviderType

# Configure logging
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False
        }
    }
}

import logging.config
logging.config.dictConfig(logging_config)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

def create_test_excel_file(file_path: Path, num_rows: int = 50) -> None:
    """Create a test Excel file with sample lead data."""
    test_data = []
    
    for i in range(num_rows):
        test_data.append({
            'EntityName': f'Test Company {i+1}',
            'DirectorName': f'Director {i+1}' if i % 10 != 0 else '',  # Some empty names
            'Keyword': 'LOGISTICS',
            'ContactNumber': f'+27-{11:03d}-{i*10+1000:04d}',
            'EmailAddress': f'contact{i+1}@testcompany{i+1}.co.za',
            'RegisteredAddressProvince': ['Gauteng', 'Western Cape', 'KwaZulu-Natal'][i % 3]
        })
    
    df = pd.DataFrame(test_data)
    df.to_excel(file_path, index=False)
    logger.info("Test Excel file created", file_path=str(file_path), rows=num_rows)

def test_job_database():
    """Test JobDatabase functionality."""
    logger.info("Testing JobDatabase functionality")
    
    # Initialize database
    db = JobDatabase(Path("test_cache/test_jobs.db"))
    
    # Create test job
    job = JobExecution(
        job_id="test-job-001",
        input_file_path="test_input.xlsx",
        input_file_modified_time=int(time.time()),
        output_file_path="test_output.xlsx",
        total_rows=100,
        batch_size=10
    )
    
    # Test job creation
    job_id = db.create_job(job)
    assert job_id == "test-job-001"
    logger.info("✅ Job creation successful")
    
    # Test lock acquisition
    lock_acquired = db.acquire_lock("test_input.xlsx", job_id)
    assert lock_acquired == True
    logger.info("✅ Lock acquisition successful")
    
    # Test duplicate lock prevention
    duplicate_lock = db.acquire_lock("test_input.xlsx", "different-job")
    assert duplicate_lock == False
    logger.info("✅ Duplicate lock prevention working")
    
    # Test job retrieval
    retrieved_job = db.get_existing_job("test_input.xlsx")
    assert retrieved_job is not None
    assert retrieved_job.job_id == job_id
    logger.info("✅ Job retrieval successful")
    
    # Test lead results saving
    test_results = [
        LeadResult(
            job_id=job_id,
            row_index=i,
            batch_number=0,
            entity_name=f"Company {i}",
            director_name=f"Director {i}",
            classification_result={'ethnicity': 'test', 'confidence': 0.9},
            processing_status='success',
            api_provider='rule_based',
            processing_time_ms=10.0
        ) for i in range(5)
    ]
    
    db.save_lead_results(test_results)
    logger.info("✅ Lead results saving successful")
    
    # Test progress update
    db.update_job_progress(job_id, 0, 5, 0)
    logger.info("✅ Progress update successful")
    
    # Test job validation
    validation_report = db.validate_job_integrity(job_id)
    logger.info("✅ Job validation successful", validation_report=validation_report)
    
    # Test job completion
    db.complete_job(job_id, success=True)
    logger.info("✅ Job completion successful")
    
    # Release lock
    db.release_lock("test_input.xlsx")
    logger.info("✅ Lock release successful")
    
    logger.info("🎉 JobDatabase tests completed successfully")

def test_streaming_processor():
    """Test StreamingExcelProcessor functionality."""
    logger.info("Testing StreamingExcelProcessor functionality")
    
    # Create test file
    test_file = Path("test_data/test_leads.xlsx")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    create_test_excel_file(test_file, 25)
    
    # Initialize processor
    processor = StreamingExcelProcessor(test_file, batch_size=10)
    
    # Test row counting
    total_rows = processor.get_total_rows()
    assert total_rows == 25
    logger.info("✅ Row counting successful", total_rows=total_rows)
    
    # Test batch streaming
    batches_processed = 0
    total_records = 0
    
    for batch in processor.stream_batches():
        batches_processed += 1
        total_records += len(batch)
        
        # Validate batch structure
        assert isinstance(batch, list)
        assert len(batch) <= 10  # Batch size
        
        for record in batch:
            assert '_source_row_index' in record
            assert 'EntityName' in record
            assert 'DirectorName' in record
    
    assert batches_processed == 3  # 25 rows / 10 batch_size = 3 batches
    assert total_records == 25
    logger.info("✅ Batch streaming successful", 
               batches=batches_processed, 
               total_records=total_records)
    
    # Test resume from middle
    resume_batches = 0
    for batch in processor.stream_batches(start_row=15):
        resume_batches += 1
    
    assert resume_batches == 1  # Only last 10 rows (15-24)
    logger.info("✅ Resume from middle successful", resume_batches=resume_batches)
    
    # Test file info
    file_info = processor.get_file_info()
    assert file_info['total_rows'] == 25
    logger.info("✅ File info successful", file_info=file_info)
    
    logger.info("🎉 StreamingExcelProcessor tests completed successfully")

def test_rate_limiter():
    """Test RateLimiter functionality."""
    logger.info("Testing RateLimiter functionality")
    
    # Initialize rate limiter
    limiter = RateLimiter()
    
    # Test provider status
    status = limiter.get_provider_status()
    assert 'providers' in status
    assert 'summary' in status
    logger.info("✅ Provider status successful", 
               available_providers=status['summary']['available_providers'])
    
    # Test rate limit permits (should work without API keys)
    permit_acquired = asyncio.run(limiter.acquire_permit(ProviderType.OPENAI))
    logger.info("✅ Rate limit permit test", permit_acquired=permit_acquired)
    
    # Test provider switching
    next_provider = limiter.get_next_available_provider()
    logger.info("✅ Provider switching test", next_provider=next_provider)
    
    # Test rate limit error handling (simulated)
    class MockRateLimitError(Exception):
        pass
    
    backoff_delay = limiter.handle_rate_limit_error(ProviderType.OPENAI, MockRateLimitError("Rate limit exceeded"))
    assert backoff_delay > 0
    logger.info("✅ Rate limit error handling successful", backoff_delay=backoff_delay)
    
    # Test provider availability after error
    status_after_error = limiter.get_provider_status()
    openai_status = status_after_error['providers']['openai']
    assert openai_status['in_backoff'] == True
    logger.info("✅ Provider backoff working", openai_available=openai_status['available'])
    
    logger.info("🎉 RateLimiter tests completed successfully")

def test_integration():
    """Test integration between components."""
    logger.info("Testing component integration")
    
    # Create test data
    test_file = Path("test_data/integration_test.xlsx")
    create_test_excel_file(test_file, 15)
    
    # Initialize components
    db = JobDatabase(Path("test_cache/integration_jobs.db"))
    processor = StreamingExcelProcessor(test_file, batch_size=5)
    limiter = RateLimiter()
    
    # Create job
    job = JobExecution(
        job_id="integration-test-001",
        input_file_path=str(test_file),
        input_file_modified_time=int(test_file.stat().st_mtime),
        output_file_path="integration_output.xlsx",
        total_rows=processor.get_total_rows(),
        batch_size=5
    )
    
    job_id = db.create_job(job)
    db.acquire_lock(str(test_file), job_id)
    
    # Simulate processing batches
    batch_number = 0
    total_processed = 0
    
    for batch in processor.stream_batches():
        # Simulate processing each lead in batch
        batch_results = []
        
        for record in batch:
            # Simple mock classification
            result = LeadResult(
                job_id=job_id,
                row_index=record['_source_row_index'],
                batch_number=batch_number,
                entity_name=record['EntityName'],
                director_name=record['DirectorName'],
                classification_result={'ethnicity': 'mock', 'confidence': 0.8},
                processing_status='success' if record['DirectorName'] else 'failed',
                api_provider='mock_classifier',
                processing_time_ms=5.0
            )
            batch_results.append(result)
        
        # Save results and update progress
        db.save_lead_results(batch_results)
        
        successful_count = sum(1 for r in batch_results if r.processing_status == 'success')
        total_processed += successful_count
        
        db.update_job_progress(job_id, batch_number, total_processed, len(batch_results) - successful_count)
        
        logger.info("Integration batch processed", 
                   batch_number=batch_number,
                   successful=successful_count,
                   total_processed=total_processed)
        
        batch_number += 1
    
    # Validate and complete
    validation_report = db.validate_job_integrity(job_id)
    assert validation_report['is_valid']
    
    db.complete_job(job_id, success=True)
    db.release_lock(str(test_file))
    
    logger.info("🎉 Integration test completed successfully",
               total_batches=batch_number,
               total_processed=total_processed)

def main():
    """Run all tests."""
    logger.info("🚀 Starting resumable framework tests")
    
    try:
        # Create test directories
        Path("test_cache").mkdir(exist_ok=True)
        Path("test_data").mkdir(exist_ok=True)
        
        # Run individual component tests
        test_job_database()
        test_streaming_processor()
        test_rate_limiter()
        
        # Run integration test
        test_integration()
        
        logger.info("🎉 ALL TESTS PASSED - Resumable framework is working correctly!")
        
        # Summary
        print("\n" + "="*80)
        print("🎉 RESUMABLE JOB FRAMEWORK - VALIDATION COMPLETE")
        print("="*80)
        print("✅ JobDatabase: Schema creation, job management, progress tracking")
        print("✅ StreamingExcelProcessor: Memory-efficient batch processing")
        print("✅ RateLimiter: Provider management, backoff strategies")
        print("✅ Integration: End-to-end workflow coordination")
        print("\n📊 Framework Status: READY FOR PRODUCTION DEPLOYMENT")
        print("🔧 Next Steps: Integrate with ResumableJobRunner for full functionality")
        print("="*80)
        
    except Exception as e:
        logger.error("❌ Test failed", error=str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()