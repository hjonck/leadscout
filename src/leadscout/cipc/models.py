"""CIPC data models for South African company registry integration.

This module defines Pydantic models for representing CIPC company data,
personal names extracted from company names, search requests/responses,
and related data structures used throughout the CIPC integration system.

Key Models:
- CIPCCompany: Complete company registry record
- PersonalName: Extracted personal name with metadata
- CompanySearchRequest/Response: Search API contracts
- CompanyMatch: Individual search result with scoring
- CIPCDownloadBatch: Metadata for CSV download batches

Architecture:
All models use Pydantic for validation, serialization, and type safety.
Models integrate with the existing classification system and provide
clean APIs for Developer B integration.

Usage:
    from leadscout.cipc.models import CIPCCompany, CompanySearchRequest
    
    company = CIPCCompany(
        registration_number="2021/123456/07",
        company_name="ABC Trading CC",
        company_type="Close Corporation"
    )
"""

import re
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class CompanyType(str, Enum):
    """CIPC company type classifications."""

    PRIVATE_COMPANY = "Private Company"
    PUBLIC_COMPANY = "Public Company"
    CLOSE_CORPORATION = "Close Corporation"
    SECTION_21 = "Section 21"
    PARTNERSHIP = "Partnership"
    SOLE_PROPRIETORSHIP = "Sole Proprietorship"
    TRUST = "Trust"
    COOPERATIVE = "Cooperative"
    EXTERNAL_COMPANY = "External Company"
    BRANCH = "Branch"
    OTHER = "Other"


class CompanyStatus(str, Enum):
    """CIPC company status classifications."""

    ACTIVE = "Active"
    IN_BUSINESS = "In Business"
    DORMANT = "Dormant"
    DEREGISTERED = "Deregistered"
    LIQUIDATED = "Liquidated"
    UNDER_LIQUIDATION = "Under Liquidation"
    UNKNOWN = "Unknown"


class CIPCCompany(BaseModel):
    """South African company registry record from CIPC data.

    Represents a complete company record from the CIPC CSV downloads,
    including extracted personal names and processed metadata for
    search and classification purposes.

    Attributes:
        registration_number: Official CIPC registration number
        company_name: Full registered company name
        company_type: Type of business entity
        company_status: Current registration status
        extracted_names: Personal names found in company name
        province: Inferred province location
        industry_keywords: Business type keywords
        download_batch: Date of CSV batch this record came from
        file_source: Which letter file (A-Z) contained this record
        name_slug: Normalized name for search operations
        confidence_score: Confidence in data extraction (0-1)
        created_at: Record creation timestamp
        last_updated: Last modification timestamp
    """

    # Core CIPC fields
    registration_number: str = Field(
        ...,
        min_length=5,
        max_length=20,
        description="Official CIPC registration number",
    )
    company_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Full registered company name",
    )
    company_type: CompanyType = Field(
        CompanyType.OTHER, description="Type of business entity"
    )
    company_status: CompanyStatus = Field(
        CompanyStatus.UNKNOWN, description="Current registration status"
    )

    # Extracted and processed data
    extracted_names: List["PersonalName"] = Field(
        default_factory=list,
        description="Personal names extracted from company name",
    )
    province: Optional[str] = Field(
        None, max_length=50, description="Inferred province location"
    )
    industry_keywords: List[str] = Field(
        default_factory=list, description="Industry classification keywords"
    )

    # Processing metadata
    download_batch: date = Field(
        ..., description="Date of CSV batch this record came from"
    )
    file_source: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Letter file (A-Z) that contained this record",
    )
    name_slug: str = Field(
        ..., description="Normalized name for search operations"
    )
    confidence_score: float = Field(
        1.0, ge=0, le=1, description="Confidence in data extraction accuracy"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Record creation timestamp",
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last modification timestamp",
    )

    @validator("registration_number")
    def validate_registration_number(cls, v: str) -> str:
        """Validate South African company registration number format."""
        if not v or not v.strip():
            raise ValueError("Registration number is required")

        reg_num = v.strip().upper()

        # Basic format validation - YYYY/NNNNNN/NN
        sa_reg_pattern = r"^\d{4}/\d{6}/\d{2}$"
        if re.match(sa_reg_pattern, reg_num):
            return reg_num

        # Allow other formats but flag for review
        if len(reg_num) < 5:
            raise ValueError("Registration number too short")

        return reg_num

    @validator("company_name")
    def validate_company_name(cls, v: str) -> str:
        """Validate and clean company name."""
        if not v or not v.strip():
            raise ValueError("Company name is required")

        # Clean up whitespace and normalize
        cleaned = " ".join(v.strip().split())

        # Check for suspicious characters
        if any(char in cleaned for char in ["|", "\t", "\n", "\r"]):
            raise ValueError("Company name contains invalid characters")

        # Convert to title case for consistency
        return cleaned.title()

    @validator("name_slug", pre=False, always=True)
    def generate_name_slug(cls, v: str, values: dict) -> str:
        """Generate normalized slug from company name."""
        if v:  # If slug is already provided, use it
            return v

        company_name = values.get("company_name", "")
        if not company_name:
            return ""

        # Normalize for search: lowercase, remove special chars, collapse spaces
        slug = re.sub(r"[^\w\s]", "", company_name.lower())
        slug = re.sub(r"\s+", " ", slug).strip()
        return slug

    @validator("file_source")
    def validate_file_source(cls, v: str) -> str:
        """Validate file source format."""
        if not v or not v.strip():
            raise ValueError("File source is required")

        source = v.strip().upper()

        # Should be single letter A-Z or letter with number
        if not re.match(r"^[A-Z](\d+)?$", source):
            raise ValueError("Invalid file source format")

        return source

    def get_display_name(self) -> str:
        """Get formatted display name for UI.

        Returns:
            Formatted company name with type suffix
        """
        if self.company_type == CompanyType.OTHER:
            return self.company_name
        return f"{self.company_name} ({self.company_type.value})"

    def get_personal_names_count(self) -> int:
        """Get count of extracted personal names.

        Returns:
            Number of personal names found in company name
        """
        return len(self.extracted_names)

    def is_active(self) -> bool:
        """Check if company is currently active.

        Returns:
            True if company status indicates active business
        """
        return self.company_status in {
            CompanyStatus.ACTIVE,
            CompanyStatus.IN_BUSINESS,
        }

    def to_search_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for search indexing.

        Returns:
            Dictionary optimized for search operations
        """
        return {
            "registration_number": self.registration_number,
            "company_name": self.company_name,
            "name_slug": self.name_slug,
            "company_type": self.company_type.value,
            "company_status": self.company_status.value,
            "province": self.province,
            "industry_keywords": self.industry_keywords,
            "extracted_names": [name.name for name in self.extracted_names],
            "is_active": self.is_active(),
            "download_batch": self.download_batch.isoformat(),
        }


class PersonalName(BaseModel):
    """Personal name extracted from CIPC company name.

    Represents an individual personal name found within a company name,
    along with extraction metadata and confidence scoring for integration
    with the name classification system.

    Attributes:
        name: The extracted personal name
        phonetic_key: Metaphone/Soundex key for matching
        position: Position within company name (0-indexed)
        extraction_method: Method used to extract name
        confidence: Confidence in extraction accuracy (0-1)
        context: Surrounding text context
        company_registration: Source company registration number
    """

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Extracted personal name",
    )
    phonetic_key: str = Field(
        ..., description="Metaphone/Soundex key for matching"
    )
    position: int = Field(
        ..., ge=0, description="Position within company name (0-indexed)"
    )
    extraction_method: str = Field(
        ..., description="Method used to extract name"
    )
    confidence: float = Field(
        ..., ge=0, le=1, description="Confidence in extraction accuracy"
    )
    context: str = Field(
        ..., max_length=255, description="Surrounding text context"
    )
    company_registration: str = Field(
        ..., description="Source company registration number"
    )

    @validator("name")
    def validate_name(cls, v: str) -> str:
        """Validate and clean personal name."""
        if not v or not v.strip():
            raise ValueError("Name is required")

        # Clean and normalize
        cleaned = " ".join(v.strip().split())

        # Basic name validation - should contain only letters, spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-Z\s'-]+$", cleaned):
            raise ValueError("Name contains invalid characters")

        # Convert to title case
        return cleaned.title()

    @validator("extraction_method")
    def validate_extraction_method(cls, v: str) -> str:
        """Validate extraction method."""
        valid_methods = {
            "regex_pattern",
            "tokenization",
            "capitalization",
            "known_surnames",
            "name_dictionary",
            "manual",
        }
        if v not in valid_methods:
            raise ValueError(
                f"Invalid extraction method. Must be one of: {valid_methods}"
            )
        return v

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if extraction meets high confidence threshold.

        Args:
            threshold: Minimum confidence level

        Returns:
            True if confidence meets or exceeds threshold
        """
        return self.confidence >= threshold


class SearchFilters(BaseModel):
    """Filters for company search operations.

    Defines filtering criteria for company searches including geographic,
    business type, and status filters to narrow search results.
    """

    province: Optional[str] = Field(None, description="Filter by province")
    company_type: Optional[CompanyType] = Field(
        None, description="Filter by company type"
    )
    company_status: Optional[CompanyStatus] = Field(
        None, description="Filter by company status"
    )
    active_only: bool = Field(
        True, description="Include only active companies"
    )
    min_confidence: float = Field(
        0.0, ge=0, le=1, description="Minimum extraction confidence"
    )
    has_personal_names: Optional[bool] = Field(
        None, description="Filter by presence of personal names"
    )
    download_batch_from: Optional[date] = Field(
        None, description="Minimum download batch date"
    )
    download_batch_to: Optional[date] = Field(
        None, description="Maximum download batch date"
    )


class CompanyMatch(BaseModel):
    """Individual company search result with scoring.

    Represents a single matching company from search results with
    similarity scoring and match metadata for ranking and filtering.
    """

    company: CIPCCompany = Field(..., description="Matched company record")
    similarity_score: float = Field(
        ..., ge=0, le=1, description="Similarity to search query"
    )
    match_type: str = Field(
        ..., description="Type of match (exact, fuzzy, partial)"
    )
    match_fields: List[str] = Field(
        ..., description="Fields that contributed to match"
    )
    rank: int = Field(..., ge=1, description="Rank in search results")

    @validator("match_type")
    def validate_match_type(cls, v: str) -> str:
        """Validate match type."""
        valid_types = {"exact", "fuzzy", "partial", "phonetic", "substring"}
        if v not in valid_types:
            raise ValueError(
                f"Invalid match type. Must be one of: {valid_types}"
            )
        return v

    def is_high_quality_match(self, threshold: float = 0.8) -> bool:
        """Check if match meets high quality threshold.

        Args:
            threshold: Minimum similarity score

        Returns:
            True if match is high quality
        """
        return (
            self.similarity_score >= threshold
            and self.company.is_active()
            and self.match_type in {"exact", "fuzzy"}
        )


class CompanySearchRequest(BaseModel):
    """Request model for company search operations.

    Defines the parameters for company search queries including the
    search query, filters, pagination, and result formatting options.
    """

    query: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Company name search query",
    )
    filters: SearchFilters = Field(
        default_factory=lambda: SearchFilters(
            province=None,
            company_type=None,
            company_status=None,
            active_only=True,
            min_confidence=0.0,
            has_personal_names=None,
            download_batch_from=None,
            download_batch_to=None,
        ),
        description="Search filters",
    )
    exact_match: bool = Field(False, description="Require exact name match")
    fuzzy_threshold: float = Field(
        0.6, ge=0, le=1, description="Minimum fuzzy match score"
    )
    max_results: int = Field(
        20, ge=1, le=100, description="Maximum number of results"
    )
    include_inactive: bool = Field(
        False, description="Include inactive companies"
    )
    sort_by: str = Field("relevance", description="Sort order for results")

    @validator("query")
    def validate_query(cls, v: str) -> str:
        """Validate and clean search query."""
        if not v or not v.strip():
            raise ValueError("Search query is required")

        # Clean and normalize
        cleaned = " ".join(v.strip().split())

        # Remove potentially problematic characters for search
        cleaned = re.sub(r'[|<>"]', "", cleaned)

        return cleaned

    @validator("sort_by")
    def validate_sort_by(cls, v: str) -> str:
        """Validate sort criteria."""
        valid_sorts = {"relevance", "name", "registration_date", "status"}
        if v not in valid_sorts:
            raise ValueError(
                f"Invalid sort criteria. Must be one of: {valid_sorts}"
            )
        return v


class CompanySearchResponse(BaseModel):
    """Response model for company search operations.

    Contains search results with metadata about the query execution
    including performance metrics and result summary information.
    """

    query: str = Field(..., description="Original search query")
    matches: List[CompanyMatch] = Field(..., description="Matching companies")
    total_results: int = Field(
        ..., ge=0, description="Total number of matches found"
    )
    returned_results: int = Field(
        ..., ge=0, description="Number of results returned"
    )
    search_time_ms: int = Field(..., ge=0, description="Search execution time")
    filters_applied: SearchFilters = Field(
        ..., description="Filters that were applied"
    )
    has_more_results: bool = Field(
        False, description="Whether more results are available"
    )

    @validator("returned_results", pre=False, always=True)
    def validate_returned_results(cls, v: int, values: dict) -> int:
        """Ensure returned results matches actual matches count."""
        matches = values.get("matches", [])
        return len(matches)


class CIPCDownloadBatch(BaseModel):
    """Metadata for CIPC CSV download batch.

    Tracks information about monthly CSV download batches including
    download statistics, processing status, and error information.
    """

    year: int = Field(..., ge=2000, le=3000, description="Download year")
    month: int = Field(..., ge=1, le=12, description="Download month")
    download_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="When download was performed",
    )
    files_downloaded: int = Field(
        0, ge=0, le=26, description="Number of CSV files downloaded"
    )
    total_companies: int = Field(
        0, ge=0, description="Total companies processed"
    )
    total_names_extracted: int = Field(
        0, ge=0, description="Total personal names extracted"
    )
    processing_time_minutes: int = Field(
        0, ge=0, description="Total processing time"
    )
    status: str = Field("pending", description="Batch processing status")
    error_count: int = Field(
        0, ge=0, description="Number of errors encountered"
    )
    error_details: List[str] = Field(
        default_factory=list, description="Detailed error messages"
    )

    @validator("status")
    def validate_status(cls, v: str) -> str:
        """Validate batch status."""
        valid_statuses = {
            "pending",
            "downloading",
            "processing",
            "completed",
            "failed",
        }
        if v not in valid_statuses:
            raise ValueError(
                f"Invalid status. Must be one of: {valid_statuses}"
            )
        return v

    def get_batch_identifier(self) -> str:
        """Get unique identifier for this batch.

        Returns:
            String identifier in format YYYY-MM
        """
        return f"{self.year:04d}-{self.month:02d}"

    def add_error(self, error_message: str) -> None:
        """Add an error to the batch processing log.

        Args:
            error_message: Description of the error
        """
        self.error_details.append(error_message)
        self.error_count = len(self.error_details)


class CIPCProcessingStats(BaseModel):
    """Statistics for CIPC processing performance.

    Tracks processing performance metrics for monitoring and optimization
    of the CIPC integration system.
    """

    total_companies_processed: int = Field(
        0, ge=0, description="Total companies processed"
    )
    total_names_extracted: int = Field(
        0, ge=0, description="Total personal names extracted"
    )
    successful_downloads: int = Field(
        0, ge=0, description="Successful CSV downloads"
    )
    failed_downloads: int = Field(0, ge=0, description="Failed CSV downloads")
    average_processing_time_ms: float = Field(
        0.0, ge=0, description="Average processing time per company"
    )
    extraction_accuracy_rate: float = Field(
        0.0, ge=0, le=1, description="Name extraction accuracy rate"
    )
    cache_hit_rate: float = Field(
        0.0, ge=0, le=1, description="Cache hit rate for searches"
    )
    last_batch_date: Optional[date] = Field(
        None, description="Date of last processed batch"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Statistics update timestamp",
    )

    def get_download_success_rate(self) -> float:
        """Calculate download success rate percentage.

        Returns:
            Success rate as percentage (0-100)
        """
        total_downloads = self.successful_downloads + self.failed_downloads
        if total_downloads == 0:
            return 0.0
        return (self.successful_downloads / total_downloads) * 100

    def get_names_per_company_ratio(self) -> float:
        """Calculate average number of names extracted per company.

        Returns:
            Average names per company
        """
        if self.total_companies_processed == 0:
            return 0.0
        return self.total_names_extracted / self.total_companies_processed


# Update forward references for Pydantic models
CIPCCompany.model_rebuild()
