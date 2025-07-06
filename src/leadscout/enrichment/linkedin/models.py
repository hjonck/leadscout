"""Data models for LinkedIn research and compliance.

This module defines the data models used for LinkedIn research results,
compliance tracking, and rate limiting following the proven patterns
from the classification system.

Developer B - Classification & Enrichment Specialist
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ResearchMethod(Enum):
    """Method used for LinkedIn research."""
    
    SEARCH_API = "search_api"
    PROFILE_LOOKUP = "profile_lookup"
    COMPANY_LOOKUP = "company_lookup"
    MANUAL_SEARCH = "manual_search"


class ProfileType(Enum):
    """Type of LinkedIn profile."""
    
    INDIVIDUAL = "individual"
    COMPANY = "company"
    UNKNOWN = "unknown"


class ComplianceStatus(Enum):
    """Compliance status for research operations."""
    
    COMPLIANT = "compliant"
    RATE_LIMITED = "rate_limited"
    TOS_VIOLATION = "tos_violation"
    API_ERROR = "api_error"
    BLOCKED = "blocked"


class LinkedInResearchResult(BaseModel):
    """Result from LinkedIn director profile research."""
    
    director_name: str = Field(..., description="Director name searched")
    company_name: str = Field(..., description="Company context")
    
    # Research results
    profile_found: bool = False
    profile_url: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Professional information (business-relevant only)
    current_position: Optional[str] = None
    current_company: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = None
    
    # Network indicators (professional context only)
    connection_count_range: Optional[str] = None  # e.g., "500+", "100-500"
    mutual_connections: Optional[int] = None
    professional_associations: List[str] = Field(default_factory=list)
    
    # Research metadata
    research_method: Optional[ResearchMethod] = None
    processing_time_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Compliance tracking
    compliance_status: ComplianceStatus = ComplianceStatus.COMPLIANT
    rate_limit_remaining: Optional[int] = None
    
    @field_validator("profile_url")
    @classmethod
    def validate_profile_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate LinkedIn profile URL format."""
        if v is None:
            return v
        
        if not v.startswith("https://"):
            v = f"https://{v}"
        
        # Basic LinkedIn URL validation
        if "linkedin.com" not in v:
            raise ValueError("Must be a LinkedIn URL")
        
        return v


class LinkedInCompanyResult(BaseModel):
    """Result from LinkedIn company profile research."""
    
    company_name: str = Field(..., description="Company name searched")
    
    # Company research results
    company_found: bool = False
    company_url: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Company information (public data only)
    company_size: Optional[str] = None  # e.g., "1-10", "11-50", "51-200"
    industry: Optional[str] = None
    headquarters: Optional[str] = None
    founded_year: Optional[int] = None
    company_type: Optional[str] = None  # e.g., "Private", "Public"
    
    # Business indicators
    specialties: List[str] = Field(default_factory=list)
    recent_updates: List[str] = Field(default_factory=list)
    employee_count_estimate: Optional[int] = None
    
    # Research metadata
    research_method: Optional[ResearchMethod] = None
    processing_time_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Compliance tracking
    compliance_status: ComplianceStatus = ComplianceStatus.COMPLIANT
    rate_limit_remaining: Optional[int] = None


class RateLimitTracker(BaseModel):
    """Track rate limiting for compliance."""
    
    window_start: datetime = Field(default_factory=datetime.utcnow)
    window_duration_minutes: int = 60
    max_requests_per_window: int = 100
    current_request_count: int = 0
    
    # Request history for compliance analysis
    recent_requests: List[datetime] = Field(default_factory=list)
    blocked_until: Optional[datetime] = None
    
    def can_make_request(self) -> bool:
        """Check if a request can be made within rate limits."""
        now = datetime.utcnow()
        
        # Check if currently blocked
        if self.blocked_until and now < self.blocked_until:
            return False
        
        # Clean old requests from window
        window_start = now - timedelta(minutes=self.window_duration_minutes)
        self.recent_requests = [
            req for req in self.recent_requests 
            if req > window_start
        ]
        
        # Check if under limit
        return len(self.recent_requests) < self.max_requests_per_window
    
    def record_request(self) -> None:
        """Record a new request for rate limiting."""
        now = datetime.utcnow()
        self.recent_requests.append(now)
        self.current_request_count += 1
    
    def set_blocked(self, duration_minutes: int = 60) -> None:
        """Set blocked status for specified duration."""
        self.blocked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)


class LinkedInComplianceConfig(BaseModel):
    """Configuration for LinkedIn research compliance."""
    
    # Rate limiting settings (conservative)
    requests_per_hour: int = 50  # Very conservative
    requests_per_day: int = 200
    min_delay_between_requests_seconds: float = 5.0
    
    # Compliance settings
    respect_robots_txt: bool = True
    max_search_results: int = 5  # Limit search scope
    timeout_seconds: float = 10.0
    
    # Data collection limitations
    collect_personal_info: bool = False  # Only business-relevant data
    collect_contact_details: bool = False  # Respect privacy
    store_profile_photos: bool = False  # No personal images
    
    # Terms of service compliance
    tos_compliance_mode: str = "strict"  # "strict", "moderate", "basic"
    require_explicit_consent: bool = True
    respect_privacy_settings: bool = True
    
    # Fallback behavior
    graceful_degradation: bool = True  # Continue without LinkedIn data if blocked
    cache_results: bool = True  # Cache to reduce API calls
    cache_duration_hours: int = 24
    
    @field_validator("tos_compliance_mode")
    @classmethod
    def validate_compliance_mode(cls, v: str) -> str:
        """Validate compliance mode setting."""
        valid_modes = {"strict", "moderate", "basic"}
        if v not in valid_modes:
            raise ValueError(f"Compliance mode must be one of: {valid_modes}")
        return v


class LinkedInSearchQuery(BaseModel):
    """Search query for LinkedIn research."""
    
    query_type: str = Field(..., description="Type of search (person, company)")
    search_terms: List[str] = Field(..., description="Search terms")
    filters: Dict[str, Any] = Field(default_factory=dict)
    max_results: int = 5
    
    # Context for relevance scoring
    company_context: Optional[str] = None
    location_context: Optional[str] = None
    industry_context: Optional[str] = None
    
    @field_validator("search_terms")
    @classmethod
    def validate_search_terms(cls, v: List[str]) -> List[str]:
        """Validate search terms are not empty."""
        if not v or not any(term.strip() for term in v):
            raise ValueError("At least one search term is required")
        return [term.strip() for term in v if term.strip()]


class LinkedInResearchStats(BaseModel):
    """Statistics for LinkedIn research performance and compliance."""
    
    total_research_requests: int = 0
    successful_director_searches: int = 0
    successful_company_searches: int = 0
    failed_searches: int = 0
    
    # Compliance metrics
    rate_limit_violations: int = 0
    tos_compliance_score: float = 1.0  # 1.0 = fully compliant
    blocked_periods: int = 0
    
    # Performance metrics
    average_research_time_ms: float = 0.0
    average_confidence_score: float = 0.0
    cache_hit_rate: float = 0.0
    
    # Method breakdown
    api_searches: int = 0
    manual_searches: int = 0
    cached_results: int = 0
    
    # Quality metrics
    high_confidence_results: int = 0  # >0.8 confidence
    medium_confidence_results: int = 0  # 0.5-0.8 confidence
    low_confidence_results: int = 0  # <0.5 confidence
    
    @property
    def success_rate(self) -> float:
        """Calculate overall research success rate."""
        if self.total_research_requests == 0:
            return 0.0
        successful = self.successful_director_searches + self.successful_company_searches
        return successful / self.total_research_requests
    
    @property
    def compliance_risk_level(self) -> str:
        """Assess compliance risk level."""
        if self.tos_compliance_score >= 0.9:
            return "low"
        elif self.tos_compliance_score >= 0.7:
            return "medium"
        else:
            return "high"
    
    def update_with_result(
        self, 
        result: LinkedInResearchResult, 
        from_cache: bool = False
    ) -> None:
        """Update statistics with a new research result."""
        self.total_research_requests += 1
        
        if from_cache:
            self.cached_results += 1
        
        if result.profile_found:
            self.successful_director_searches += 1
        else:
            self.failed_searches += 1
        
        # Update compliance tracking
        if result.compliance_status != ComplianceStatus.COMPLIANT:
            if result.compliance_status == ComplianceStatus.RATE_LIMITED:
                self.rate_limit_violations += 1
            elif result.compliance_status == ComplianceStatus.BLOCKED:
                self.blocked_periods += 1
        
        # Update confidence breakdown
        if result.confidence >= 0.8:
            self.high_confidence_results += 1
        elif result.confidence >= 0.5:
            self.medium_confidence_results += 1
        else:
            self.low_confidence_results += 1
        
        # Update averages
        total = self.total_research_requests
        self.average_confidence_score = (
            (self.average_confidence_score * (total - 1)) + result.confidence
        ) / total
        
        if result.processing_time_ms:
            self.average_research_time_ms = (
                (self.average_research_time_ms * (total - 1)) + result.processing_time_ms
            ) / total
        
        # Update cache hit rate
        self.cache_hit_rate = self.cached_results / total
        
        # Update compliance score based on violations
        if self.rate_limit_violations > 0 or self.blocked_periods > 0:
            violation_rate = (self.rate_limit_violations + self.blocked_periods) / total
            self.tos_compliance_score = max(0.0, 1.0 - violation_rate)


# Update forward references
LinkedInResearchResult.model_rebuild()
LinkedInCompanyResult.model_rebuild()