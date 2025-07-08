#!/usr/bin/env python3
"""
Simple debug test for learning database integration.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from leadscout.classification.classifier import create_classifier

async def test_single_name():
    """Test single name classification to debug learning integration."""
    
    print("🧪 Simple Learning Debug Test")
    print("=" * 40)
    
    # Test with a single name that should trigger LLM
    test_name = "XILUVA RIRHANDZU"
    
    print(f"Testing name: {test_name}")
    
    # Remove existing database
    import os
    db_files = ["cache/llm_learning.db", "cache/llm_learning.db-wal", "cache/llm_learning.db-shm"]
    for db_file in db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"Removed {db_file}")
    
    # Create classifier
    classifier = create_classifier(mode="cost_optimized", enable_llm=True)
    
    print("Classifier created, testing classification...")
    
    # Test classification
    result = await classifier.classify_name(test_name)
    
    if result:
        print(f"✅ Classification successful:")
        print(f"  Ethnicity: {result.ethnicity.value}")
        print(f"  Confidence: {result.confidence:.3f}")
        print(f"  Method: {result.method.value}")
        print(f"  Processing time: {result.processing_time_ms:.1f}ms")
    else:
        print("❌ Classification failed")
    
    # Get stats
    stats = classifier.get_session_stats()
    print(f"\n📊 Session Stats:")
    print(f"  Total: {stats.total_classifications}")
    print(f"  LLM: {stats.llm_classifications}")
    print(f"  Learning stores: {stats.learning_stores}")
    print(f"  LLM cost: ${stats.llm_cost_usd:.4f}")
    
    # Check learning database using the same instance
    learning_stats = classifier.learning_db.get_learning_statistics()
    
    print(f"\n🧠 Learning Database Stats:")
    print(f"  Stored classifications: {learning_stats.get('total_llm_classifications', 0)}")
    print(f"  Active patterns: {learning_stats.get('active_learned_patterns', 0)}")
    print(f"  Phonetic families: {learning_stats.get('phonetic_families', 0)}")
    
    return result, stats, learning_stats

if __name__ == "__main__":
    asyncio.run(test_single_name())