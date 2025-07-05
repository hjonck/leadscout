"""Name classification module for South African ethnicities.

This module provides a comprehensive multi-layered approach to classifying
South African names by ethnicity using rule-based dictionaries, phonetic
matching, and LLM fallback strategies.

Key Components:
- RuleBasedClassifier: Fast dictionary-based classification (90%+ coverage)
- PhoneticClassifier: Phonetic matching for variant spellings
- LLMClassifier: AI-powered classification for edge cases
- NameClassifier: Main orchestrator that combines all approaches

Architecture:
1. Rule-based classification (95% target coverage, <10ms)
2. Phonetic matching for unknown names (<50ms)
3. LLM classification for remaining cases (<2s)

Usage:
    from leadscout.classification import NameClassifier
    
    classifier = NameClassifier()
    result = await classifier.classify("Bongani Mthembu")
    print(f"{result.name} -> {result.ethnicity.value} ({result.confidence:.2f})")

Integration:
- Uses Developer A's caching system for performance
- Provides classification results for lead scoring
- Supports batch processing for large datasets
"""

from .dictionaries import EthnicityType, NameDictionaries, NameEntry, get_dictionaries
from .exceptions import (
    BatchProcessingError,
    CacheIntegrationError,
    ClassificationError,
    ConfidenceThresholdError,
    DictionaryError,
    LLMClassificationError,
    NameValidationError,
    PhoneticMatchingError,
    RuleClassificationError,
)
from .models import (
    AlternativeClassification,
    BatchClassificationRequest,
    Classification,
    ClassificationCache,
    ClassificationMethod,
    ClassificationRequest,
    ClassificationStats,
    ConfidenceLevel,
    LLMClassificationDetails,
    MultiWordNameAnalysis,
    PhoneticClassificationDetails,
    RuleClassificationDetails,
    ValidationResult,
)
from .classifier import NameClassifier, create_classifier
from .llm import LLMClassifier
from .phonetic import PhoneticClassifier
from .rules import RuleBasedClassifier

# Version and metadata
__version__ = "1.0.0"
__author__ = "LeadScout Development Team"

# Main exports
__all__ = [
    # Core types
    "EthnicityType",
    "Classification",
    "ClassificationMethod",
    "ConfidenceLevel",
    # Main classifier
    "NameClassifier",
    "create_classifier",
    # Component classifiers
    "RuleBasedClassifier",
    "PhoneticClassifier",
    "LLMClassifier",
    # Models
    "ClassificationRequest",
    "BatchClassificationRequest",
    "RuleClassificationDetails",
    "PhoneticClassificationDetails",
    "LLMClassificationDetails",
    "AlternativeClassification",
    "MultiWordNameAnalysis",
    "ValidationResult",
    "ClassificationStats",
    "ClassificationCache",
    # Dictionaries
    "NameDictionaries",
    "NameEntry",
    "get_dictionaries",
    # Exceptions
    "ClassificationError",
    "NameValidationError",
    "DictionaryError",
    "RuleClassificationError",
    "PhoneticMatchingError",
    "LLMClassificationError",
    "CacheIntegrationError",
    "BatchProcessingError",
    "ConfidenceThresholdError",
]

# Module-level configuration
DEFAULT_CONFIDENCE_THRESHOLD = 0.70
HIGH_CONFIDENCE_THRESHOLD = 0.85
VERY_HIGH_CONFIDENCE_THRESHOLD = 0.95

# Performance targets (from requirements)
TARGET_RULE_CLASSIFICATION_MS = 10
TARGET_PHONETIC_CLASSIFICATION_MS = 50
TARGET_LLM_CLASSIFICATION_MS = 2000
TARGET_CACHE_HIT_RATE = 0.80
TARGET_LLM_USAGE_RATE = 0.05  # <5% of classifications should use LLM

# Ethnicity priority order for multi-word names (least European first)
ETHNICITY_PRIORITY = [
    EthnicityType.AFRICAN,
    EthnicityType.INDIAN,
    EthnicityType.CAPE_MALAY,
    EthnicityType.COLOURED,
    EthnicityType.WHITE,
    EthnicityType.UNKNOWN,
]


def get_classification_info() -> dict:
    """Get information about the classification module."""
    dictionaries = get_dictionaries()
    coverage = dictionaries.get_ethnicity_coverage()

    return {
        "version": __version__,
        "total_names_in_dictionaries": sum(coverage.values()),
        "ethnicity_coverage": coverage,
        "performance_targets": {
            "rule_classification_ms": TARGET_RULE_CLASSIFICATION_MS,
            "phonetic_classification_ms": TARGET_PHONETIC_CLASSIFICATION_MS,
            "llm_classification_ms": TARGET_LLM_CLASSIFICATION_MS,
            "cache_hit_rate": TARGET_CACHE_HIT_RATE,
            "llm_usage_rate": TARGET_LLM_USAGE_RATE,
        },
        "supported_ethnicities": [e.value for e in EthnicityType],
        "classification_methods": [m.value for m in ClassificationMethod],
    }
