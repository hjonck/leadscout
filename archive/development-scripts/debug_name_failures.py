#!/usr/bin/env python3
"""Debug script to investigate rule-based classification failures."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from leadscout.classification.rules import RuleBasedClassifier
from leadscout.classification.dictionaries import get_dictionaries

def test_failing_names():
    """Test the specific names that are failing rule classification."""
    
    classifier = RuleBasedClassifier()
    dictionaries = get_dictionaries()
    
    failing_names = [
        "ANDREAS PETRUS VAN DER MERWE",
        "HEINRICH ADRIAN TIMMIE", 
        "ALLISTER PIETERSEN",
        "NOMVUYISEKO EUNICE MSINDO"
    ]
    
    print("=== DEBUGGING RULE-BASED CLASSIFICATION FAILURES ===\n")
    
    for name in failing_names:
        print(f"Testing: {name}")
        print("-" * 50)
        
        # Test validation first
        validation = classifier.validate_name(name)
        print(f"Validation result:")
        print(f"  - Valid: {validation.is_valid}")
        print(f"  - Normalized: {validation.normalized_name}")
        print(f"  - Parts: {validation.name_parts}")
        print(f"  - Is multi-word: {validation.is_multi_word}")
        if validation.validation_errors:
            print(f"  - Errors: {validation.validation_errors}")
        
        # Check individual parts in dictionaries
        if validation.name_parts:
            print(f"\nDictionary lookups for individual parts:")
            for part in validation.name_parts:
                part_lower = part.lower()
                print(f"  Part: '{part}' ('{part_lower}')")
                
                found_in = []
                for ethnicity, dictionary in dictionaries.dictionaries.items():
                    if part_lower in dictionary:
                        entry = dictionary[part_lower]
                        found_in.append(f"{ethnicity.value} (conf: {entry.confidence})")
                
                if found_in:
                    print(f"    Found in: {', '.join(found_in)}")
                else:
                    print(f"    NOT FOUND in any dictionary")
        
        # Test classification
        try:
            result = classifier.classify_name(name)
            if result:
                print(f"\nClassification result:")
                print(f"  - Ethnicity: {result.ethnicity.value}")
                print(f"  - Confidence: {result.confidence}")
                print(f"  - Method: {result.method.value}")
            else:
                print(f"\nNo classification result returned")
        except Exception as e:
            print(f"\nClassification failed with error: {e}")
        
        print("\n" + "="*70 + "\n")

def check_dictionary_coverage():
    """Check what names are actually in the dictionaries."""
    
    dictionaries = get_dictionaries()
    
    print("=== DICTIONARY COVERAGE ANALYSIS ===\n")
    
    # Check for obvious missing names
    expected_names = {
        'andreas': 'WHITE (Afrikaans first name)',
        'petrus': 'WHITE (Afrikaans first name)', 
        'van': 'WHITE (Afrikaans particle)',
        'der': 'WHITE (Afrikaans particle)',
        'merwe': 'WHITE (Afrikaans surname)',
        'heinrich': 'WHITE (German/Afrikaans first name)',
        'adrian': 'WHITE (English first name)',
        'timmie': 'WHITE/COLOURED (surname)',
        'allister': 'WHITE (English first name)',
        'pietersen': 'WHITE/COLOURED (surname)',
        'nomvuyiseko': 'AFRICAN (Xhosa first name)',
        'eunice': 'WHITE (English first name)',
        'msindo': 'AFRICAN (surname)'
    }
    
    for name, expected in expected_names.items():
        print(f"Checking '{name}' (expected: {expected})")
        
        found_in = []
        for ethnicity, dictionary in dictionaries.dictionaries.items():
            if name in dictionary:
                entry = dictionary[name]
                found_in.append(f"{ethnicity.value} (conf: {entry.confidence})")
        
        if found_in:
            print(f"  ✓ Found in: {', '.join(found_in)}")
        else:
            print(f"  ✗ NOT FOUND - This is a gap!")
        print()

def check_coverage_stats():
    """Check overall dictionary statistics."""
    
    classifier = RuleBasedClassifier()
    stats = classifier.get_coverage_stats()
    
    print("=== DICTIONARY STATISTICS ===\n")
    print(f"Total names: {stats['total_names']}")
    print("\nBreakdown by ethnicity:")
    for ethnicity, count in stats['ethnicity_breakdown'].items():
        percentage = stats['coverage_percentages'][ethnicity.value]
        print(f"  {ethnicity.value}: {count} names ({percentage:.1f}%)")
    
    print(f"\nSpecial heuristics:")
    for name, count in stats['special_heuristics'].items():
        print(f"  {name}: {count}")

if __name__ == "__main__":
    test_failing_names()
    check_dictionary_coverage() 
    check_coverage_stats()