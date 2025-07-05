"""Comprehensive South African test names dataset for validation.

This module provides test datasets for validating the classification system
with known South African names across all ethnic groups.
"""

from typing import List, Dict, Any
from leadscout.classification.dictionaries import EthnicityType


def get_test_dataset() -> List[Dict[str, Any]]:
    """Get comprehensive test dataset of South African names."""
    return [
        # African names - Nguni (Zulu, Xhosa)
        {"name": "Thabo Mthembu", "expected_ethnicity": EthnicityType.AFRICAN, "category": "nguni"},
        {"name": "Bongani Nkomo", "expected_ethnicity": EthnicityType.AFRICAN, "category": "nguni"},
        {"name": "Nomsa Dlamini", "expected_ethnicity": EthnicityType.AFRICAN, "category": "nguni"},
        {"name": "Sipho Ndlovu", "expected_ethnicity": EthnicityType.AFRICAN, "category": "nguni"},
        {"name": "Zodwa Khumalo", "expected_ethnicity": EthnicityType.AFRICAN, "category": "nguni"},
        {"name": "Mandla Buthelezi", "expected_ethnicity": EthnicityType.AFRICAN, "category": "nguni"},
        {"name": "Thandi Cele", "expected_ethnicity": EthnicityType.AFRICAN, "category": "nguni"},
        {"name": "Sandile Makhanya", "expected_ethnicity": EthnicityType.AFRICAN, "category": "nguni"},
        {"name": "Nokuthula Zulu", "expected_ethnicity": EthnicityType.AFRICAN, "category": "nguni"},
        {"name": "Siyabonga Gumede", "expected_ethnicity": EthnicityType.AFRICAN, "category": "nguni"},
        
        # African names - Xhosa specific
        {"name": "Nelson Mandela", "expected_ethnicity": EthnicityType.AFRICAN, "category": "xhosa"},
        {"name": "Thabo Mbeki", "expected_ethnicity": EthnicityType.AFRICAN, "category": "xhosa"},
        {"name": "Walter Sisulu", "expected_ethnicity": EthnicityType.AFRICAN, "category": "xhosa"},
        {"name": "Andile Mda", "expected_ethnicity": EthnicityType.AFRICAN, "category": "xhosa"},
        {"name": "Nomonde Dlomo", "expected_ethnicity": EthnicityType.AFRICAN, "category": "xhosa"},
        
        # African names - Sotho
        {"name": "Cyril Ramaphosa", "expected_ethnicity": EthnicityType.AFRICAN, "category": "sotho"},
        {"name": "Julius Malema", "expected_ethnicity": EthnicityType.AFRICAN, "category": "sotho"},
        {"name": "Kgalema Motlanthe", "expected_ethnicity": EthnicityType.AFRICAN, "category": "sotho"},
        {"name": "Thabang Mokoena", "expected_ethnicity": EthnicityType.AFRICAN, "category": "sotho"},
        {"name": "Palesa Mofokeng", "expected_ethnicity": EthnicityType.AFRICAN, "category": "sotho"},
        {"name": "Tshepo Molefe", "expected_ethnicity": EthnicityType.AFRICAN, "category": "sotho"},
        {"name": "Lerato Tsotetsi", "expected_ethnicity": EthnicityType.AFRICAN, "category": "sotho"},
        
        # African names - Tswana
        {"name": "Seretse Khama", "expected_ethnicity": EthnicityType.AFRICAN, "category": "tswana"},
        {"name": "Patrice Motsepe", "expected_ethnicity": EthnicityType.AFRICAN, "category": "tswana"},
        {"name": "Katlego Maboe", "expected_ethnicity": EthnicityType.AFRICAN, "category": "tswana"},
        {"name": "Boitumelo Tlhaping", "expected_ethnicity": EthnicityType.AFRICAN, "category": "tswana"},
        
        # African names - Venda
        {"name": "Frank Ravele", "expected_ethnicity": EthnicityType.AFRICAN, "category": "venda"},
        {"name": "Rudzani Mudau", "expected_ethnicity": EthnicityType.AFRICAN, "category": "venda"},
        
        # Indian names - Tamil (KZN)
        {"name": "Priya Pillay", "expected_ethnicity": EthnicityType.INDIAN, "category": "tamil"},
        {"name": "Rajesh Naidoo", "expected_ethnicity": EthnicityType.INDIAN, "category": "tamil"},
        {"name": "Kavitha Reddy", "expected_ethnicity": EthnicityType.INDIAN, "category": "tamil"},
        {"name": "Ashwin Naicker", "expected_ethnicity": EthnicityType.INDIAN, "category": "tamil"},
        {"name": "Deepa Moodley", "expected_ethnicity": EthnicityType.INDIAN, "category": "tamil"},
        {"name": "Sunil Maharaj", "expected_ethnicity": EthnicityType.INDIAN, "category": "tamil"},
        {"name": "Anita Chetty", "expected_ethnicity": EthnicityType.INDIAN, "category": "tamil"},
        {"name": "Raman Sundaram", "expected_ethnicity": EthnicityType.INDIAN, "category": "tamil"},
        
        # Indian names - Gujarati
        {"name": "Ashish Patel", "expected_ethnicity": EthnicityType.INDIAN, "category": "gujarati"},
        {"name": "Priya Shah", "expected_ethnicity": EthnicityType.INDIAN, "category": "gujarati"},
        {"name": "Kiran Modi", "expected_ethnicity": EthnicityType.INDIAN, "category": "gujarati"},
        {"name": "Nisha Desai", "expected_ethnicity": EthnicityType.INDIAN, "category": "gujarati"},
        
        # Indian names - Hindi/North Indian
        {"name": "Amit Sharma", "expected_ethnicity": EthnicityType.INDIAN, "category": "hindi"},
        {"name": "Priya Gupta", "expected_ethnicity": EthnicityType.INDIAN, "category": "hindi"},
        {"name": "Rajesh Singh", "expected_ethnicity": EthnicityType.INDIAN, "category": "hindi"},
        {"name": "Sunita Kumar", "expected_ethnicity": EthnicityType.INDIAN, "category": "hindi"},
        
        # Cape Malay names
        {"name": "Abdullah Cassiem", "expected_ethnicity": EthnicityType.CAPE_MALAY, "category": "cape_malay"},
        {"name": "Fatima Hendricks", "expected_ethnicity": EthnicityType.CAPE_MALAY, "category": "cape_malay"},
        {"name": "Mohamed Adams", "expected_ethnicity": EthnicityType.CAPE_MALAY, "category": "cape_malay"},
        {"name": "Ayesha Isaacs", "expected_ethnicity": EthnicityType.CAPE_MALAY, "category": "cape_malay"},
        {"name": "Hassan Jacobs", "expected_ethnicity": EthnicityType.CAPE_MALAY, "category": "cape_malay"},
        {"name": "Khadija Khan", "expected_ethnicity": EthnicityType.CAPE_MALAY, "category": "cape_malay"},
        {"name": "Omar Petersen", "expected_ethnicity": EthnicityType.CAPE_MALAY, "category": "cape_malay"},
        {"name": "Zainab Arendse", "expected_ethnicity": EthnicityType.CAPE_MALAY, "category": "cape_malay"},
        
        # Coloured names - Month surnames
        {"name": "John September", "expected_ethnicity": EthnicityType.COLOURED, "category": "month_surname"},
        {"name": "Mary April", "expected_ethnicity": EthnicityType.COLOURED, "category": "month_surname"},
        {"name": "David October", "expected_ethnicity": EthnicityType.COLOURED, "category": "month_surname"},
        {"name": "Sarah January", "expected_ethnicity": EthnicityType.COLOURED, "category": "month_surname"},
        {"name": "Peter August", "expected_ethnicity": EthnicityType.COLOURED, "category": "month_surname"},
        {"name": "Linda December", "expected_ethnicity": EthnicityType.COLOURED, "category": "month_surname"},
        
        # Coloured names - Other
        {"name": "Michael Brown", "expected_ethnicity": EthnicityType.COLOURED, "category": "coloured"},
        {"name": "Sharon Booysen", "expected_ethnicity": EthnicityType.COLOURED, "category": "coloured"},
        {"name": "Trevor Jantjies", "expected_ethnicity": EthnicityType.COLOURED, "category": "coloured"},
        {"name": "Karen Solomons", "expected_ethnicity": EthnicityType.COLOURED, "category": "coloured"},
        
        # White names - Afrikaans
        {"name": "Pieter van der Merwe", "expected_ethnicity": EthnicityType.WHITE, "category": "afrikaans"},
        {"name": "Johannes Botha", "expected_ethnicity": EthnicityType.WHITE, "category": "afrikaans"},
        {"name": "Anna du Plessis", "expected_ethnicity": EthnicityType.WHITE, "category": "afrikaans"},
        {"name": "Francois Steyn", "expected_ethnicity": EthnicityType.WHITE, "category": "afrikaans"},
        {"name": "Maria van Zyl", "expected_ethnicity": EthnicityType.WHITE, "category": "afrikaans"},
        {"name": "Hendrik Fourie", "expected_ethnicity": EthnicityType.WHITE, "category": "afrikaans"},
        {"name": "Susanna Le Roux", "expected_ethnicity": EthnicityType.WHITE, "category": "afrikaans"},
        {"name": "Willem Pretorius", "expected_ethnicity": EthnicityType.WHITE, "category": "afrikaans"},
        
        # White names - English
        {"name": "John Smith", "expected_ethnicity": EthnicityType.WHITE, "category": "english"},
        {"name": "Sarah Johnson", "expected_ethnicity": EthnicityType.WHITE, "category": "english"},
        {"name": "Michael Brown", "expected_ethnicity": EthnicityType.WHITE, "category": "english"},
        {"name": "Emma Wilson", "expected_ethnicity": EthnicityType.WHITE, "category": "english"},
        {"name": "David Taylor", "expected_ethnicity": EthnicityType.WHITE, "category": "english"},
    ]


def get_phonetic_variants_dataset() -> List[Dict[str, Any]]:
    """Get dataset of phonetic variants and misspellings for testing."""
    return [
        # Phonetic variants of African names
        {"name": "Bonganni", "expected_ethnicity": EthnicityType.AFRICAN, "variant_of": "Bongani"},
        {"name": "Thapho", "expected_ethnicity": EthnicityType.AFRICAN, "variant_of": "Thabo"},
        {"name": "Nomza", "expected_ethnicity": EthnicityType.AFRICAN, "variant_of": "Nomsa"},
        {"name": "Cypho", "expected_ethnicity": EthnicityType.AFRICAN, "variant_of": "Sipho"},
        {"name": "Ramafoze", "expected_ethnicity": EthnicityType.AFRICAN, "variant_of": "Ramaphosa"},
        
        # Phonetic variants of Indian names
        {"name": "Pilai", "expected_ethnicity": EthnicityType.INDIAN, "variant_of": "Pillay"},
        {"name": "Reddi", "expected_ethnicity": EthnicityType.INDIAN, "variant_of": "Reddy"},
        {"name": "Naideau", "expected_ethnicity": EthnicityType.INDIAN, "variant_of": "Naidoo"},
        {"name": "Patell", "expected_ethnicity": EthnicityType.INDIAN, "variant_of": "Patel"},
        
        # Phonetic variants of Cape Malay names
        {"name": "Cassim", "expected_ethnicity": EthnicityType.CAPE_MALAY, "variant_of": "Cassiem"},
        {"name": "Hendrix", "expected_ethnicity": EthnicityType.CAPE_MALAY, "variant_of": "Hendricks"},
        {"name": "Abdulla", "expected_ethnicity": EthnicityType.CAPE_MALAY, "variant_of": "Abdullah"},
        
        # Phonetic variants of White names
        {"name": "Boter", "expected_ethnicity": EthnicityType.WHITE, "variant_of": "Botha"},
        {"name": "Smyth", "expected_ethnicity": EthnicityType.WHITE, "variant_of": "Smith"},
        {"name": "Van der Merw", "expected_ethnicity": EthnicityType.WHITE, "variant_of": "Van der Merwe"},
    ]


def get_performance_test_names() -> List[str]:
    """Get names for performance testing."""
    return [
        "Thabo Mthembu",    # African - should hit rules fast
        "Priya Pillay",     # Indian - should hit rules fast  
        "Abdullah Cassiem", # Cape Malay - should hit rules fast
        "John September",   # Coloured month - should hit special heuristic
        "Pieter Botha",     # White - should hit rules fast
        "Unknown Person",   # Should fail rules, try phonetic, fail
    ]


def get_accuracy_metrics_by_ethnicity() -> Dict[EthnicityType, Dict[str, int]]:
    """Get expected accuracy metrics broken down by ethnicity."""
    test_data = get_test_dataset()
    phonetic_data = get_phonetic_variants_dataset()
    
    metrics = {}
    for ethnicity in EthnicityType:
        if ethnicity == EthnicityType.UNKNOWN:
            continue
            
        exact_matches = len([d for d in test_data if d["expected_ethnicity"] == ethnicity])
        phonetic_matches = len([d for d in phonetic_data if d["expected_ethnicity"] == ethnicity])
        
        metrics[ethnicity] = {
            "exact_matches": exact_matches,
            "phonetic_variants": phonetic_matches,
            "total": exact_matches + phonetic_matches
        }
    
    return metrics


def get_expected_performance_targets() -> Dict[str, float]:
    """Get expected performance targets in milliseconds."""
    return {
        "rule_based_avg_ms": 10.0,     # <10ms target
        "phonetic_avg_ms": 50.0,       # <50ms target  
        "full_pipeline_ms": 100.0,     # <100ms target
        "cache_hit_ms": 5.0,           # <5ms for cache hits
    }