"""Classification-specific exceptions.

This module defines custom exceptions for the name classification system,
providing specific error types for different failure modes and integration
issues. Follows the custom exception hierarchy from core.exceptions.

Key Features:
- Specific exception types for each classification method
- Integration-specific exceptions for cache and API failures
- Validation exceptions for malformed input data
- Cost and rate limiting exceptions for LLM usage
- Clear error messages for debugging and user feedback

Architecture Decision: Uses hierarchical exception structure with specific
exception types for different failure modes to enable proper error handling
and retry logic throughout the classification pipeline.

Integration: Inherits from core LeadScout exceptions to maintain consistency
across the entire application.
"""

from typing import Optional, List, Dict, Any


class ClassificationError(Exception):
    """Base exception for classification system errors."""
    
    def __init__(
        self, 
        message: str, 
        name: Optional[str] = None,
        method: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.name = name
        self.method = method
        self.details = details or {}


class NameValidationError(ClassificationError):
    """Exception raised when name validation fails."""
    
    def __init__(
        self, 
        message: str, 
        name: str,
        validation_errors: List[str],
        suggested_corrections: Optional[List[str]] = None
    ):
        super().__init__(message, name=name)
        self.validation_errors = validation_errors
        self.suggested_corrections = suggested_corrections or []


class DictionaryError(ClassificationError):
    """Exception raised when dictionary operations fail."""
    
    def __init__(
        self, 
        message: str, 
        dictionary_type: Optional[str] = None,
        missing_files: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.dictionary_type = dictionary_type
        self.missing_files = missing_files or []


class RuleClassificationError(ClassificationError):
    """Exception raised during rule-based classification."""
    
    def __init__(
        self, 
        message: str, 
        name: str,
        conflicting_matches: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(message, name=name, method="rule_based")
        self.conflicting_matches = conflicting_matches or []


class PhoneticMatchingError(ClassificationError):
    """Exception raised during phonetic matching."""
    
    def __init__(
        self, 
        message: str, 
        name: str,
        failed_algorithms: Optional[List[str]] = None,
        partial_results: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, name=name, method="phonetic")
        self.failed_algorithms = failed_algorithms or []
        self.partial_results = partial_results or {}


class LLMClassificationError(ClassificationError):
    """Exception raised during LLM classification."""
    
    def __init__(
        self, 
        message: str, 
        name: Optional[str] = None,
        model: Optional[str] = None,
        api_response: Optional[str] = None,
        retry_count: int = 0
    ):
        super().__init__(message, name=name, method="llm")
        self.model = model
        self.api_response = api_response
        self.retry_count = retry_count


class LLMRateLimitError(LLMClassificationError):
    """Exception raised when LLM API rate limits are exceeded."""
    
    def __init__(
        self, 
        message: str, 
        retry_after_seconds: Optional[int] = None,
        daily_limit_exceeded: bool = False
    ):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds
        self.daily_limit_exceeded = daily_limit_exceeded


class LLMCostLimitError(LLMClassificationError):
    """Exception raised when LLM usage exceeds cost limits."""
    
    def __init__(
        self, 
        message: str, 
        current_cost: float,
        cost_limit: float,
        tokens_used: int
    ):
        super().__init__(message)
        self.current_cost = current_cost
        self.cost_limit = cost_limit
        self.tokens_used = tokens_used


class CacheIntegrationError(ClassificationError):
    """Exception raised when cache integration fails."""
    
    def __init__(
        self, 
        message: str, 
        cache_operation: str,
        name: Optional[str] = None,
        cache_details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, name=name)
        self.cache_operation = cache_operation
        self.cache_details = cache_details or {}


class BatchProcessingError(ClassificationError):
    """Exception raised during batch processing operations."""
    
    def __init__(
        self, 
        message: str, 
        batch_size: int,
        processed_count: int,
        failed_names: List[str],
        partial_results: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(message)
        self.batch_size = batch_size
        self.processed_count = processed_count
        self.failed_names = failed_names
        self.partial_results = partial_results or []


class ConfidenceThresholdError(ClassificationError):
    """Exception raised when classification confidence is below required threshold."""
    
    def __init__(
        self, 
        message: str, 
        name: str,
        achieved_confidence: float,
        required_confidence: float,
        method: str
    ):
        super().__init__(message, name=name, method=method)
        self.achieved_confidence = achieved_confidence
        self.required_confidence = required_confidence


class AugmentedRetrievalError(ClassificationError):
    """Exception raised when augmented retrieval for few-shot learning fails."""
    
    def __init__(
        self, 
        message: str, 
        name: str,
        search_method: str,
        examples_found: int,
        minimum_required: int
    ):
        super().__init__(message, name=name)
        self.search_method = search_method
        self.examples_found = examples_found
        self.minimum_required = minimum_required


class MultiWordAnalysisError(ClassificationError):
    """Exception raised during multi-word name analysis."""
    
    def __init__(
        self, 
        message: str, 
        name: str,
        name_parts: List[str],
        individual_errors: List[str]
    ):
        super().__init__(message, name=name)
        self.name_parts = name_parts
        self.individual_errors = individual_errors


class EthnicityMappingError(ClassificationError):
    """Exception raised when ethnicity mapping or conversion fails."""
    
    def __init__(
        self, 
        message: str, 
        source_ethnicity: str,
        target_system: str,
        available_mappings: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.source_ethnicity = source_ethnicity
        self.target_system = target_system
        self.available_mappings = available_mappings or []


class ConfigurationError(ClassificationError):
    """Exception raised when classification system configuration is invalid."""
    
    def __init__(
        self, 
        message: str, 
        config_section: str,
        invalid_values: Optional[Dict[str, str]] = None
    ):
        super().__init__(message)
        self.config_section = config_section
        self.invalid_values = invalid_values or {}


class PerformanceError(ClassificationError):
    """Exception raised when performance targets are not met."""
    
    def __init__(
        self, 
        message: str, 
        operation: str,
        actual_time_ms: float,
        target_time_ms: float,
        performance_impact: str
    ):
        super().__init__(message)
        self.operation = operation
        self.actual_time_ms = actual_time_ms
        self.target_time_ms = target_time_ms
        self.performance_impact = performance_impact


# Convenience functions for common error scenarios

def raise_invalid_name(name: str, reason: str) -> None:
    """Raise NameValidationError for invalid names."""
    raise NameValidationError(
        f"Invalid name '{name}': {reason}",
        name=name,
        validation_errors=[reason]
    )


def raise_cache_miss(name: str, cache_operation: str) -> None:
    """Raise CacheIntegrationError for cache misses when cache is required."""
    raise CacheIntegrationError(
        f"Cache miss for name '{name}' during {cache_operation}",
        cache_operation=cache_operation,
        name=name
    )


def raise_low_confidence(
    name: str, 
    method: str, 
    confidence: float, 
    threshold: float
) -> None:
    """Raise ConfidenceThresholdError for low confidence results."""
    raise ConfidenceThresholdError(
        f"Classification confidence {confidence:.2f} below threshold {threshold:.2f} for '{name}' using {method}",
        name=name,
        achieved_confidence=confidence,
        required_confidence=threshold,
        method=method
    )


def raise_llm_failure(
    name: str, 
    model: str, 
    error_details: str,
    retry_count: int = 0
) -> None:
    """Raise LLMClassificationError for LLM API failures."""
    raise LLMClassificationError(
        f"LLM classification failed for '{name}' using {model}: {error_details}",
        name=name,
        model=model,
        api_response=error_details,
        retry_count=retry_count
    )


def raise_phonetic_failure(
    name: str, 
    algorithms: List[str], 
    error_details: str
) -> None:
    """Raise PhoneticMatchingError for phonetic algorithm failures."""
    raise PhoneticMatchingError(
        f"Phonetic matching failed for '{name}': {error_details}",
        name=name,
        failed_algorithms=algorithms
    )