#!/usr/bin/env python3
"""Test script for the phonetic classification system."""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from leadscout.classification.phonetic import PhoneticClassifier


async def test_phonetic_classifier():
    """Test the phonetic classifier with variant spellings."""
    classifier = PhoneticClassifier()
    
    # Test names with common variants/misspellings
    test_cases = [
        # Name variants that should match phonetically
        ("Bonganni", "african"),  # Variant of Bongani
        ("Thapho", "african"),    # Variant of Thabo
        ("Pilai", "indian"),      # Variant of Pillay
        ("Reddi", "indian"),      # Variant of Reddy
        ("Hendrix", "cape_malay"), # Variant of Hendricks
        ("Boter", "white"),       # Variant of Botha
        ("Smyth", "white"),       # Variant of Smith
        
        # Names not in dictionary but phonetically similar
        ("Ramafoze", "african"),  # Similar to Ramaphosa
        ("Naideau", "indian"),    # Similar to Naidoo
        
        # Names that should not match
        ("Xylophen", None),       # No phonetic matches expected
    ]
    
    print("Testing Phonetic Classification:")
    print("=" * 60)
    
    correct_classifications = 0
    total_tests = 0
    
    for name, expected_ethnicity in test_cases:
        try:
            result = await classifier.classify_name(name)
            
            if result is None:
                if expected_ethnicity is None:
                    print(f"✓ {name:<15} -> No classification (expected)")
                    correct_classifications += 1
                else:
                    print(f"✗ {name:<15} -> No classification (expected {expected_ethnicity})")
            else:
                ethnicity_str = result.ethnicity.value
                if result.ethnicity.value == expected_ethnicity:
                    print(f"✓ {name:<15} -> {ethnicity_str:<12} (confidence: {result.confidence:.2f}) [{result.phonetic_details.top_algorithm}]")
                    correct_classifications += 1
                else:
                    expected_str = expected_ethnicity if expected_ethnicity else "None"
                    print(f"✗ {name:<15} -> {ethnicity_str:<12} (expected: {expected_str}) [{result.phonetic_details.top_algorithm}]")
                    
                # Show some phonetic details
                if result.phonetic_details:
                    print(f"    Algorithms: {len(result.phonetic_details.matches)} matches, consensus: {result.phonetic_details.consensus_score:.2f}")
                    
            total_tests += 1
            
        except Exception as e:
            print(f"✗ {name:<15} -> ERROR: {e}")
            total_tests += 1
    
    print("\n" + "=" * 60)
    print(f"Accuracy: {correct_classifications}/{total_tests} ({correct_classifications/total_tests*100:.1f}%)")
    
    # Test finding similar names
    print("\nTesting Similar Name Finding:")
    print("-" * 40)
    
    test_name = "Bonganni"
    similar = classifier.find_similar_names(test_name, limit=5)
    print(f"Similar names to '{test_name}':")
    for match in similar:
        print(f"  {match.matched_name:<12} ({match.matched_ethnicity.value:<10}) - {match.algorithm:<12} - {match.similarity_score:.2f}")
    
    # Print phonetic statistics
    print("\nPhonetic System Statistics:")
    print("-" * 40)
    stats = classifier.get_phonetic_stats()
    print(f"Jellyfish available: {stats['jellyfish_available']}")
    print(f"Algorithms: {', '.join(stats['algorithms_available'])}")
    print("Cached mappings:")
    for algorithm, count in stats['cached_phonetic_mappings'].items():
        print(f"  {algorithm:<12}: {count:>4} codes")


if __name__ == "__main__":
    asyncio.run(test_phonetic_classifier())