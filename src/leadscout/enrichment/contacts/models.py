"""Data models for contact validation and enhancement.

This module defines the data models used for contact validation results,
quality scoring, and data enhancement following the proven confidence
scoring patterns from the classification system.

Developer B - Classification & Enrichment Specialist
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ValidationMethod(Enum):
    """Method used for contact validation."""
    
    FORMAT_CHECK = "format_check"
    DOMAIN_VALIDATION = "domain_validation"
    PHONE_PARSING = "phone_parsing"
    ADDRESS_STANDARDIZATION = "address_standardization"
    WEBSITE_ENHANCEMENT = "website_enhancement"
    LINKEDIN_ENHANCEMENT = "linkedin_enhancement"


class ContactType(Enum):
    """Type of contact information."""
    
    EMAIL = "email"
    PHONE = "phone"
    MOBILE = "mobile"
    ADDRESS = "address"
    WEBSITE = "website"
    LINKEDIN = "linkedin"


class EmailValidationResult(BaseModel):
    """Result from email validation."""
    
    email: str = Field(..., description="Email address validated")
    is_valid_format: bool = False
    domain: Optional[str] = None
    is_business_email: bool = False
    is_disposable: bool = False
    
    # Domain analysis
    domain_reputation_score: float = Field(default=0.0, ge=0.0, le=1.0)
    mx_record_exists: bool = False
    
    # Business context
    likely_personal: bool = False
    likely_role_based: bool = False  # info@, sales@, etc.
    
    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Basic email format validation."""
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()


class PhoneValidationResult(BaseModel):
    """Result from phone number validation."""
    
    phone: str = Field(..., description="Phone number validated")
    is_valid_format: bool = False
    country_code: Optional[str] = None
    area_code: Optional[str] = None
    
    # Phone type analysis
    is_mobile: bool = False
    is_landline: bool = False
    is_toll_free: bool = False
    
    # Business context
    likely_business_hours: bool = False
    region: Optional[str] = None
    carrier: Optional[str] = None
    
    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        """Normalize phone number format."""
        # Remove non-digit characters except +
        import re
        normalized = re.sub(r'[^\d+]', '', v)
        return normalized


class AddressValidationResult(BaseModel):
    """Result from address validation."""
    
    address: str = Field(..., description="Address validated")
    is_complete: bool = False
    standardized_address: Optional[str] = None
    
    # Address components
    street_address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    
    # Business context
    is_business_district: bool = False
    is_residential_area: bool = False
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)


class ContactValidationResult(BaseModel):
    """Complete contact validation result."""
    
    # Input data
    original_contact_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation results by type
    email_validation: Optional[EmailValidationResult] = None
    phone_validation: Optional[PhoneValidationResult] = None
    mobile_validation: Optional[PhoneValidationResult] = None
    address_validation: Optional[AddressValidationResult] = None
    
    # Overall scores (using classification confidence patterns)
    overall_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    business_relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Validation metadata
    validation_methods_used: List[ValidationMethod] = Field(default_factory=list)
    processing_time_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def contact_quality_grade(self) -> str:
        """Get quality grade similar to classification confidence levels."""
        if self.overall_quality_score >= 0.9:
            return "excellent"
        elif self.overall_quality_score >= 0.8:
            return "good" 
        elif self.overall_quality_score >= 0.6:
            return "fair"
        elif self.overall_quality_score >= 0.4:
            return "poor"
        else:
            return "very_poor"


class ContactQualityScore(BaseModel):
    """Detailed contact quality scoring using classification confidence patterns."""
    
    # Individual component scores
    email_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    phone_quality: float = Field(default=0.0, ge=0.0, le=1.0) 
    address_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Composite scores
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_level: str = "low"  # low, medium, high, very_high
    
    # Quality factors
    has_business_email: bool = False
    has_mobile_number: bool = False
    has_complete_address: bool = False
    has_website: bool = False
    has_linkedin: bool = False
    
    # Enhancement indicators
    enhanced_by_website: bool = False
    enhanced_by_linkedin: bool = False
    enhanced_by_validation: bool = False
    
    def calculate_overall_score(self) -> None:
        """Calculate overall score using weighted components."""
        weights = {
            "email": 0.3,
            "phone": 0.25,
            "address": 0.2,
            "completeness": 0.25
        }
        
        self.overall_score = (
            self.email_quality * weights["email"] +
            self.phone_quality * weights["phone"] +
            self.address_quality * weights["address"] +
            self.completeness * weights["completeness"]
        )
        
        # Set confidence level based on score
        if self.overall_score >= 0.85:
            self.confidence_level = "very_high"
        elif self.overall_score >= 0.7:
            self.confidence_level = "high"
        elif self.overall_score >= 0.5:
            self.confidence_level = "medium"
        else:
            self.confidence_level = "low"


class EnhancedContactData(BaseModel):
    """Enhanced contact data combining original data with discovered information."""
    
    # Original contact data
    original_email: Optional[str] = None
    original_phone: Optional[str] = None
    original_mobile: Optional[str] = None
    original_address: Optional[str] = None
    
    # Enhanced data from website discovery
    website_email: Optional[str] = None
    website_phone: Optional[str] = None
    website_address: Optional[str] = None
    
    # Enhanced data from LinkedIn research
    linkedin_company: Optional[str] = None
    linkedin_industry: Optional[str] = None
    linkedin_location: Optional[str] = None
    
    # Validated and standardized data
    validated_email: Optional[str] = None
    validated_phone: Optional[str] = None
    validated_mobile: Optional[str] = None
    standardized_address: Optional[str] = None
    
    # Quality assessment
    quality_score: Optional[ContactQualityScore] = None
    validation_result: Optional[ContactValidationResult] = None
    
    # Enhancement metadata
    enhancement_methods: List[str] = Field(default_factory=list)
    enhancement_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def best_email(self) -> Optional[str]:
        """Get the best available email address."""
        if self.validated_email:
            return self.validated_email
        elif self.website_email:
            return self.website_email
        else:
            return self.original_email
    
    @property
    def best_phone(self) -> Optional[str]:
        """Get the best available phone number."""
        if self.validated_phone:
            return self.validated_phone
        elif self.website_phone:
            return self.website_phone
        else:
            return self.original_phone
    
    @property
    def best_address(self) -> Optional[str]:
        """Get the best available address."""
        if self.standardized_address:
            return self.standardized_address
        elif self.website_address:
            return self.website_address
        else:
            return self.original_address


class ContactValidationConfig(BaseModel):
    """Configuration for contact validation."""
    
    # Validation thresholds
    min_quality_threshold: float = 0.5
    require_business_email: bool = False
    require_mobile_number: bool = False
    
    # Enhancement settings
    enhance_with_website_data: bool = True
    enhance_with_linkedin_data: bool = True
    validate_email_domains: bool = True
    validate_phone_formats: bool = True
    
    # Performance settings
    validation_timeout_seconds: float = 10.0
    max_concurrent_validations: int = 5
    
    # Scoring weights
    email_weight: float = 0.3
    phone_weight: float = 0.25
    address_weight: float = 0.2
    completeness_weight: float = 0.25


class ContactValidationStats(BaseModel):
    """Statistics for contact validation performance."""
    
    total_validations: int = 0
    successful_validations: int = 0
    enhanced_contacts: int = 0
    
    # Quality distribution
    excellent_quality_contacts: int = 0  # >0.9
    good_quality_contacts: int = 0       # 0.8-0.9
    fair_quality_contacts: int = 0       # 0.6-0.8
    poor_quality_contacts: int = 0       # <0.6
    
    # Enhancement breakdown
    website_enhancements: int = 0
    linkedin_enhancements: int = 0
    validation_improvements: int = 0
    
    # Performance metrics
    average_validation_time_ms: float = 0.0
    average_quality_score: float = 0.0
    enhancement_success_rate: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate validation success rate."""
        if self.total_validations == 0:
            return 0.0
        return self.successful_validations / self.total_validations
    
    def update_with_result(self, result: ContactValidationResult) -> None:
        """Update statistics with a new validation result."""
        self.total_validations += 1
        
        if result.overall_quality_score >= 0.5:
            self.successful_validations += 1
        
        # Update quality distribution
        if result.overall_quality_score >= 0.9:
            self.excellent_quality_contacts += 1
        elif result.overall_quality_score >= 0.8:
            self.good_quality_contacts += 1
        elif result.overall_quality_score >= 0.6:
            self.fair_quality_contacts += 1
        else:
            self.poor_quality_contacts += 1
        
        # Update averages
        total = self.total_validations
        self.average_quality_score = (
            (self.average_quality_score * (total - 1)) + result.overall_quality_score
        ) / total
        
        if result.processing_time_ms:
            self.average_validation_time_ms = (
                (self.average_validation_time_ms * (total - 1)) + result.processing_time_ms
            ) / total
        
        # Update enhancement rate
        if len(result.validation_methods_used) > 1:  # More than just format check
            self.enhanced_contacts += 1
        
        self.enhancement_success_rate = self.enhanced_contacts / total


# Update forward references
ContactValidationResult.model_rebuild()
ContactQualityScore.model_rebuild()
EnhancedContactData.model_rebuild()