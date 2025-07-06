"""Data models for website discovery and validation.

This module defines the data models used for website discovery results,
validation scores, and discovery strategies following the proven patterns
from the classification system.

Developer B - Classification & Enrichment Specialist
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class DiscoveryMethod(Enum):
    """Method used for website discovery."""
    
    DOMAIN_PATTERN = "domain_pattern"
    SEARCH_ENGINE = "search_engine"
    EMAIL_DOMAIN = "email_domain"
    MANUAL = "manual"


class WebsiteStatus(Enum):
    """Website validation status."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    REDIRECT = "redirect"
    SSL_ERROR = "ssl_error"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"


class WebsiteDiscoveryResult(BaseModel):
    """Result from website discovery process."""
    
    company_name: str = Field(..., description="Company name searched")
    discovered_url: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    discovery_method: Optional[DiscoveryMethod] = None
    
    # Discovery details
    alternative_urls: List[str] = Field(default_factory=list)
    search_queries_used: List[str] = Field(default_factory=list)
    processing_time_ms: Optional[float] = None
    
    # Validation results
    validation_result: Optional["WebsiteValidationResult"] = None
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator("discovered_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL format if provided."""
        if v is None:
            return v
        
        # Basic URL validation
        if not v.startswith(("http://", "https://")):
            v = f"https://{v}"
        
        return v.lower().strip()


class WebsiteValidationResult(BaseModel):
    """Result from website validation process."""
    
    url: str = Field(..., description="URL that was validated")
    status: WebsiteStatus = Field(..., description="Website status")
    response_time_ms: Optional[float] = None
    ssl_valid: bool = False
    
    # Content analysis
    business_relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    has_contact_info: bool = False
    professional_appearance: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Technical details
    status_code: Optional[int] = None
    redirect_url: Optional[str] = None
    error_message: Optional[str] = None
    
    # Content indicators
    company_name_matches: bool = False
    has_business_content: bool = False
    has_commerce_indicators: bool = False
    
    @property
    def overall_quality_score(self) -> float:
        """Calculate overall website quality score."""
        if self.status != WebsiteStatus.ACTIVE:
            return 0.0
        
        # Weight different factors
        weights = {
            "business_relevance": 0.4,
            "professional_appearance": 0.3,
            "ssl_valid": 0.2,
            "response_time": 0.1
        }
        
        score = 0.0
        score += self.business_relevance_score * weights["business_relevance"]
        score += self.professional_appearance * weights["professional_appearance"]
        score += (1.0 if self.ssl_valid else 0.0) * weights["ssl_valid"]
        
        # Response time scoring (under 2s = 1.0, over 5s = 0.0)
        if self.response_time_ms:
            response_score = max(0.0, 1.0 - (self.response_time_ms - 2000) / 3000)
            score += response_score * weights["response_time"]
        
        return min(1.0, score)


class DomainPattern(BaseModel):
    """Domain pattern for systematic website discovery."""
    
    pattern: str = Field(..., description="Domain pattern template")
    priority: int = Field(default=1, description="Search priority")
    country_code: str = Field(default="za", description="Country code for domains")
    
    def generate_url(self, company_name: str) -> str:
        """Generate URL from pattern and company name."""
        # Normalize company name for URL
        normalized = company_name.lower()
        normalized = normalized.replace(" ", "").replace("-", "").replace("_", "")
        normalized = "".join(c for c in normalized if c.isalnum())
        
        return self.pattern.format(
            company=normalized,
            country=self.country_code
        )


class SearchQuery(BaseModel):
    """Search query for website discovery."""
    
    query: str = Field(..., description="Search query string")
    priority: int = Field(default=1, description="Query priority")
    expected_domains: List[str] = Field(default_factory=list)
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate search query."""
        if not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()


class WebsiteDiscoveryConfig(BaseModel):
    """Configuration for website discovery system."""
    
    # Timeout settings
    request_timeout_seconds: float = 10.0
    total_discovery_timeout_seconds: float = 60.0
    
    # Discovery strategy settings
    max_domain_patterns: int = 10
    max_search_results: int = 5
    max_concurrent_validations: int = 3
    
    # Quality thresholds
    min_confidence_threshold: float = 0.6
    min_quality_threshold: float = 0.5
    
    # Search engine settings
    search_engine_enabled: bool = True
    search_api_key: Optional[str] = None
    
    # Domain patterns to try
    default_domain_patterns: List[str] = Field(
        default_factory=lambda: [
            "https://{company}.co.za",
            "https://www.{company}.co.za", 
            "https://{company}.com",
            "https://www.{company}.com",
            "https://{company}.org",
        ]
    )


class WebsiteDiscoveryStats(BaseModel):
    """Statistics for website discovery performance."""
    
    total_discoveries: int = 0
    successful_discoveries: int = 0
    failed_discoveries: int = 0
    
    # Method breakdown
    domain_pattern_successes: int = 0
    search_engine_successes: int = 0
    email_domain_successes: int = 0
    
    # Performance metrics
    average_discovery_time_ms: float = 0.0
    average_validation_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    
    # Quality metrics
    average_confidence_score: float = 0.0
    average_quality_score: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate discovery success rate."""
        if self.total_discoveries == 0:
            return 0.0
        return self.successful_discoveries / self.total_discoveries
    
    def update_with_result(self, result: WebsiteDiscoveryResult) -> None:
        """Update statistics with a new discovery result."""
        self.total_discoveries += 1
        
        if result.discovered_url:
            self.successful_discoveries += 1
            
            # Update method breakdown
            if result.discovery_method == DiscoveryMethod.DOMAIN_PATTERN:
                self.domain_pattern_successes += 1
            elif result.discovery_method == DiscoveryMethod.SEARCH_ENGINE:
                self.search_engine_successes += 1
            elif result.discovery_method == DiscoveryMethod.EMAIL_DOMAIN:
                self.email_domain_successes += 1
        else:
            self.failed_discoveries += 1
        
        # Update averages (simple running average)
        total = self.total_discoveries
        if result.processing_time_ms:
            self.average_discovery_time_ms = (
                (self.average_discovery_time_ms * (total - 1)) + result.processing_time_ms
            ) / total
        
        self.average_confidence_score = (
            (self.average_confidence_score * (total - 1)) + result.confidence
        ) / total
        
        if result.validation_result:
            self.average_quality_score = (
                (self.average_quality_score * (total - 1)) + 
                result.validation_result.overall_quality_score
            ) / total


# Update forward references
WebsiteDiscoveryResult.model_rebuild()
WebsiteValidationResult.model_rebuild()