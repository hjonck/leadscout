"""Custom exceptions for LeadScout.

This module defines the exception hierarchy for the LeadScout system,
following the coding standards for proper error handling.
"""

from typing import Any, Dict, Optional


class LeadScoutError(Exception):
    """Base exception for all LeadScout errors.

    All custom exceptions in the LeadScout system should inherit from
    this base class to maintain a consistent exception hierarchy.

    Attributes:
        message: Human-readable error message
        context: Additional context information (optional)
    """

    def __init__(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(
                f"{k}={v}" for k, v in self.context.items()
            )
            return f"{self.message} ({context_str})"
        return self.message


class ConfigurationError(LeadScoutError):
    """Configuration-related errors.

    Raised when there are issues with application configuration,
    missing required settings, or invalid configuration values.
    """


class ValidationError(LeadScoutError):
    """Data validation errors.

    Raised when input data fails validation checks, such as
    invalid lead data format or malformed input files.
    """


class APIError(LeadScoutError):
    """API-related errors.

    Raised when external API calls fail, including network issues,
    authentication failures, or service unavailability.

    Attributes:
        status_code: HTTP status code (if applicable)
        retry_after: Suggested retry delay in seconds (if provided by API)
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        retry_after: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, context)
        self.status_code = status_code
        self.retry_after = retry_after


class CacheError(LeadScoutError):
    """Cache system errors.

    Raised when there are issues with the cache system, such as
    database connection failures or cache corruption.
    """


class ClassificationError(LeadScoutError):
    """Name classification errors.

    Raised when name classification fails due to algorithm errors
    or insufficient data for classification.
    """


class EnrichmentError(LeadScoutError):
    """Lead enrichment errors.

    Raised when lead enrichment processes fail, such as data source
    unavailability or enrichment pipeline failures.
    """


class FileProcessingError(LeadScoutError):
    """File processing errors.

    Raised when there are issues reading or writing Excel files,
    such as file corruption or permission issues.
    """


class RateLimitError(APIError):
    """API rate limit exceeded.

    Raised when API rate limits are exceeded and requests need
    to be throttled or retried.
    """

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message, status_code=429, retry_after=retry_after, context=context
        )


class AuthenticationError(APIError):
    """API authentication errors.

    Raised when API authentication fails due to invalid or
    missing API keys.
    """

    def __init__(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, status_code=401, context=context)
