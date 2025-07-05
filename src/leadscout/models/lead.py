"""Lead data models for input and output structures."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
import re

from .classification import Classification
from .contact import ContactValidation


class Lead(BaseModel):
    """Input lead data model with validation.
    
    Represents the input data structure from Excel files with all required
    fields for lead enrichment processing.
    
    Attributes:
        entity_name: Legal business name
        trading_as_name: Trading/brand name  
        keyword: Industry/business type descriptor
        contact_number: Primary business phone number
        cell_number: Mobile phone number
        email_address: Contact email address
        registered_address: Full business address
        registered_address_city: City name
        registered_address_province: Province/state
        director_name: Director/owner name
        director_cell: Director mobile number
        
    Example:
        >>> lead = Lead(
        ...     entity_name="ABC Trading CC",
        ...     trading_as_name="ABC Electronics", 
        ...     keyword="electronics retail",
        ...     contact_number="011-123-4567",
        ...     cell_number="082-123-4567",
        ...     email_address="info@abc.co.za",
        ...     registered_address="123 Main St, Johannesburg",
        ...     registered_address_city="Johannesburg",
        ...     registered_address_province="Gauteng",
        ...     director_name="John Smith",
        ...     director_cell="082-987-6543"
        ... )
    """
    
    entity_name: str = Field(..., min_length=2, max_length=255, description="Legal business name")
    trading_as_name: str = Field(..., min_length=2, max_length=255, description="Trading/brand name")
    keyword: str = Field(..., min_length=2, max_length=100, description="Industry/business type")
    contact_number: str = Field(..., min_length=10, max_length=20, description="Primary phone number")
    cell_number: str = Field(..., min_length=10, max_length=20, description="Mobile phone number")
    email_address: str = Field(..., description="Contact email address")
    registered_address: str = Field(..., min_length=10, max_length=500, description="Full business address")
    registered_address_city: str = Field(..., min_length=2, max_length=100, description="City name")
    registered_address_province: str = Field(..., min_length=2, max_length=100, description="Province/state")
    director_name: str = Field(..., min_length=2, max_length=255, description="Director/owner name")
    director_cell: str = Field(..., min_length=10, max_length=20, description="Director mobile number")
    
    @validator('entity_name', 'trading_as_name', 'director_name')
    def validate_names(cls, v: str) -> str:
        """Validate and clean name fields."""
        if not v or not v.strip():
            raise ValueError("Name fields cannot be empty")
        
        # Clean up extra whitespace
        cleaned = ' '.join(v.strip().split())
        
        # Check for suspicious characters that might indicate data corruption
        if any(char in cleaned for char in ['|', '\t', '\n', '\r']):
            raise ValueError("Name contains invalid characters")
            
        return cleaned
    
    @validator('email_address')
    def validate_email(cls, v: str) -> str:
        """Validate email address format."""
        if not v or not v.strip():
            raise ValueError("Email address is required")
            
        email = v.strip().lower()
        
        # Basic email validation regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email address format")
            
        return email
    
    @validator('contact_number', 'cell_number', 'director_cell')
    def validate_phone_numbers(cls, v: str) -> str:
        """Validate and normalize phone number format."""
        if not v or not v.strip():
            raise ValueError("Phone number is required")
            
        # Remove all non-digit characters except + at the start
        phone = re.sub(r'[^\d+]', '', v.strip())
        
        # Remove leading + for South African numbers
        if phone.startswith('+27'):
            phone = '0' + phone[3:]
        elif phone.startswith('27') and len(phone) >= 10:
            phone = '0' + phone[2:]
            
        # Validate South African phone number format
        if not re.match(r'^0[1-9]\d{8}$', phone):
            raise ValueError("Invalid South African phone number format")
            
        return phone
    
    @validator('registered_address_province')
    def validate_province(cls, v: str) -> str:
        """Validate South African province names."""
        if not v or not v.strip():
            raise ValueError("Province is required")
            
        province = v.strip().title()
        
        # List of valid South African provinces
        valid_provinces = {
            'Eastern Cape', 'Free State', 'Gauteng', 'KwaZulu-Natal',
            'Limpopo', 'Mpumalanga', 'Northern Cape', 'North West', 'Western Cape'
        }
        
        # Allow some common variations
        province_mapping = {
            'Kzn': 'KwaZulu-Natal',
            'Kwazulu-Natal': 'KwaZulu-Natal',
            'Kwazulu Natal': 'KwaZulu-Natal',
            'North-West': 'North West',
            'Northwest': 'North West',
            'Ec': 'Eastern Cape',
            'Wc': 'Western Cape',
            'Nc': 'Northern Cape',
            'Gp': 'Gauteng',
            'Fs': 'Free State',
            'Mp': 'Mpumalanga',
            'Lp': 'Limpopo'
        }
        
        if province in province_mapping:
            province = province_mapping[province]
        elif province not in valid_provinces:
            # Don't reject, but note for manual review
            pass
            
        return province
    
    def get_hash(self) -> str:
        """Generate a unique hash for this lead for caching purposes.
        
        Returns:
            SHA-256 hash of key lead identifiers
        """
        import hashlib
        
        # Use key identifiers that uniquely identify this lead
        key_data = f"{self.entity_name}|{self.trading_as_name}|{self.email_address}"
        return hashlib.sha256(key_data.encode('utf-8')).hexdigest()


class EnrichedLead(BaseModel):
    """Output model for enriched lead data.
    
    Contains the original lead data plus all enrichment information
    gathered from various sources.
    
    Attributes:
        original_lead: The original input lead data
        classification: Name ethnicity classification results
        contact_validation: Contact information validation results
        website_url: Discovered company website
        linkedin_profile: Director LinkedIn profile URL
        website_found: Flag indicating website was discovered
        linkedin_found: Flag indicating LinkedIn profile was found
        data_richness_score: Overall data availability score (0-100)
        contact_quality_score: Contact information quality score (0-100) 
        priority_score: Final lead prioritization score (0-100)
        confidence_level: Overall confidence in enrichment data (0-1)
        processing_timestamp: When enrichment was completed
        error_messages: Any errors encountered during processing
        
    Example:
        >>> enriched = EnrichedLead(
        ...     original_lead=lead,
        ...     classification=Classification(ethnicity="european", confidence=0.95),
        ...     website_found=True,
        ...     website_url="https://abc.co.za",
        ...     priority_score=85
        ... )
    """
    
    # Original data
    original_lead: Lead = Field(..., description="Original input lead data")
    
    # Enrichment data
    classification: Optional[Classification] = Field(None, description="Name ethnicity classification")
    contact_validation: Optional[ContactValidation] = Field(None, description="Contact validation results")
    website_url: Optional[str] = Field(None, description="Discovered company website")
    linkedin_profile: Optional[str] = Field(None, description="Director LinkedIn profile URL")
    
    # Data availability flags
    website_found: bool = Field(False, description="Website discovery success flag")
    linkedin_found: bool = Field(False, description="LinkedIn profile found flag")
    
    # Scoring metrics
    data_richness_score: float = Field(0.0, ge=0, le=100, description="Data availability score")
    contact_quality_score: float = Field(0.0, ge=0, le=100, description="Contact quality score")
    priority_score: float = Field(0.0, ge=0, le=100, description="Final prioritization score")
    confidence_level: float = Field(0.0, ge=0, le=1, description="Overall confidence level")
    
    # Processing metadata
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Processing completion time")
    error_messages: list[str] = Field(default_factory=list, description="Processing errors")
    
    @validator('website_url')
    def validate_website_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate website URL format."""
        if v is None:
            return v
            
        url = v.strip()
        if not url:
            return None
            
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Basic URL validation
        url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/.*)?$'
        if not re.match(url_pattern, url):
            raise ValueError("Invalid website URL format")
            
        return url
    
    @validator('linkedin_profile')
    def validate_linkedin_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate LinkedIn profile URL format."""
        if v is None:
            return v
            
        url = v.strip()
        if not url:
            return None
            
        # Ensure LinkedIn URL format
        if 'linkedin.com' not in url.lower():
            raise ValueError("Invalid LinkedIn URL")
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        return url
    
    def add_error(self, error_message: str) -> None:
        """Add an error message to the enrichment results.
        
        Args:
            error_message: Description of the error that occurred
        """
        self.error_messages.append(error_message)
    
    def has_errors(self) -> bool:
        """Check if any errors occurred during processing.
        
        Returns:
            True if errors were encountered, False otherwise
        """
        return len(self.error_messages) > 0
    
    def get_enrichment_summary(self) -> dict[str, any]:
        """Get a summary of enrichment results.
        
        Returns:
            Dictionary containing key enrichment metrics
        """
        return {
            'entity_name': self.original_lead.entity_name,
            'classification': self.classification.ethnicity if self.classification else None,
            'classification_confidence': self.classification.confidence if self.classification else 0,
            'website_found': self.website_found,
            'linkedin_found': self.linkedin_found,
            'priority_score': self.priority_score,
            'confidence_level': self.confidence_level,
            'has_errors': self.has_errors(),
            'error_count': len(self.error_messages)
        }