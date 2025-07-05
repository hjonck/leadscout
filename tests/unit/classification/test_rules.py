#!/usr/bin/env python3
"""Quick test script for the classification system."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from leadscout.classification import RuleBasedClassifier, EthnicityType


def test_rule_classifier():
    """Test the rule-based classifier with sample South African names."""
    classifier = RuleBasedClassifier()
    
    # Test names from different ethnic groups
    test_names = [
        # African names
        ("Bongani Mthembu", EthnicityType.AFRICAN),
        ("Thabo Mandela", EthnicityType.AFRICAN),
        ("Nomsa Khumalo", EthnicityType.AFRICAN),
        ("Kagiso Ramaphosa", EthnicityType.AFRICAN),
        
        # Indian names
        ("Priya Pillay", EthnicityType.INDIAN),
        ("Rajesh Naidoo", EthnicityType.INDIAN),
        ("Anita Reddy", EthnicityType.INDIAN),
        ("Ashwin Patel", EthnicityType.INDIAN),
        
        # Cape Malay names
        ("Abdullah Cassiem", EthnicityType.CAPE_MALAY),
        ("Fatima Hendricks", EthnicityType.CAPE_MALAY),
        ("Mohamed Adams", EthnicityType.CAPE_MALAY),
        
        # Coloured names (month surnames)
        ("John September", EthnicityType.COLOURED),
        ("Mary April", EthnicityType.COLOURED),
        ("David October", EthnicityType.COLOURED),
        
        # White names
        ("Pieter van der Merwe", EthnicityType.WHITE),
        ("Johannes Botha", EthnicityType.WHITE),
        ("John Smith", EthnicityType.WHITE),
        
        # Unknown names (should return None)
        ("Unknown McUnknown", None),
    ]
    
    print("Testing Rule-Based Classification:")
    print("=" * 50)
    
    correct_classifications = 0
    total_tests = 0
    
    for name, expected_ethnicity in test_names:
        try:
            result = classifier.classify_name(name)
            
            if result is None:
                if expected_ethnicity is None:
                    print(f"✓ {name:<25} -> No classification (expected)")
                    correct_classifications += 1
                else:
                    print(f"✗ {name:<25} -> No classification (expected {expected_ethnicity.value})")
            else:
                if result.ethnicity == expected_ethnicity:
                    print(f"✓ {name:<25} -> {result.ethnicity.value:<12} (confidence: {result.confidence:.2f})")
                    correct_classifications += 1
                else:
                    expected_str = expected_ethnicity.value if expected_ethnicity else "None"
                    print(f"✗ {name:<25} -> {result.ethnicity.value:<12} (expected: {expected_str})")
                    
            total_tests += 1
            
        except Exception as e:
            print(f"✗ {name:<25} -> ERROR: {e}")
            total_tests += 1
    
    print("\n" + "=" * 50)
    print(f"Accuracy: {correct_classifications}/{total_tests} ({correct_classifications/total_tests*100:.1f}%)")
    
    # Print coverage statistics
    print("\nDictionary Coverage:")
    stats = classifier.get_coverage_stats()
    for ethnicity, count in stats["ethnicity_breakdown"].items():
        print(f"  {ethnicity.value:<12}: {count:>4} names")
    print(f"  {'Total':<12}: {stats['total_names']:>4} names")


if __name__ == "__main__":
    test_rule_classifier()