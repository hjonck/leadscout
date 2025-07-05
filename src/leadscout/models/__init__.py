"""LeadScout data models.

This module contains all data models used throughout the LeadScout system.
All models use Pydantic for validation and type safety.
"""

from .lead import Lead, EnrichedLead
from .classification import Classification, EthnicityType
from .contact import ContactInfo, ContactValidation

__all__ = [
    "Lead",
    "EnrichedLead", 
    "Classification",
    "EthnicityType",
    "ContactInfo",
    "ContactValidation",
]