"""Enhanced contact validation leveraging classification system patterns.

Provides comprehensive contact quality assessment and validation
using proven async patterns and confidence scoring approaches.

Developer B - Classification & Enrichment Specialist
"""

from .contact_validator import ContactValidator
from .models import (
    ContactValidationResult,
    ContactQualityScore,
    EnhancedContactData,
    ContactValidationConfig,
    ContactValidationStats,
    ValidationMethod,
    ContactType,
    EmailValidationResult,
    PhoneValidationResult,
    AddressValidationResult,
)

__all__ = [
    "ContactValidator",
    "ContactValidationResult",
    "ContactQualityScore", 
    "EnhancedContactData",
    "ContactValidationConfig",
    "ContactValidationStats",
    "ValidationMethod",
    "ContactType",
    "EmailValidationResult",
    "PhoneValidationResult", 
    "AddressValidationResult",
]