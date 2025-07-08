#!/usr/bin/env python3
"""
Learning System Performance Benchmarking Tool.

Comprehensive benchmarking of the learning database performance and cost optimization.
Measures processing speed, cost savings, and learning effectiveness.

Key Features:
- Processing speed benchmarking
- Cost optimization measurement
- Learning effectiveness validation
- Performance regression testing
- Comparative analysis over time

Usage:
    python benchmark_learning_performance.py
    
When to use:
- Performance optimization research
- Regression testing after changes
- Cost savings validation
- Learning system effectiveness measurement
- Performance baseline establishment
"""

import asyncio
import time
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from leadscout.classification.classifier import create_classifier

async def benchmark_learning_performance():
    """Benchmark performance with learning database active."""
    
    print("🚀 LEARNING DATABASE PERFORMANCE BENCHMARK")
    print("=" * 60)
    
    # Test dataset with mix of known and unknown names
    test_names = [
        # Known names (should hit cache/rules)
        "JOHN SMITH",
        "MARY JOHNSON", 
        "DAVID WILLIAMS",
        "SARAH BROWN",
        
        # Previously learned names (should hit cache)
        "XILUVA RIRHANDZU",
        "RHULANI TSAKANI",
        
        # New African names (will trigger LLM + learning)
        "NKOSANA MTHEMBU",
        "THANDIWE NGCOBO",
        "SIPHO MADONSELA",
        "NOMSA DLAMINI",
        
        # Mixed complexity
        "PRIYA PATEL",
        "AHMED HASSAN",
        "FATIMA KHAN",
        "CHEN WEI MING",
        "LUNGILE SIBEKO"
    ]
    
    print(f"Testing with {len(test_names)} names across different categories")
    print("Categories: Known rules, Previously learned, New African names, International")
    
    # Create classifier
    classifier = create_classifier(mode="cost_optimized", enable_llm=True)
    
    print(f"\n⏱️  Starting performance benchmark...")
    start_time = time.time()
    
    results = []
    for i, name in enumerate(test_names, 1):
        name_start = time.time()
        result = await classifier.classify_name(name)
        name_time = (time.time() - name_start) * 1000
        
        if result:
            results.append({
                'name': name,
                'ethnicity': result.ethnicity.value,
                'method': result.method.value,
                'confidence': result.confidence,
                'time_ms': name_time
            })
            
        # Progress indicator
        if i % 5 == 0:
            print(f"  Processed {i}/{len(test_names)} names...")
    
    total_time = time.time() - start_time
    
    # Get comprehensive stats
    stats = classifier.get_session_stats()
    learning_stats = classifier.learning_db.get_learning_statistics()
    
    print(f"\n📊 PERFORMANCE RESULTS")
    print("=" * 40)
    print(f"Total Processing Time: {total_time:.2f}s")
    print(f"Average Time per Name: {(total_time/len(test_names)*1000):.1f}ms")
    print(f"Names Processed: {len(results)}/{len(test_names)}")
    
    print(f"\n🎯 CLASSIFICATION BREAKDOWN")
    print("=" * 30)
    print(f"Rule-based: {stats.rule_classifications} ({stats.rule_hit_rate:.1%})")
    print(f"Phonetic: {stats.phonetic_classifications} ({stats.phonetic_hit_rate:.1%})")
    print(f"Learned/Cache: {stats.learned_hits} ({stats.learned_hit_rate:.1%})")
    print(f"LLM: {stats.llm_classifications} ({stats.llm_usage_rate:.1%})")
    print(f"Cache Hits: {stats.cache_hits} ({stats.cache_hit_rate:.1%})")
    
    print(f"\n💰 COST OPTIMIZATION")
    print("=" * 25)
    print(f"Total LLM Cost: ${stats.llm_cost_usd:.4f}")
    print(f"Learning Stores: {stats.learning_stores}")
    print(f"Cost per Classification: ${stats.llm_cost_usd/len(results):.5f}")
    print(f"LLM Efficiency: {(1 - stats.llm_usage_rate) * 100:.1f}% non-LLM")
    
    print(f"\n🧠 LEARNING DATABASE STATUS")
    print("=" * 35)
    print(f"Stored Classifications: {learning_stats.get('total_llm_classifications', 0)}")
    print(f"Active Patterns: {learning_stats.get('active_learned_patterns', 0)}")
    print(f"Phonetic Families: {learning_stats.get('phonetic_families', 0)}")
    print(f"Learning Efficiency: {learning_stats.get('learning_efficiency', 0):.3f} patterns/LLM")
    
    # Method distribution analysis
    method_counts = {}
    fast_classifications = 0
    
    for result in results:
        method = result['method']
        method_counts[method] = method_counts.get(method, 0) + 1
        
        # Count fast classifications (< 100ms)
        if result['time_ms'] < 100:
            fast_classifications += 1
    
    print(f"\n⚡ SPEED OPTIMIZATION")
    print("=" * 25)
    print(f"Fast Classifications (<100ms): {fast_classifications}/{len(results)} ({fast_classifications/len(results)*100:.1f}%)")
    
    print(f"\nMethod Distribution:")
    for method, count in sorted(method_counts.items()):
        percentage = count / len(results) * 100
        print(f"  {method}: {count} ({percentage:.1f}%)")
    
    # Performance targets validation
    print(f"\n✅ PERFORMANCE TARGETS VALIDATION")
    print("=" * 40)
    
    targets = {
        "LLM usage <5%": stats.llm_usage_rate < 0.05,
        "Average time <50ms": (total_time/len(test_names)*1000) < 50,
        "Cost per classification <$0.001": (stats.llm_cost_usd/len(results)) < 0.001,
        "Fast classification rate >80%": (fast_classifications/len(results)) > 0.8,
        "Learning patterns generated": learning_stats.get('active_learned_patterns', 0) > 0,
        "Learning efficiency >1.0": learning_stats.get('learning_efficiency', 0) > 1.0
    }
    
    passed_targets = 0
    for target, passed in targets.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {target}: {status}")
        if passed:
            passed_targets += 1
    
    overall_performance = passed_targets >= 4  # At least 4/6 targets
    
    print(f"\n🎯 OVERALL PERFORMANCE: {'✅ EXCELLENT' if overall_performance else '❌ NEEDS IMPROVEMENT'}")
    print(f"   Targets Met: {passed_targets}/6")
    
    # Sample results
    print(f"\n📋 SAMPLE CLASSIFICATION RESULTS")
    print("=" * 40)
    for result in results[:8]:  # Show first 8 results
        print(f"  {result['name']:<20} → {result['ethnicity']:<10} ({result['method']:<8}) {result['time_ms']:.1f}ms")
    
    if len(results) > 8:
        print(f"  ... and {len(results) - 8} more")
    
    return {
        'total_time': total_time,
        'results_count': len(results),
        'stats': stats,
        'learning_stats': learning_stats,
        'performance_targets_met': passed_targets,
        'overall_performance': overall_performance
    }

if __name__ == "__main__":
    asyncio.run(benchmark_learning_performance())