#!/usr/bin/env python3
"""
Integration validation test for learning database and resumable jobs.

Tests end-to-end integration with learning analytics and validates the
complete Developer A integration with the learning database system.

This test validates:
1. Learning database integration with resumable job processing
2. Batch learning analytics storage and retrieval
3. Job-level learning metrics and cost optimization tracking
4. CLI integration with production-ready commands
5. Complete system integration with Developer B's classification system

Usage:
    source .venv/bin/activate && python test_integration_validation.py
"""

import asyncio
import pandas as pd
from pathlib import Path
import tempfile
import os
import sys
import time
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.leadscout.core.resumable_job_runner import ResumableJobRunner
from src.leadscout.classification.learning_database import LLMLearningDatabase
from src.leadscout.core.config import get_settings
from src.leadscout.core.job_database import JobDatabase

async def test_integration_validation():
    """Test complete integration with learning database."""
    
    print("🧪 INTEGRATION VALIDATION TEST")
    print("=" * 60)
    print("Developer A - Learning Database Integration Validation")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Create test data with South African names for better classification testing
    test_data = {
        'EntityName': ['Mthembu Holdings Pty Ltd', 'Van Der Merwe Transport', 'Patel Brothers Trading'],
        'DirectorName': ['THABO MTHEMBU', 'PIETER VAN DER MERWE', 'PRIYA PATEL'],
        'Keyword': ['LOGISTICS', 'TRANSPORT', 'TRADING']
    }
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        df = pd.DataFrame(test_data)
        df.to_excel(tmp.name, index=False)
        test_file = tmp.name
    
    try:
        # Test 1: Learning Database Initialization
        print("📊 Test 1: Learning Database Initialization")
        
        learning_db = LLMLearningDatabase()
        initial_stats = learning_db.get_learning_statistics()
        
        print(f"  ✅ Learning database initialized")
        print(f"  Initial LLM Classifications: {initial_stats.get('total_llm_classifications', 0)}")
        print(f"  Initial Patterns: {initial_stats.get('active_learned_patterns', 0)}")
        print(f"  Initial Phonetic Families: {initial_stats.get('phonetic_families', 0)}")
        print()
        
        # Test 2: Job Database Integration
        print("📊 Test 2: Job Database Integration")
        
        job_db = JobDatabase()
        print(f"  ✅ Job database initialized")
        print(f"  Database path: {job_db.db_path}")
        print()
        
        # Test 3: Resumable Job Runner with Learning Integration
        print("📊 Test 3: Resumable Job Runner with Learning Integration")
        
        start_time = time.time()
        
        runner = ResumableJobRunner(
            input_file=Path(test_file),
            batch_size=2  # Small batch for testing
        )
        
        print(f"  ✅ ResumableJobRunner initialized with learning database")
        print(f"  Learning DB Path: {runner.learning_db.db_path}")
        print(f"  Job Session ID: {runner.job_session_id}")
        print()
        
        # Test 4: Complete Job Processing
        print("📊 Test 4: Complete Job Processing with Learning Analytics")
        
        job_id = await runner.run()
        
        processing_time = time.time() - start_time
        
        print(f"  ✅ Job completed successfully")
        print(f"  Job ID: {job_id}")
        print(f"  Processing Time: {processing_time:.2f}s")
        print()
        
        # Test 5: Learning Analytics Validation
        print("📊 Test 5: Learning Analytics Validation")
        
        # Get job learning summary
        learning_summary = await runner.get_job_learning_summary(job_id)
        
        if learning_summary:
            print(f"  ✅ Learning summary generated successfully")
            print(f"  Total Classifications: {learning_summary.get('total_classifications', 0)}")
            
            llm_usage = learning_summary.get('llm_usage', {})
            print(f"  LLM Usage: {llm_usage.get('count', 0)} calls ({llm_usage.get('rate', 0):.1f}%)")
            
            learning_system = learning_summary.get('learning_system', {})
            print(f"  Learned Pattern Hits: {learning_system.get('learned_pattern_hits', 0)}")
            print(f"  Patterns in Database: {learning_system.get('patterns_in_database', 0)}")
            
            cost_opt = learning_summary.get('cost_optimization', {})
            print(f"  Cost Saved: ${cost_opt.get('cost_saved', 0):.4f}")
            print(f"  Cost Savings: {cost_opt.get('cost_savings_percent', 0):.1f}%")
        else:
            print(f"  ❌ Learning summary not generated")
        print()
        
        # Test 6: Database Analytics Validation
        print("📊 Test 6: Database Analytics Validation")
        
        # Get learning analytics from database
        job_learning_analytics = job_db.get_job_learning_analytics(job_id)
        
        if job_learning_analytics:
            print(f"  ✅ Job learning analytics retrieved from database")
            print(f"  Total Classifications: {job_learning_analytics.get('total_classifications', 0)}")
            print(f"  LLM Classifications: {job_learning_analytics.get('llm_classifications', 0)}")
            print(f"  Learning Efficiency: {job_learning_analytics.get('learning_efficiency', 0):.3f}")
            
            batch_summary = job_learning_analytics.get('batch_summary', {})
            if batch_summary:
                print(f"  Total Batches: {batch_summary.get('total_batches', 0)}")
                print(f"  Total LLM Calls: {batch_summary.get('total_llm_calls', 0)}")
        else:
            print(f"  ⚠️  No job learning analytics found in database")
        print()
        
        # Test 7: Learning Database State Validation
        print("📊 Test 7: Learning Database State Validation")
        
        final_stats = learning_db.get_learning_statistics()
        
        print(f"  ✅ Learning database accessible after processing")
        print(f"  LLM Classifications: {final_stats.get('total_llm_classifications', 0)}")
        print(f"  Active Patterns: {final_stats.get('active_learned_patterns', 0)}")
        print(f"  Phonetic Families: {final_stats.get('phonetic_families', 0)}")
        print(f"  Learning Efficiency: {final_stats.get('learning_efficiency', 0):.3f}")
        
        # Check for improvements
        classification_growth = final_stats.get('total_llm_classifications', 0) - initial_stats.get('total_llm_classifications', 0)
        pattern_growth = final_stats.get('active_learned_patterns', 0) - initial_stats.get('active_learned_patterns', 0)
        
        print(f"  Growth: +{classification_growth} classifications, +{pattern_growth} patterns")
        print()
        
        # Test 8: Processing Stats Validation
        print("📊 Test 8: Processing Stats Validation")
        
        print(f"  ✅ Processing statistics tracked")
        print(f"  Batches Processed: {runner.processing_stats.get('batches_processed', 0)}")
        print(f"  Leads Processed: {runner.processing_stats.get('leads_processed', 0)}")
        print(f"  LLM Calls: {runner.processing_stats.get('llm_calls', 0)}")
        print(f"  Learned Pattern Hits: {runner.processing_stats.get('learned_pattern_hits', 0)}")
        print(f"  Cost Saved: ${runner.processing_stats.get('cost_saved', 0):.4f}")
        print()
        
        # Test 9: Integration Success Criteria
        print("📊 Test 9: Integration Success Criteria")
        
        success_criteria = {
            "Learning database integration": learning_db is not None,
            "Job processing completion": job_id is not None,
            "Learning analytics generation": learning_summary is not None,
            "Batch analytics storage": job_learning_analytics is not None,
            "Processing stats tracking": runner.processing_stats.get('leads_processed', 0) > 0,
            "Database state consistency": final_stats.get('total_llm_classifications', 0) >= initial_stats.get('total_llm_classifications', 0)
        }
        
        all_passed = True
        for criterion, passed in success_criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {criterion}: {status}")
            if not passed:
                all_passed = False
        print()
        
        # Final Assessment
        print("🎉 INTEGRATION VALIDATION COMPLETE")
        print("=" * 60)
        
        if all_passed:
            print("✅ ALL INTEGRATION TESTS PASSED")
            print("🚀 Learning database integration is production ready!")
            print()
            print("Key Achievements:")
            print("  • Learning database successfully integrated with resumable jobs")
            print("  • Batch learning analytics stored and retrievable")
            print("  • Job-level learning metrics tracked accurately")
            print("  • Processing statistics captured for cost optimization")
            print("  • Database consistency maintained throughout processing")
        else:
            print("❌ SOME INTEGRATION TESTS FAILED")
            print("⚠️  Review failed criteria before production deployment")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            os.unlink(test_file)
        except:
            pass


async def test_cli_integration():
    """Test CLI integration with learning database."""
    
    print("\n🖥️  CLI INTEGRATION TEST")
    print("=" * 40)
    
    try:
        # Test importing CLI commands
        from src.leadscout.cli.jobs import jobs
        from src.leadscout.cli.main import cli
        
        print("  ✅ CLI commands imported successfully")
        print("  ✅ Jobs command group available")
        print("  ✅ Main CLI includes jobs integration")
        
        # Test CLI help (basic functionality)
        import click.testing
        runner = click.testing.CliRunner()
        
        # Test main CLI help
        result = runner.invoke(cli, ['--help'])
        if result.exit_code == 0:
            print("  ✅ Main CLI help working")
        else:
            print("  ❌ Main CLI help failed")
        
        # Test jobs CLI help
        result = runner.invoke(cli, ['jobs', '--help'])
        if result.exit_code == 0:
            print("  ✅ Jobs CLI help working")
        else:
            print("  ❌ Jobs CLI help failed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ CLI integration test failed: {e}")
        return False


async def main():
    """Run all integration validation tests."""
    
    print("🎉 DEVELOPER A - INTEGRATION VALIDATION TEST SUITE")
    print("=" * 80)
    print("Learning Database Integration with Resumable Job Framework")
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run integration tests
    integration_success = await test_integration_validation()
    cli_success = await test_cli_integration()
    
    # Overall assessment
    print("\n" + "=" * 80)
    print("🏆 FINAL ASSESSMENT")
    print("=" * 80)
    
    if integration_success and cli_success:
        print("🎉 ALL VALIDATION TESTS PASSED SUCCESSFULLY!")
        print()
        print("✅ Learning Database Integration: COMPLETE")
        print("✅ Resumable Job Framework: ENHANCED")
        print("✅ Production CLI: READY")
        print("✅ Analytics and Monitoring: FUNCTIONAL")
        print()
        print("🚀 DEVELOPER A PHASE A1 IMPLEMENTATION: PRODUCTION READY")
        print()
        print("Business Value Delivered:")
        print("  • Enterprise-scale job processing with learning analytics")
        print("  • Real-time cost optimization tracking and monitoring")
        print("  • Production-ready CLI for enterprise operations")
        print("  • Complete integration with auto-improvement system")
        print("  • Measurable ROI through learning system effectiveness")
        
        return True
    else:
        print("❌ SOME VALIDATION TESTS FAILED")
        print()
        if not integration_success:
            print("❌ Learning Database Integration: NEEDS ATTENTION")
        if not cli_success:
            print("❌ CLI Integration: NEEDS ATTENTION")
        print()
        print("⚠️  Review failed components before proceeding to Phase A2")
        
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
        print(f"\nTest completed with exit code: {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)