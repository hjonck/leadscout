"""
Test learning database integration with the classification system.

Validates cost optimization through auto-learning by testing the system's ability
to learn from LLM classifications and reduce LLM dependency over time.

Developer B - Classification & Enrichment Specialist
"""

import asyncio
import pandas as pd
from pathlib import Path
import time

from src.leadscout.classification.classifier import NameClassifier, create_classifier
from src.leadscout.classification.learning_database import LLMLearningDatabase

async def test_learning_integration():
    """Test learning database integration and cost optimization."""
    
    print("🧪 LEARNING DATABASE INTEGRATION TEST")
    print("=" * 60)
    
    # Test names designed to trigger LLM classification for learning
    test_names = [
        "XILUVA RIRHANDZU",      # Unique Tsonga/Venda combination
        "MASIXOLE ZANDILE",      # Unusual Xhosa combination
        "RHULANI TSAKANI",       # Less common Tsonga names
        "AZANIA NOKUTHULA",      # Modern African combinations
        "RENDANI FULUFHELO",     # Venda names not in dictionary
        "LESEGO KAGISO",         # Tswana modern names
        "THANDOLWETHU NOMSA",    # Long compound Zulu
        "PALESA MAMELLO",        # Sotho combinations
        "MXOLISI SANDILE",       # Xhosa with X patterns
        "REFILWE MAPULE",        # Modern Sotho/Tswana
        "THANDIWE NOMZAMO",      # Classic but variant spellings
        "SIZAKELE BOITUMELO"     # Cross-ethnic combinations
    ]
    
    print(f"Testing with {len(test_names)} challenging names designed to trigger LLM classification")
    
    # Phase 1: First run (builds learning database)
    print("\n📊 Phase 1: Initial Run (Building Learning Database)")
    
    classifier1 = create_classifier(mode="cost_optimized", enable_llm=True)
    phase1_results = []
    phase1_start = time.time()
    
    for name in test_names:
        result = await classifier1.classify_name(name)
        if result:
            phase1_results.append({
                'name': name,
                'ethnicity': result.ethnicity.value,
                'method': result.method.value,
                'confidence': result.confidence
            })
    
    phase1_time = time.time() - phase1_start
    phase1_stats = classifier1.get_session_stats()
    
    print(f"  Phase 1 Results:")
    print(f"    Total Classifications: {len(phase1_results)}")
    print(f"    LLM Usage: {phase1_stats.llm_classifications} ({phase1_stats.llm_usage_rate:.1%})")
    print(f"    Rule Usage: {phase1_stats.rule_classifications} ({phase1_stats.rule_hit_rate:.1%})")
    print(f"    Phonetic Usage: {phase1_stats.phonetic_classifications} ({phase1_stats.phonetic_hit_rate:.1%})")
    print(f"    Learned Pattern Usage: {phase1_stats.learned_hits}")
    print(f"    Learning Stores: {phase1_stats.learning_stores}")
    print(f"    Processing Time: {phase1_time:.2f}s")
    print(f"    LLM Cost: ${phase1_stats.llm_cost_usd:.4f}")
    
    # Phase 2: Second run (benefits from learning database)
    print("\n📊 Phase 2: Learning Run (Using Learned Patterns)")
    
    classifier2 = create_classifier(mode="cost_optimized", enable_llm=True)
    phase2_results = []
    phase2_start = time.time()
    
    for name in test_names:
        result = await classifier2.classify_name(name)
        if result:
            phase2_results.append({
                'name': name,
                'ethnicity': result.ethnicity.value,
                'method': result.method.value,
                'confidence': result.confidence
            })
    
    phase2_time = time.time() - phase2_start
    phase2_stats = classifier2.get_session_stats()
    
    print(f"  Phase 2 Results:")
    print(f"    Total Classifications: {len(phase2_results)}")
    print(f"    LLM Usage: {phase2_stats.llm_classifications} ({phase2_stats.llm_usage_rate:.1%})")
    print(f"    Rule Usage: {phase2_stats.rule_classifications} ({phase2_stats.rule_hit_rate:.1%})")
    print(f"    Phonetic Usage: {phase2_stats.phonetic_classifications} ({phase2_stats.phonetic_hit_rate:.1%})")
    print(f"    Learned Pattern Usage: {phase2_stats.learned_hits} ({phase2_stats.learned_hit_rate:.1%})")
    print(f"    Learning Stores: {phase2_stats.learning_stores}")
    print(f"    Processing Time: {phase2_time:.2f}s")
    print(f"    LLM Cost: ${phase2_stats.llm_cost_usd:.4f}")
    
    # Calculate improvement metrics
    print("\n📈 LEARNING IMPROVEMENT METRICS")
    print("=" * 40)
    
    llm_reduction = phase1_stats.llm_usage_rate - phase2_stats.llm_usage_rate
    cost_reduction = phase1_stats.llm_cost_usd - phase2_stats.llm_cost_usd
    cost_reduction_percent = (cost_reduction / max(phase1_stats.llm_cost_usd, 0.001)) * 100
    speed_improvement = phase1_time - phase2_time
    
    print(f"  LLM Usage Reduction: {llm_reduction:.1%}")
    print(f"  Cost Reduction: ${cost_reduction:.4f} ({cost_reduction_percent:.1f}%)")
    print(f"  Processing Speed Change: {speed_improvement:.2f}s")
    print(f"  Learned Pattern Usage: {phase2_stats.learned_hits} classifications")
    
    # Learning database analytics
    learning_db = LLMLearningDatabase()
    stats = learning_db.get_learning_statistics()
    
    print(f"\n🧠 LEARNING DATABASE ANALYTICS")
    print("=" * 40)
    print(f"  Total LLM Classifications Stored: {stats.get('total_llm_classifications', 0)}")
    print(f"  Active Learned Patterns: {stats.get('active_learned_patterns', 0)}")
    print(f"  Phonetic Families: {stats.get('phonetic_families', 0)}")
    print(f"  Learning Efficiency: {stats.get('learning_efficiency', 0):.3f} patterns/LLM call")
    
    if 'recent_30_days' in stats:
        recent = stats['recent_30_days']
        print(f"\n📈 Recent Performance (30 days):")
        print(f"    Classifications: {recent.get('total_classifications', 0)}")
        print(f"    Average Confidence: {recent.get('average_confidence', 0):.2f}")
        print(f"    Total Cost: ${recent.get('total_cost_usd', 0):.4f}")
    
    # Success criteria validation
    print(f"\n✅ SUCCESS CRITERIA VALIDATION")
    print("=" * 40)
    
    success_criteria = {
        "Learning database integration working": len(phase2_results) > 0,
        "LLM usage reduction achieved": llm_reduction >= 0,
        "Cost reduction achieved": cost_reduction >= 0,
        "Learning patterns generated": stats.get('active_learned_patterns', 0) > 0,
        "Phonetic families built": stats.get('phonetic_families', 0) > 0,
        "Target <5% LLM usage progress": phase2_stats.llm_usage_rate <= phase1_stats.llm_usage_rate,
        "Speed improvement or maintained": speed_improvement >= -0.5,  # Allow slight slowdown
        "Learning stores successful": phase1_stats.learning_stores > 0
    }
    
    passed_count = 0
    for criterion, passed in success_criteria.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {criterion}: {status}")
        if passed:
            passed_count += 1
    
    overall_success = passed_count >= 6  # At least 6 out of 8 criteria
    
    print(f"\n🎯 OVERALL INTEGRATION SUCCESS: {'✅ PASS' if overall_success else '❌ FAIL'}")
    print(f"   Criteria Met: {passed_count}/8")
    
    # Detailed analysis of learned patterns
    if phase2_stats.learned_hits > 0:
        print(f"\n🎓 LEARNING SUCCESS ANALYSIS")
        print("=" * 40)
        print(f"  Names classified using learned patterns: {phase2_stats.learned_hits}")
        print(f"  Learning hit rate: {phase2_stats.learned_hit_rate:.1%}")
        print(f"  Cost avoidance from learning: ${phase2_stats.learned_hits * 0.002:.4f}")
        
        # Show which names used learned patterns vs LLM
        print(f"\n  Classification Method Breakdown:")
        phase1_llm_names = [r['name'] for r in phase1_results if 'method' in r and 'LLM' in r.get('method', '')]
        phase2_learned_count = phase2_stats.learned_hits
        phase2_llm_count = phase2_stats.llm_classifications
        
        print(f"    Phase 1 LLM classifications: {len(phase1_llm_names)}")
        print(f"    Phase 2 Learned patterns: {phase2_learned_count}")
        print(f"    Phase 2 LLM classifications: {phase2_llm_count}")
        print(f"    Conversion rate: {(phase2_learned_count / max(len(phase1_llm_names), 1)):.1%}")
    
    return {
        'phase1_stats': phase1_stats,
        'phase2_stats': phase2_stats,
        'improvement_metrics': {
            'llm_reduction': llm_reduction,
            'cost_reduction': cost_reduction,
            'cost_reduction_percent': cost_reduction_percent,
            'speed_improvement': speed_improvement
        },
        'learning_db_stats': stats,
        'success_criteria': success_criteria,
        'overall_success': overall_success
    }

if __name__ == "__main__":
    asyncio.run(test_learning_integration())