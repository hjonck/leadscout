#!/usr/bin/env python3
"""
Test learning effectiveness by running the same name twice.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from leadscout.classification.classifier import create_classifier

async def test_learning_effectiveness():
    """Test that learned patterns reduce LLM usage."""
    
    print("🧪 Learning Effectiveness Test")
    print("=" * 50)
    
    test_name = "XILUVA RIRHANDZU"
    
    print(f"Testing name: {test_name}")
    print("(Database already contains learning data from previous test)")
    
    # Create classifier
    classifier = create_classifier(mode="cost_optimized", enable_llm=True)
    
    print("\n🔍 First classification (should use learned pattern)...")
    
    # Test classification
    result1 = await classifier.classify_name(test_name)
    
    if result1:
        print(f"✅ Classification successful:")
        print(f"  Ethnicity: {result1.ethnicity.value}")
        print(f"  Confidence: {result1.confidence:.3f}")
        print(f"  Method: {result1.method.value}")
        print(f"  Processing time: {result1.processing_time_ms:.1f}ms")
    else:
        print("❌ Classification failed")
    
    # Get stats
    stats1 = classifier.get_session_stats()
    print(f"\n📊 First Run Stats:")
    print(f"  Total: {stats1.total_classifications}")
    print(f"  LLM: {stats1.llm_classifications}")
    print(f"  Learned: {stats1.learned_hits}")
    print(f"  Learning stores: {stats1.learning_stores}")
    print(f"  LLM cost: ${stats1.llm_cost_usd:.4f}")
    
    print(f"\n🔍 Second classification (should definitely use learned pattern)...")
    
    # Test same name again
    result2 = await classifier.classify_name(test_name)
    
    if result2:
        print(f"✅ Classification successful:")
        print(f"  Ethnicity: {result2.ethnicity.value}")
        print(f"  Confidence: {result2.confidence:.3f}")
        print(f"  Method: {result2.method.value}")
        print(f"  Processing time: {result2.processing_time_ms:.1f}ms")
    else:
        print("❌ Classification failed")
    
    # Get final stats
    stats2 = classifier.get_session_stats()
    print(f"\n📊 Final Session Stats:")
    print(f"  Total: {stats2.total_classifications}")
    print(f"  LLM: {stats2.llm_classifications}")
    print(f"  Learned: {stats2.learned_hits}")
    print(f"  Learning stores: {stats2.learning_stores}")
    print(f"  LLM cost: ${stats2.llm_cost_usd:.4f}")
    
    # Analysis
    print(f"\n🎯 LEARNING EFFECTIVENESS ANALYSIS")
    print("=" * 40)
    
    if stats2.learned_hits > 0:
        print(f"✅ SUCCESS: {stats2.learned_hits} classifications used learned patterns!")
        print(f"✅ LLM Usage: {stats2.llm_classifications}/{stats2.total_classifications} ({stats2.llm_usage_rate:.1%})")
        print(f"✅ Learning Rate: {stats2.learned_hit_rate:.1%}")
        print(f"✅ Cost Savings: Learning patterns avoid LLM costs")
        
        if result1 and result1.method.value == 'cache':
            print(f"✅ CACHE HIT: First run used cached/learned result!")
        elif result2 and result2.method.value == 'cache':
            print(f"✅ CACHE HIT: Second run used cached/learned result!")
        else:
            print(f"ℹ️  No cache hits, but learned patterns may be building")
    else:
        print(f"❌ No learned patterns used yet")
        print(f"ℹ️  This might be expected for new names or patterns still building")
    
    return {
        'total_classifications': stats2.total_classifications,
        'llm_usage': stats2.llm_classifications,
        'learned_hits': stats2.learned_hits,
        'llm_usage_rate': stats2.llm_usage_rate,
        'learned_hit_rate': stats2.learned_hit_rate,
        'cost_usd': stats2.llm_cost_usd
    }

if __name__ == "__main__":
    asyncio.run(test_learning_effectiveness())