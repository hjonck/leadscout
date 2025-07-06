#!/usr/bin/env python3
"""
Final system validation with learning database active.
"""

import asyncio
import time
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from leadscout.classification.classifier import create_classifier

async def validate_system_performance():
    """Final validation of complete system with learning database."""
    
    print("🔍 FINAL SYSTEM VALIDATION")
    print("=" * 50)
    
    # Comprehensive test across all classification methods
    test_cases = [
        # Rule-based (should be instant)
        ("JOHN SMITH", "rule_based", "white"),
        ("PRIYA PATEL", "rule_based", "indian"),
        ("AHMED HASSAN", "rule_based", "cape_malay"),
        
        # Learned patterns (should hit cache)
        ("XILUVA RIRHANDZU", "cache", "african"),
        ("RHULANI TSAKANI", "cache", "african"), 
        
        # Phonetic (if available)
        ("JOHNATHAN SMITH", "rule_based", "white"),  # Should match JOHN via rules
        
        # New name (will trigger LLM + learning)
        ("BANDILE MNGUNI", None, "african"),  # Unknown name, will learn
    ]
    
    print(f"Testing {len(test_cases)} validation cases")
    
    # Create classifier
    classifier = create_classifier(mode="cost_optimized", enable_llm=True)
    
    print(f"\n🧪 Running validation cases...")
    
    validation_results = []
    total_start = time.time()
    
    for i, (name, expected_method, expected_ethnicity) in enumerate(test_cases, 1):
        case_start = time.time()
        result = await classifier.classify_name(name)
        case_time = (time.time() - case_start) * 1000
        
        if result:
            success = result.ethnicity.value == expected_ethnicity
            method_match = expected_method is None or result.method.value == expected_method
            
            validation_results.append({
                'name': name,
                'expected_ethnicity': expected_ethnicity,
                'actual_ethnicity': result.ethnicity.value,
                'expected_method': expected_method,
                'actual_method': result.method.value,
                'confidence': result.confidence,
                'time_ms': case_time,
                'ethnicity_correct': success,
                'method_correct': method_match,
                'overall_correct': success and method_match
            })
            
            status = "✅" if success and method_match else "⚠️" if success else "❌"
            print(f"  {i}. {name:<20} → {result.ethnicity.value:<10} ({result.method.value:<10}) {case_time:6.1f}ms {status}")
        else:
            print(f"  {i}. {name:<20} → FAILED (no result)")
            validation_results.append({
                'name': name,
                'overall_correct': False,
                'time_ms': case_time
            })
    
    total_time = time.time() - total_start
    
    # Get comprehensive stats
    stats = classifier.get_session_stats()
    learning_stats = classifier.learning_db.get_learning_statistics()
    
    print(f"\n📊 VALIDATION SUMMARY")
    print("=" * 30)
    
    correct_results = sum(1 for r in validation_results if r.get('overall_correct', False))
    ethnicity_correct = sum(1 for r in validation_results if r.get('ethnicity_correct', False))
    method_correct = sum(1 for r in validation_results if r.get('method_correct', False))
    
    print(f"Overall Accuracy: {correct_results}/{len(test_cases)} ({correct_results/len(test_cases)*100:.1f}%)")
    print(f"Ethnicity Accuracy: {ethnicity_correct}/{len(test_cases)} ({ethnicity_correct/len(test_cases)*100:.1f}%)")
    print(f"Method Prediction: {method_correct}/{len(test_cases)} ({method_correct/len(test_cases)*100:.1f}%)")
    print(f"Total Processing Time: {total_time:.2f}s")
    print(f"Average Time per Case: {total_time/len(test_cases)*1000:.1f}ms")
    
    print(f"\n🎯 SYSTEM PERFORMANCE")
    print("=" * 25)
    print(f"Rule Classifications: {stats.rule_classifications} ({stats.rule_hit_rate:.1%})")
    print(f"Phonetic Classifications: {stats.phonetic_classifications} ({stats.phonetic_hit_rate:.1%})")
    print(f"Learned/Cache Hits: {stats.learned_hits} ({stats.learned_hit_rate:.1%})")
    print(f"LLM Classifications: {stats.llm_classifications} ({stats.llm_usage_rate:.1%})")
    print(f"Learning Stores: {stats.learning_stores}")
    
    print(f"\n💰 COST & EFFICIENCY")
    print("=" * 20)
    print(f"Total LLM Cost: ${stats.llm_cost_usd:.4f}")
    print(f"Cost per Classification: ${stats.llm_cost_usd/len(test_cases):.5f}")
    print(f"Non-LLM Efficiency: {(1 - stats.llm_usage_rate)*100:.1f}%")
    
    print(f"\n🧠 LEARNING STATUS")
    print("=" * 18)
    print(f"Total Stored Classifications: {learning_stats.get('total_llm_classifications', 0)}")
    print(f"Active Patterns: {learning_stats.get('active_learned_patterns', 0)}")
    print(f"Phonetic Families: {learning_stats.get('phonetic_families', 0)}")
    print(f"Learning Efficiency: {learning_stats.get('learning_efficiency', 0):.3f}")
    
    # Performance validation
    print(f"\n✅ SYSTEM VALIDATION RESULTS")
    print("=" * 35)
    
    validations = {
        "Classification Accuracy >90%": (correct_results/len(test_cases)) > 0.9,
        "Average Response Time <500ms": (total_time/len(test_cases)*1000) < 500,
        "LLM Usage <20%": stats.llm_usage_rate < 0.2,
        "Learning System Active": learning_stats.get('total_llm_classifications', 0) > 0,
        "Cost per Classification <$0.01": (stats.llm_cost_usd/len(test_cases)) < 0.01,
        "Cache/Learning Working": stats.learned_hits > 0 or stats.cache_hits > 0
    }
    
    passed_validations = 0
    for validation, passed in validations.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {validation}: {status}")
        if passed:
            passed_validations += 1
    
    system_health = passed_validations >= 5  # At least 5/6 validations
    
    print(f"\n🎯 SYSTEM HEALTH: {'✅ EXCELLENT' if system_health else '❌ ISSUES DETECTED'}")
    print(f"   Validations Passed: {passed_validations}/6")
    
    # Learning effectiveness check
    if stats.learned_hits > 0:
        print(f"\n🎓 LEARNING EFFECTIVENESS CONFIRMED")
        print(f"   Learned patterns are actively reducing LLM usage!")
        print(f"   Cache hits: {stats.learned_hits} classifications")
    
    return {
        'validation_accuracy': correct_results/len(test_cases),
        'system_health': system_health,
        'learning_active': stats.learned_hits > 0,
        'performance_stats': stats,
        'learning_stats': learning_stats
    }

if __name__ == "__main__":
    asyncio.run(validate_system_performance())