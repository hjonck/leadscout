"""CIPC (Companies and Intellectual Property Commission) integration module.

This module handles integration with South African company registry data,
including CSV downloads, company name parsing, search functionality, and
data caching for the LeadScout lead enrichment system.

Key Components:
- CIPCDownloader: Automated monthly CSV download management
- NameExtractor: Personal name extraction from company names  
- CompanySearchEngine: Fuzzy matching and company lookup
- CIPCModels: Data models for company registry information

Architecture:
The CIPC module follows an async-first design with multi-tier caching
and robust error handling. It processes monthly CSV downloads containing
up to 2M+ South African company records and extracts personal names for
ethnicity classification by Developer B.

Integration Points:
- Provides company search APIs to enrichment pipeline
- Supplies extracted names to classification system
- Caches results via PostgreSQL and Redis layers
- Integrates with overall lead scoring system

Performance Targets:
- Company search: <200ms average response time
- CSV processing: Complete 26-file batch within 30 minutes
- Name extraction: >95% accuracy for SA naming patterns
- Cache hit rate: >80% for repeated company lookups

Usage:
    from leadscout.cipc import CIPCDownloader, CompanySearchEngine
    
    # Download latest CIPC data
    downloader = CIPCDownloader()
    await downloader.download_monthly_batch(2025, 1)
    
    # Search for companies
    search_engine = CompanySearchEngine()
    results = await search_engine.search_companies("ABC Trading CC")
"""

from .exceptions import (
    CIPCDownloadError,
    CIPCError,
    CIPCParsingError,
    CIPCSearchError,
    CIPCValidationError,
)
from .models import (
    CIPCCompany,
    CIPCDownloadBatch,
    CIPCProcessingStats,
    CompanyMatch,
    CompanySearchRequest,
    CompanySearchResponse,
    PersonalName,
    SearchFilters,
)

__all__ = [
    # Models
    "CIPCCompany",
    "PersonalName",
    "CompanySearchRequest",
    "CompanySearchResponse",
    "CompanyMatch",
    "CIPCDownloadBatch",
    "SearchFilters",
    "CIPCProcessingStats",
    # Exceptions
    "CIPCError",
    "CIPCDownloadError",
    "CIPCParsingError",
    "CIPCSearchError",
    "CIPCValidationError",
]
