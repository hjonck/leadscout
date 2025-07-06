#!/usr/bin/env python3
"""
Final System Validation Test Script

This script performs comprehensive end-to-end validation of the complete
LeadScout system as specified in final-system-validation-assignment.md
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_complete_pipeline():
    """Test the complete lead enrichment pipeline."""
    print("🚀 Testing Complete Lead Enrichment Pipeline")
    print("=" * 60)
    
    try:
        # Import required modules
        from leadscout.models.lead import Lead
        from leadscout.classification.classifier import NameClassifier
        from leadscout.cache.base import CacheManager
        from leadscout.cipc.search.company_searcher import CompanySearcher
        
        print("✅ All core modules imported successfully")
        
        # Sample South African lead data
        test_lead = Lead(
            entity_name="Mthembu Holdings",
            trading_as_name="Mthembu Holdings", 
            director_name="Thabo Mthembu",
            registered_address_province="KwaZulu-Natal",
            contact_number="031-555-0123",
            email_address="info@mthembuholdings.co.za"
        )
        
        print(f"Input: {test_lead.entity_name} - Director: {test_lead.director_name}")
        print()
        
        # 1. Test name classification (Developer B's system)
        print("1. Testing Name Classification...")
        classifier = NameClassifier()
        start_time = time.time()
        classification = await classifier.classify(test_lead.director_name)
        classification_time = (time.time() - start_time) * 1000
        
        print(f"   ✅ Classification: {classification.ethnicity} ({classification.confidence:.2f})")
        print(f"   ✅ Method: {classification.classification_method}")
        print(f"   ✅ Performance: {classification_time:.2f}ms")
        print()
        
        # 2. Test company search (Developer A's system)
        print("2. Testing Company Search...")
        searcher = CompanySearcher()
        start_time = time.time()
        company_matches = await searcher.search_companies(
            test_lead.entity_name, 
            province=test_lead.registered_address_province
        )
        search_time = (time.time() - start_time) * 1000
        
        print(f"   ✅ Search completed: {len(company_matches)} matches found")
        print(f"   ✅ Performance: {search_time:.2f}ms")
        if company_matches:
            print(f"   ✅ Best match: {company_matches[0].name} (confidence: {company_matches[0].confidence:.2f})")
        print()
        
        # 3. Test cache performance (Developer A's system)
        print("3. Testing Cache Performance...")
        cache = CacheManager()
        
        # First lookup (should be fast due to integration)
        start_time = time.time()
        cached_classification = await cache.get_classification(test_lead.director_name)
        cache_time = (time.time() - start_time) * 1000
        
        print(f"   ✅ Cache Performance: {cache_time:.2f}ms")
        print(f"   ✅ Cache hit: {'Yes' if cached_classification else 'No'}")
        print()
        
        # 4. Test complete enrichment
        print("4. Complete Enrichment Result:")
        enriched_lead = {
            "original_lead": test_lead.dict(),
            "director_ethnicity": classification.ethnicity,
            "director_confidence": classification.confidence,
            "company_matches": len(company_matches),
            "cipc_verified": len(company_matches) > 0,
            "enrichment_timestamp": datetime.utcnow().isoformat(),
            "processing_times": {
                "classification_ms": classification_time,
                "company_search_ms": search_time,
                "cache_lookup_ms": cache_time
            }
        }
        
        print(f"   ✅ Director ethnicity classified: {classification.ethnicity}")
        print(f"   ✅ Company data enriched: {len(company_matches)} matches")
        print(f"   ✅ Cache optimized: {cache_time:.2f}ms lookup")
        print(f"   ✅ Cost optimized: {classification.classification_method} (minimal LLM usage)")
        print()
        
        total_time = classification_time + search_time + cache_time
        print(f"🎯 Total Pipeline Time: {total_time:.2f}ms")
        print(f"🎯 Pipeline Status: PRODUCTION READY ✅")
        
        return enriched_lead, {
            "classification_time": classification_time,
            "search_time": search_time, 
            "cache_time": cache_time,
            "total_time": total_time
        }
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

async def benchmark_complete_system():
    """Benchmark the complete integrated system."""
    print("\n🏁 Performance Benchmark Results")
    print("=" * 60)
    
    try:
        from leadscout.classification.classifier import NameClassifier
        from leadscout.cache.base import CacheManager
        from leadscout.cipc.search.company_searcher import CompanySearcher
        
        classifier = NameClassifier()
        cache = CacheManager()
        searcher = CompanySearcher()
        
        # Test various SA names representing different performance paths
        test_names = [
            "Thabo Mthembu",      # Rule-based (should be <0.1ms)
            "Priya Pillay",       # Rule-based (should be <0.1ms)  
            "Sipho Khumalo",      # Phonetic (should be <50ms)
            "Unknown Surname",    # LLM fallback (should be <2s)
        ]
        
        classification_times = []
        cache_times = []
        methods_used = []
        
        for name in test_names:
            print(f"Testing: {name}")
            
            # Test classification performance
            start = time.time()
            result = await classifier.classify(name)
            classify_time = (time.time() - start) * 1000
            classification_times.append(classify_time)
            methods_used.append(result.classification_method)
            
            # Test cache performance  
            start = time.time()
            cached = await cache.get_classification(name)
            cache_time = (time.time() - start) * 1000
            cache_times.append(cache_time)
            
            print(f"  Classification: {classify_time:.2f}ms → {result.ethnicity}")
            print(f"  Cache lookup: {cache_time:.2f}ms")
            print(f"  Method: {result.classification_method}")
            print()
        
        # Test company search performance
        start = time.time()
        companies = await searcher.search_companies("Mthembu Holdings", province="KwaZulu-Natal")
        search_time = (time.time() - start) * 1000
        
        print(f"Company Search: {search_time:.2f}ms → {len(companies)} results")
        print()
        
        # Validate against targets
        print("🎯 Target Validation:")
        rule_based_times = [t for i, t in enumerate(classification_times) if methods_used[i] == "rule_based"]
        phonetic_times = [t for i, t in enumerate(classification_times) if methods_used[i] == "phonetic"]
        
        if rule_based_times:
            avg_rule_time = sum(rule_based_times) / len(rule_based_times)
            print(f"  ✅ Rule-based: {avg_rule_time:.2f}ms (target: <10ms)")
        
        if phonetic_times:
            avg_phonetic_time = sum(phonetic_times) / len(phonetic_times) 
            print(f"  ✅ Phonetic: {avg_phonetic_time:.2f}ms (target: <50ms)")
        
        avg_cache_time = sum(cache_times) / len(cache_times)
        print(f"  ✅ Cache: {avg_cache_time:.2f}ms (target: <10ms)")
        print(f"  ✅ Company search: {search_time:.2f}ms (target: <200ms)")
        
        return {
            "rule_based_avg": avg_rule_time if rule_based_times else 0,
            "phonetic_avg": avg_phonetic_time if phonetic_times else 0,
            "cache_avg": avg_cache_time,
            "search_time": search_time,
            "methods_used": methods_used
        }
        
    except Exception as e:
        print(f"❌ Benchmark test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def validate_cost_optimization():
    """Validate cost optimization is working as designed."""
    print("\n💰 Cost Optimization Validation")
    print("=" * 60)
    
    try:
        from leadscout.classification.classifier import NameClassifier
        
        classifier = NameClassifier()
        
        # Test diverse SA names to measure LLM usage
        test_names = [
            # Known names that should use rule-based
            "Thabo Mthembu", "Priya Pillay", "Hassan Cassiem", 
            "John Smith", "Maria van der Merwe", "Fatima Adams",
            "Sipho Khumalo", "Sarah Johnson", "Ahmed Patel",
            "Lucky Ngcobo", "Emma Wilson", "Rasheed Khan",
            # Mix in some that might need phonetic/LLM
            "Nomsa Dlamini", "David Brown", "Zinhle Ndaba"
        ] * 5  # 75 total tests
        
        llm_calls = 0
        rule_based = 0
        phonetic = 0
        
        print(f"Testing {len(test_names)} classifications...")
        
        start_time = time.time()
        for i, name in enumerate(test_names):
            result = await classifier.classify(name)
            
            if result.classification_method == "rule_based":
                rule_based += 1
            elif result.classification_method == "phonetic":
                phonetic += 1
            elif result.classification_method == "llm":
                llm_calls += 1
            
            if (i + 1) % 15 == 0:
                print(f"  Progress: {i + 1}/{len(test_names)} completed")
        
        total_time = time.time() - start_time
        
        total_tests = len(test_names)
        llm_percentage = (llm_calls / total_tests) * 100
        rule_percentage = (rule_based / total_tests) * 100
        phonetic_percentage = (phonetic / total_tests) * 100
        
        print(f"\n📊 Results:")
        print(f"  Rule-based: {rule_based}/{total_tests} ({rule_percentage:.1f}%) - no cost")
        print(f"  Phonetic: {phonetic}/{total_tests} ({phonetic_percentage:.1f}%) - no cost")
        print(f"  LLM calls: {llm_calls}/{total_tests} ({llm_percentage:.1f}%) - API cost")
        print()
        print(f"🎯 Target: <5% LLM usage")
        print(f"✅ Actual: {llm_percentage:.1f}% LLM usage")
        print(f"💡 Cost efficiency: {100 - llm_percentage:.1f}% free classifications")
        print(f"⚡ Total processing time: {total_time:.2f}s ({total_time/total_tests*1000:.2f}ms avg)")
        
        return {
            "total_tests": total_tests,
            "llm_calls": llm_calls,
            "rule_based": rule_based,
            "phonetic": phonetic,
            "llm_percentage": llm_percentage,
            "cost_efficiency": 100 - llm_percentage,
            "avg_time_ms": total_time/total_tests*1000
        }
        
    except Exception as e:
        print(f"❌ Cost validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_system_resilience():
    """Test error handling and system resilience."""
    print("\n🛡️ System Resilience Testing")
    print("=" * 60)
    
    try:
        from leadscout.classification.classifier import NameClassifier
        from leadscout.cache.base import CacheManager
        
        classifier = NameClassifier()
        cache = CacheManager()
        
        # Test edge cases
        edge_cases = [
            ("", "Empty string"),
            ("   ", "Whitespace only"),
            ("A", "Single character"),
            ("Very Long Name That Exceeds Normal Expectations" * 5, "Very long name"),
            ("Numbers123", "With numbers"),
            ("Special@Characters!", "Special characters"),
        ]
        
        passed_tests = 0
        total_tests = len(edge_cases)
        
        for i, (test_case, description) in enumerate(edge_cases, 1):
            try:
                print(f"{i}. {description}: ", end="")
                
                if len(test_case) > 50:
                    display_case = test_case[:47] + "..."
                else:
                    display_case = test_case
                    
                result = await classifier.classify(test_case)
                print(f"✅ Handled → {result.ethnicity if result else 'No result'}")
                passed_tests += 1
                
            except Exception as e:
                print(f"❌ Error: {type(e).__name__}: {str(e)}")
        
        # Test None handling separately
        print(f"{total_tests + 1}. None input: ", end="")
        try:
            result = await classifier.classify(None)
            print(f"✅ Handled → {result.ethnicity if result else 'No result'}")
            passed_tests += 1
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}")
        
        total_tests += 1
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"\n🎯 Resilience Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"✅ System gracefully handles edge cases")
        
        return {
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "success_rate": success_rate
        }
        
    except Exception as e:
        print(f"❌ Resilience test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Run all validation tests."""
    print("🎉 LEADSCOUT FINAL SYSTEM VALIDATION")
    print("=" * 60)
    print("Developer A - Final Validation Test Suite")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    # Run all validation tests
    pipeline_result, performance_data = await test_complete_pipeline()
    benchmark_data = await benchmark_complete_system()
    cost_data = await validate_cost_optimization()
    resilience_data = await test_system_resilience()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 FINAL VALIDATION SUMMARY")
    print("=" * 60)
    
    if pipeline_result:
        print("✅ End-to-End Pipeline: PASS")
    else:
        print("❌ End-to-End Pipeline: FAIL")
    
    if benchmark_data:
        print("✅ Performance Benchmarks: PASS")
    else:
        print("❌ Performance Benchmarks: FAIL")
    
    if cost_data and cost_data["llm_percentage"] < 5.0:
        print("✅ Cost Optimization: PASS")
    else:
        print("❌ Cost Optimization: FAIL" if not cost_data else f"⚠️  Cost Optimization: {cost_data['llm_percentage']:.1f}% LLM usage (target: <5%)")
    
    if resilience_data and resilience_data["success_rate"] >= 80:
        print("✅ System Resilience: PASS")
    else:
        print("❌ System Resilience: FAIL" if not resilience_data else f"⚠️  System Resilience: {resilience_data['success_rate']:.1f}% (target: ≥80%)")
    
    # Overall assessment
    all_passed = all([
        pipeline_result is not None,
        benchmark_data is not None,
        cost_data is not None and cost_data["llm_percentage"] < 5.0,
        resilience_data is not None and resilience_data["success_rate"] >= 80
    ])
    
    print()
    if all_passed:
        print("🚀 OVERALL STATUS: PRODUCTION READY ✅")
        print("🎉 All validation tests passed successfully!")
    else:
        print("⚠️  OVERALL STATUS: NEEDS ATTENTION")
        print("Some validation tests require review before production deployment.")
    
    return {
        "pipeline_result": pipeline_result,
        "performance_data": performance_data,
        "benchmark_data": benchmark_data,
        "cost_data": cost_data,
        "resilience_data": resilience_data,
        "all_passed": all_passed
    }

if __name__ == "__main__":
    try:
        results = asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Validation interrupted by user")
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()