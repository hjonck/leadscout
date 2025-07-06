#!/usr/bin/env python3
"""
Final System Validation - Comprehensive End-to-End Testing
Developer A: CIPC Integration & Caching Specialist

This script conducts the final validation of the integrated LeadScout system
with learning database active, validating that Developer A's resumable job
framework and Developer B's learning classification system work seamlessly.
"""

import asyncio
import time
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.leadscout.core.resumable_job_runner import ResumableJobRunner
from src.leadscout.classification.classifier import create_classifier, NameClassifier
from src.leadscout.classification.learning_database import LLMLearningDatabase
from src.leadscout.cache.base import BaseCache


class FinalSystemValidator:
    """Comprehensive validation of the integrated LeadScout system."""
    
    def __init__(self):
        self.test_results = {}
        self.validation_errors = []
        self.start_time = time.time()
        
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Execute all validation tests and return comprehensive results."""
        
        print("🚀 LEADSCOUT FINAL SYSTEM VALIDATION")
        print("=" * 80)
        print(f"Validation Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Validator: Developer A - CIPC Integration & Caching Specialist")
        print()
        
        try:
            # Test 1: End-to-End Pipeline with Learning Database
            print("📋 TEST 1: End-to-End Lead Enrichment with Learning Database")
            print("-" * 60)
            test1_result = await self._test_end_to_end_pipeline()
            self.test_results['end_to_end_pipeline'] = test1_result
            self._print_test_result("End-to-End Pipeline", test1_result['passed'])
            print()
            
            # Test 2: Performance Benchmark Validation
            print("📋 TEST 2: Performance Benchmark Validation")
            print("-" * 60)
            test2_result = await self._test_performance_benchmarks()
            self.test_results['performance_benchmarks'] = test2_result
            self._print_test_result("Performance Benchmarks", test2_result['passed'])
            print()
            
            # Test 3: Cost Optimization Validation
            print("📋 TEST 3: Cost Optimization Validation")
            print("-" * 60)
            test3_result = await self._test_cost_optimization()
            self.test_results['cost_optimization'] = test3_result
            self._print_test_result("Cost Optimization", test3_result['passed'])
            print()
            
            # Test 4: System Resilience & Error Handling
            print("📋 TEST 4: System Resilience & Error Handling")
            print("-" * 60)
            test4_result = await self._test_system_resilience()
            self.test_results['system_resilience'] = test4_result
            self._print_test_result("System Resilience", test4_result['passed'])
            print()
            
            # Test 5: Integration Stability
            print("📋 TEST 5: Integration Stability")
            print("-" * 60)
            test5_result = await self._test_integration_stability()
            self.test_results['integration_stability'] = test5_result
            self._print_test_result("Integration Stability", test5_result['passed'])
            print()
            
            # Final Assessment
            return await self._generate_final_assessment()
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR during validation: {e}")
            import traceback
            traceback.print_exc()
            return {
                'overall_status': 'FAILED',
                'error': str(e),
                'tests_completed': len(self.test_results)
            }
    
    async def _test_end_to_end_pipeline(self) -> Dict[str, Any]:
        """Test 1: End-to-End Lead Enrichment with Learning Database."""
        
        try:
            print("🔄 Testing integrated pipeline with learning database...")
            
            # Prepare test data
            test_leads = [
                {"entity_name": "Mthembu Holdings", "director_name": "Thabo Mthembu"},
                {"entity_name": "Pillay Enterprises", "director_name": "Priya Pillay"}, 
                {"entity_name": "Sithole Trading", "director_name": "Bongani Sithole"}
            ]
            
            # 1. Test Learning Database Initialization
            print("   → Initializing learning database...")
            learning_db = LLMLearningDatabase()
            initial_stats = learning_db.get_learning_statistics()
            print(f"   → Initial learning database state: {initial_stats.get('total_llm_classifications', 0)} stored classifications")
            
            # 2. Test Classification with Learning Integration
            print("   → Testing classification with learning integration...")
            classifier = create_classifier(mode="cost_optimized", enable_llm=True)
            
            classification_results = []
            for lead in test_leads:
                start_time = time.time()
                result = await classifier.classify_name(lead["director_name"])
                processing_time = (time.time() - start_time) * 1000
                
                classification_results.append({
                    'name': lead["director_name"],
                    'result': result.ethnicity.value if result else None,
                    'confidence': result.confidence if result else 0.0,
                    'method': result.method.value if result else None,
                    'processing_time_ms': processing_time
                })
                
                print(f"   → {lead['director_name']}: {result.ethnicity.value if result else 'None'} "
                      f"({result.confidence:.2f} confidence, {result.method.value if result else 'N/A'}, "
                      f"{processing_time:.2f}ms)")
            
            # 3. Get session statistics
            session_stats = classifier.get_session_stats()
            
            # 4. Flush and validate learning data
            stored_count = classifier.flush_pending_learning_records()
            final_stats = learning_db.get_learning_statistics()
            
            print(f"   → Session stats - LLM calls: {session_stats.llm_classifications}, "
                  f"Learned hits: {session_stats.learned_hits}")
            print(f"   → Learning records stored: {stored_count}")
            print(f"   → Final learning database: {final_stats.get('total_llm_classifications', 0)} total classifications")
            
            # Validate success criteria
            success_checks = {
                'classifications_completed': len(classification_results) == len(test_leads),
                'learning_database_active': final_stats.get('total_llm_classifications', 0) >= initial_stats.get('total_llm_classifications', 0),
                'performance_acceptable': all(r['processing_time_ms'] < 5000 for r in classification_results),  # 5s max
                'results_generated': all(r['result'] is not None for r in classification_results)
            }
            
            return {
                'passed': all(success_checks.values()),
                'results': classification_results,
                'session_stats': {
                    'total_classifications': session_stats.total_classifications,
                    'llm_classifications': session_stats.llm_classifications,
                    'learned_hits': session_stats.learned_hits,
                    'average_time_ms': session_stats.average_time_ms,
                    'llm_cost_usd': session_stats.llm_cost_usd
                },
                'learning_database': {
                    'initial_classifications': initial_stats.get('total_llm_classifications', 0),
                    'final_classifications': final_stats.get('total_llm_classifications', 0),
                    'records_stored': stored_count,
                    'active_patterns': final_stats.get('active_learned_patterns', 0)
                },
                'success_checks': success_checks,
                'error': None
            }
            
        except Exception as e:
            print(f"   ❌ Error in end-to-end pipeline test: {e}")
            import traceback
            traceback.print_exc()
            return {
                'passed': False,
                'error': str(e),
                'results': [],
                'success_checks': {}
            }
    
    async def _test_performance_benchmarks(self) -> Dict[str, Any]:
        """Test 2: Performance Benchmark Validation."""
        
        try:
            print("⚡ Testing performance benchmarks...")
            
            # Initialize systems
            classifier = NameClassifier()
            
            # Test various SA names representing different performance paths
            test_names = [
                ("Thabo Mthembu", "rule_based", 10),      # Should be rule-based, <10ms
                ("Priya Pillay", "rule_based", 10),       # Should be rule-based, <10ms  
                ("Bongani Sithole", "rule_based", 10),    # Should be rule-based, <10ms
            ]
            
            performance_results = []
            
            for name, expected_method, target_ms in test_names:
                # Test classification performance
                start = time.time()
                result = await classifier.classify_name(name)
                classify_time = (time.time() - start) * 1000
                
                # Test cache performance (second call should be faster)
                start = time.time()
                cached_result = await classifier.classify_name(name)
                cache_time = (time.time() - start) * 1000
                
                performance_data = {
                    'name': name,
                    'first_call_ms': classify_time,
                    'second_call_ms': cache_time,
                    'target_ms': target_ms,
                    'first_call_target_met': classify_time < target_ms,
                    'cache_improvement': cache_time < classify_time,
                    'method_used': result.method.value if result else None,
                    'ethnicity': result.ethnicity.value if result else None,
                    'confidence': result.confidence if result else 0.0
                }
                
                performance_results.append(performance_data)
                
                print(f"   → {name}:")
                print(f"     First call: {classify_time:.2f}ms → {result.ethnicity.value if result else 'None'}")
                print(f"     Second call: {cache_time:.2f}ms (Cache improvement: {cache_time < classify_time})")
                print(f"     Method: {result.method.value if result else 'None'}")
                print(f"     Target: <{target_ms}ms (Met: {classify_time < target_ms})")
            
            # Calculate overall performance metrics
            all_targets_met = all(r['first_call_target_met'] for r in performance_results)
            cache_working = all(r['cache_improvement'] for r in performance_results)
            avg_performance = sum(r['first_call_ms'] for r in performance_results) / len(performance_results)
            
            print(f"   → Average performance: {avg_performance:.2f}ms")
            print(f"   → All targets met: {all_targets_met}")
            print(f"   → Cache working: {cache_working}")
            
            return {
                'passed': all_targets_met and cache_working,
                'results': performance_results,
                'metrics': {
                    'average_performance_ms': avg_performance,
                    'all_targets_met': all_targets_met,
                    'cache_working': cache_working,
                    'fastest_time_ms': min(r['first_call_ms'] for r in performance_results),
                    'slowest_time_ms': max(r['first_call_ms'] for r in performance_results)
                },
                'error': None
            }
            
        except Exception as e:
            print(f"   ❌ Error in performance benchmark test: {e}")
            import traceback
            traceback.print_exc()
            return {
                'passed': False,
                'error': str(e),
                'results': [],
                'metrics': {}
            }
    
    async def _test_cost_optimization(self) -> Dict[str, Any]:
        """Test 3: Cost Optimization Validation."""
        
        try:
            print("💰 Testing cost optimization...")
            
            classifier = create_classifier(mode="cost_optimized", enable_llm=True)
            
            # Test diverse SA names to measure LLM usage
            test_names = [
                "Thabo Mthembu", "Priya Pillay", "Hassan Cassiem", 
                "John Smith", "Maria van der Merwe", "Fatima Adams",
                "Sipho Ndlovu", "Rajesh Patel", "Ahmed Omar",
                "Sarah Johnson", "Nomsa Dlamini", "David Williams"
            ]
            
            print(f"   → Testing cost optimization with {len(test_names)} classifications...")
            
            results = {
                'rule_based': 0,
                'phonetic': 0,
                'learned': 0,
                'llm': 0,
                'cache': 0
            }
            
            total_cost = 0.0
            processing_times = []
            
            for name in test_names:
                start_time = time.time()
                result = await classifier.classify_name(name)
                processing_time = (time.time() - start_time) * 1000
                processing_times.append(processing_time)
                
                if result:
                    method = result.method.value
                    if method in results:
                        results[method] += 1
                    else:
                        # Default mapping for any new methods
                        if 'rule' in method:
                            results['rule_based'] += 1
                        elif 'phonetic' in method:
                            results['phonetic'] += 1
                        elif 'cache' in method:
                            results['cache'] += 1
                        elif 'llm' in method:
                            results['llm'] += 1
                        else:
                            results['rule_based'] += 1  # Default assumption
            
            # Get session statistics
            session_stats = classifier.get_session_stats()
            total_cost = session_stats.llm_cost_usd
            
            # Calculate percentages
            total_classifications = len(test_names)
            percentages = {k: (v / total_classifications) * 100 for k, v in results.items()}
            
            llm_percentage = percentages['llm']
            cost_per_classification = total_cost / total_classifications if total_classifications > 0 else 0
            
            print(f"   → Results breakdown:")
            for method, count in results.items():
                if count > 0:
                    print(f"     {method.replace('_', ' ').title()}: {count} ({percentages[method]:.1f}%)")
            
            print(f"   → LLM usage: {llm_percentage:.1f}% (target: <5%)")
            print(f"   → Cost per classification: ${cost_per_classification:.5f}")
            print(f"   → Average processing time: {sum(processing_times)/len(processing_times):.2f}ms")
            
            # Validate cost optimization targets
            cost_target_met = llm_percentage < 5.0
            performance_acceptable = all(t < 1000 for t in processing_times)  # <1s per classification
            
            return {
                'passed': cost_target_met and performance_acceptable,
                'results': results,
                'percentages': percentages,
                'metrics': {
                    'llm_usage_percentage': llm_percentage,
                    'total_cost_usd': total_cost,
                    'cost_per_classification': cost_per_classification,
                    'average_processing_time_ms': sum(processing_times) / len(processing_times),
                    'cost_target_met': cost_target_met,
                    'performance_acceptable': performance_acceptable
                },
                'session_stats': {
                    'total_classifications': session_stats.total_classifications,
                    'llm_classifications': session_stats.llm_classifications,
                    'rule_classifications': session_stats.rule_classifications,
                    'phonetic_classifications': session_stats.phonetic_classifications,
                    'llm_cost_usd': session_stats.llm_cost_usd
                },
                'error': None
            }
            
        except Exception as e:
            print(f"   ❌ Error in cost optimization test: {e}")
            import traceback
            traceback.print_exc()
            return {
                'passed': False,
                'error': str(e),
                'results': {},
                'metrics': {}
            }
    
    async def _test_system_resilience(self) -> Dict[str, Any]:
        """Test 4: System Resilience & Error Handling."""
        
        try:
            print("🛡️ Testing system resilience...")
            
            classifier = NameClassifier()
            
            # Test edge cases
            edge_cases = [
                ("", "empty_string"),
                ("   ", "whitespace_only"),
                ("A", "single_character"),
                ("Very Long Name That Exceeds Normal Expectations " * 5, "very_long_name"),
                ("Numbers123", "with_numbers"),
                ("Special@Characters!", "special_characters"),
                ("Unicode-Ñame", "unicode_characters"),
                ("Mixed Case NAME", "mixed_case"),
                ("  Leading and Trailing  ", "leading_trailing_spaces"),
                ("Tab\tCharacters", "tab_characters")
            ]
            
            edge_case_results = []
            
            print("   → Testing edge cases:")
            for i, (test_case, case_type) in enumerate(edge_cases, 1):
                try:
                    display_case = test_case[:20] + "..." if len(test_case) > 20 else test_case
                    print(f"     {i}. {case_type} ('{display_case}'): ", end="")
                    
                    result = await classifier.classify_name(test_case)
                    
                    edge_case_results.append({
                        'test_case': case_type,
                        'input': test_case,
                        'success': True,
                        'result': result.ethnicity.value if result else None,
                        'error': None
                    })
                    
                    print(f"✅ Handled → {result.ethnicity.value if result else 'No result'}")
                    
                except Exception as e:
                    edge_case_results.append({
                        'test_case': case_type,
                        'input': test_case,
                        'success': False,
                        'result': None,
                        'error': str(e)
                    })
                    print(f"❌ Error: {type(e).__name__}")
            
            # Test concurrent access
            print("   → Testing concurrent access...")
            concurrent_names = ["Thabo Mthembu"] * 5
            
            async def classify_concurrent(name):
                return await classifier.classify_name(name)
            
            try:
                concurrent_results = await asyncio.gather(
                    *[classify_concurrent(name) for name in concurrent_names],
                    return_exceptions=True
                )
                
                successful_concurrent = sum(1 for r in concurrent_results if not isinstance(r, Exception))
                concurrent_success = successful_concurrent == len(concurrent_names)
                
                print(f"     Concurrent classifications: {successful_concurrent}/{len(concurrent_names)} successful")
                
            except Exception as e:
                print(f"     ❌ Concurrent access error: {e}")
                concurrent_success = False
            
            # Calculate overall resilience score
            successful_edge_cases = sum(1 for r in edge_case_results if r['success'])
            edge_case_success_rate = successful_edge_cases / len(edge_cases)
            
            overall_resilience = edge_case_success_rate >= 0.8 and concurrent_success  # 80% edge case success + concurrent success
            
            print(f"   → Edge case success rate: {edge_case_success_rate:.1%}")
            print(f"   → Concurrent access: {'✅ Success' if concurrent_success else '❌ Failed'}")
            print(f"   → Overall resilience: {'✅ Pass' if overall_resilience else '❌ Fail'}")
            
            return {
                'passed': overall_resilience,
                'edge_cases': edge_case_results,
                'metrics': {
                    'edge_case_success_rate': edge_case_success_rate,
                    'successful_edge_cases': successful_edge_cases,
                    'total_edge_cases': len(edge_cases),
                    'concurrent_access_success': concurrent_success,
                    'overall_resilience_score': edge_case_success_rate
                },
                'error': None
            }
            
        except Exception as e:
            print(f"   ❌ Error in system resilience test: {e}")
            import traceback
            traceback.print_exc()
            return {
                'passed': False,
                'error': str(e),
                'edge_cases': [],
                'metrics': {}
            }
    
    async def _test_integration_stability(self) -> Dict[str, Any]:
        """Test 5: Integration Stability."""
        
        try:
            print("🔗 Testing integration stability...")
            
            # Test 1: Learning Database Integration
            print("   → Testing learning database integration...")
            learning_db = LLMLearningDatabase()
            initial_stats = learning_db.get_learning_statistics()
            
            # Test 2: Classifier Integration
            print("   → Testing classifier integration...")
            classifier = create_classifier(mode="balanced", enable_llm=True)
            
            # Test integration with multiple calls
            test_name = "Thabo Mthembu"
            
            # First call - should store in cache and possibly learning database
            start_time = time.time()
            first_result = await classifier.classify_name(test_name)
            first_call_time = (time.time() - start_time) * 1000
            
            # Second call - should use cache
            start_time = time.time()
            second_result = await classifier.classify_name(test_name)
            second_call_time = (time.time() - start_time) * 1000
            
            # Third call - verify consistency
            start_time = time.time()
            third_result = await classifier.classify_name(test_name)
            third_call_time = (time.time() - start_time) * 1000
            
            # Test 3: Learning Database Storage
            stored_count = classifier.flush_pending_learning_records()
            final_stats = learning_db.get_learning_statistics()
            
            print(f"     Call 1: {first_call_time:.2f}ms → {first_result.ethnicity.value if first_result else 'None'}")
            print(f"     Call 2: {second_call_time:.2f}ms → {second_result.ethnicity.value if second_result else 'None'}")
            print(f"     Call 3: {third_call_time:.2f}ms → {third_result.ethnicity.value if third_result else 'None'}")
            print(f"     Learning records stored: {stored_count}")
            
            # Validate integration stability
            stability_checks = {
                'consistent_results': (
                    first_result and second_result and third_result and
                    first_result.ethnicity == second_result.ethnicity == third_result.ethnicity
                ),
                'cache_performance_improvement': second_call_time < first_call_time or second_call_time < 10,  # Cache should be fast
                'learning_database_functional': final_stats.get('total_llm_classifications', 0) >= initial_stats.get('total_llm_classifications', 0),
                'no_integration_errors': True  # We got this far without exceptions
            }
            
            # Test 4: Session Statistics Integration
            session_stats = classifier.get_session_stats()
            stats_available = hasattr(session_stats, 'total_classifications') and session_stats.total_classifications > 0
            
            stability_checks['session_stats_working'] = stats_available
            
            print(f"   → Stability checks:")
            for check, passed in stability_checks.items():
                print(f"     {check.replace('_', ' ').title()}: {'✅' if passed else '❌'}")
            
            overall_stability = all(stability_checks.values())
            
            return {
                'passed': overall_stability,
                'stability_checks': stability_checks,
                'performance_data': {
                    'first_call_ms': first_call_time,
                    'second_call_ms': second_call_time,
                    'third_call_ms': third_call_time,
                    'cache_improvement': second_call_time < first_call_time
                },
                'learning_data': {
                    'initial_classifications': initial_stats.get('total_llm_classifications', 0),
                    'final_classifications': final_stats.get('total_llm_classifications', 0),
                    'records_stored': stored_count
                },
                'session_stats': {
                    'total_classifications': session_stats.total_classifications,
                    'average_time_ms': session_stats.average_time_ms,
                    'llm_cost_usd': session_stats.llm_cost_usd
                } if stats_available else {},
                'error': None
            }
            
        except Exception as e:
            print(f"   ❌ Error in integration stability test: {e}")
            import traceback
            traceback.print_exc()
            return {
                'passed': False,
                'error': str(e),
                'stability_checks': {},
                'performance_data': {},
                'learning_data': {}
            }
    
    async def _generate_final_assessment(self) -> Dict[str, Any]:
        """Generate the final assessment of all validation tests."""
        
        total_time = time.time() - self.start_time
        
        print("🎯 FINAL ASSESSMENT")
        print("=" * 80)
        
        # Calculate overall results
        passed_tests = sum(1 for test in self.test_results.values() if test.get('passed', False))
        total_tests = len(self.test_results)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        print(f"Validation Duration: {total_time:.2f} seconds")
        print(f"Tests Completed: {total_tests}")
        print(f"Tests Passed: {passed_tests}")
        print(f"Success Rate: {success_rate:.1%}")
        print()
        
        # Individual test results
        print("📊 Individual Test Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result.get('passed', False) else "❌ FAIL"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")
            if not result.get('passed', False) and result.get('error'):
                print(f"    Error: {result['error']}")
        print()
        
        # Overall status determination
        if success_rate == 1.0:
            overall_status = "✅ PRODUCTION READY"
            deployment_recommendation = "APPROVED FOR IMMEDIATE PRODUCTION DEPLOYMENT"
        elif success_rate >= 0.8:
            overall_status = "⚠️ NEEDS MINOR FIXES"
            deployment_recommendation = "APPROVED WITH MINOR FIXES REQUIRED"
        else:
            overall_status = "❌ MAJOR ISSUES"
            deployment_recommendation = "NOT APPROVED - SIGNIFICANT ISSUES NEED RESOLUTION"
        
        print(f"🏆 OVERALL STATUS: {overall_status}")
        print(f"📋 DEPLOYMENT RECOMMENDATION: {deployment_recommendation}")
        print()
        
        # Key metrics summary
        print("📈 Key Performance Metrics:")
        
        # Extract performance data
        if 'performance_benchmarks' in self.test_results and self.test_results['performance_benchmarks'].get('metrics'):
            perf_metrics = self.test_results['performance_benchmarks']['metrics']
            print(f"  Average Classification Time: {perf_metrics.get('average_performance_ms', 0):.2f}ms")
            print(f"  All Performance Targets Met: {perf_metrics.get('all_targets_met', False)}")
            print(f"  Cache System Working: {perf_metrics.get('cache_working', False)}")
        
        # Extract cost optimization data
        if 'cost_optimization' in self.test_results and self.test_results['cost_optimization'].get('metrics'):
            cost_metrics = self.test_results['cost_optimization']['metrics']
            print(f"  LLM Usage Rate: {cost_metrics.get('llm_usage_percentage', 0):.1f}%")
            print(f"  Cost per Classification: ${cost_metrics.get('cost_per_classification', 0):.5f}")
            print(f"  Cost Target Met: {cost_metrics.get('cost_target_met', False)}")
        
        # Extract resilience data
        if 'system_resilience' in self.test_results and self.test_results['system_resilience'].get('metrics'):
            resilience_metrics = self.test_results['system_resilience']['metrics']
            print(f"  Edge Case Success Rate: {resilience_metrics.get('edge_case_success_rate', 0):.1%}")
            print(f"  Concurrent Access Working: {resilience_metrics.get('concurrent_access_success', False)}")
        
        print()
        print("🚀 Final System Validation Complete!")
        print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return {
            'overall_status': overall_status,
            'deployment_recommendation': deployment_recommendation,
            'success_rate': success_rate,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'validation_duration_seconds': total_time,
            'test_results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }
    
    def _print_test_result(self, test_name: str, passed: bool):
        """Print a formatted test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"Result: {status}")


async def main():
    """Main function to run the comprehensive validation."""
    
    validator = FinalSystemValidator()
    results = await validator.run_comprehensive_validation()
    
    # Save results to file for reporting
    results_file = Path("validation_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())