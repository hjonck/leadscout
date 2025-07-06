"""LinkedIn research system for director and company profile discovery.

Provides compliant research capabilities for professional information
with careful attention to terms of service and rate limiting.

Developer B - Classification & Enrichment Specialist
"""

from .linkedin_researcher import LinkedInResearcher
from .models import (
    LinkedInResearchResult,
    LinkedInCompanyResult,
    LinkedInComplianceConfig,
    ResearchMethod,
    ProfileType,
)

__all__ = [
    "LinkedInResearcher",
    "LinkedInResearchResult",
    "LinkedInCompanyResult", 
    "LinkedInComplianceConfig",
    "ResearchMethod",
    "ProfileType",
]