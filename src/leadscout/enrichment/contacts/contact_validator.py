"""Enhanced contact validation leveraging classification system patterns.

Provides comprehensive contact quality assessment and validation
using proven async patterns and confidence scoring approaches.

Key Features:
- Contact quality scoring using classification confidence patterns
- Multi-source data enhancement (website + LinkedIn integration)
- South African contact format validation
- Business context awareness from name classification
- Async processing with timeout management

Architecture Decision: Uses the same confidence scoring and async patterns
as the classification system for consistency and proven reliability.

Developer B - Classification & Enrichment Specialist
"""

import asyncio
import re
import time
from typing import Any, Dict, List, Optional

from ...core.exceptions import LeadScoutError
from ...models.lead import Lead
from ..linkedin.models import LinkedInResearchResult
from ..website.models import WebsiteDiscoveryResult
from .models import (
    AddressValidationResult,
    ContactQualityScore,
    ContactValidationConfig,
    ContactValidationResult,
    ContactValidationStats,
    EmailValidationResult,
    EnhancedContactData,
    PhoneValidationResult,
    ValidationMethod,
)


class ContactValidationError(LeadScoutError):
    """Errors related to contact validation."""
    pass


class ContactValidator:
    """Validate and score contact information quality using proven patterns.
    
    Uses the same confidence scoring and async patterns as the classification
    system to provide reliable contact quality assessment and enhancement.
    """
    
    def __init__(
        self,
        config: Optional[ContactValidationConfig] = None,
        enable_caching: bool = True,
    ):
        """Initialize contact validator.
        
        Args:
            config: Validation configuration
            enable_caching: Whether to enable result caching
        """
        self.config = config or ContactValidationConfig()
        self.enable_caching = enable_caching
        
        # Statistics tracking (similar to classification system)
        self.stats = ContactValidationStats()
        
        # Cache for validation results (placeholder for Developer A integration)
        self._cache: Dict[str, ContactValidationResult] = {}
        
        # South African specific patterns
        self._sa_mobile_patterns = [
            r'^(\+27|0)[6-8][0-9]{8}$',  # SA mobile numbers
        ]
        self._sa_landline_patterns = [
            r'^(\+27|0)[1-5][0-9]{7,8}$',  # SA landline numbers
        ]
        self._sa_provinces = {
            'gauteng', 'western cape', 'kwazulu-natal', 'eastern cape',
            'free state', 'mpumalanga', 'limpopo', 'north west', 'northern cape'
        }
    
    async def validate_contact_completeness(
        self,
        lead: Lead
    ) -> ContactValidationResult:
        """Validate contact information completeness and quality.
        
        Use proven confidence scoring patterns from classification system.
        
        Args:
            lead: Lead object with contact information
            
        Returns:
            ContactValidationResult with quality scores and validation details
        """
        start_time = time.time()
        
        try:
            # Extract contact data from lead
            contact_data = {
                "email": lead.email_address,
                "phone": lead.contact_number,
                "mobile": lead.cell_number,
                "address": self._build_full_address(lead),
                "company": lead.entity_name,
                "director": lead.director_name,
            }
            
            # Generate cache key
            cache_key = self._generate_cache_key(contact_data)
            
            # Check cache first
            if self.enable_caching and cache_key in self._cache:
                cached_result = self._cache[cache_key]
                return cached_result
            
            # Perform validation with timeout
            try:
                result = await asyncio.wait_for(
                    self._perform_validation(contact_data, start_time),
                    timeout=self.config.validation_timeout_seconds
                )
            except asyncio.TimeoutError:
                # Return basic result on timeout
                result = ContactValidationResult(
                    original_contact_data=contact_data,
                    overall_quality_score=0.0,
                    completeness_score=0.0,
                    business_relevance_score=0.0,
                    processing_time_ms=(time.time() - start_time) * 1000,
                )
            
            # Cache the result
            if self.enable_caching:
                self._cache[cache_key] = result
            
            # Update statistics
            self.stats.update_with_result(result)
            
            return result
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Return error result
            error_result = ContactValidationResult(
                original_contact_data=contact_data if 'contact_data' in locals() else {},
                overall_quality_score=0.0,
                completeness_score=0.0,
                business_relevance_score=0.0,
                processing_time_ms=processing_time_ms,
            )
            
            self.stats.update_with_result(error_result)
            return error_result
    
    async def _perform_validation(
        self,
        contact_data: Dict[str, Any],
        start_time: float
    ) -> ContactValidationResult:
        """Perform the actual contact validation."""
        
        validation_methods = []
        
        # Validate email
        email_result = None
        if contact_data.get("email"):
            email_result = await self._validate_email(contact_data["email"])
            validation_methods.append(ValidationMethod.FORMAT_CHECK)
            validation_methods.append(ValidationMethod.DOMAIN_VALIDATION)
        
        # Validate phone numbers
        phone_result = None
        if contact_data.get("phone"):
            phone_result = await self._validate_phone(contact_data["phone"])
            validation_methods.append(ValidationMethod.PHONE_PARSING)
        
        mobile_result = None
        if contact_data.get("mobile"):
            mobile_result = await self._validate_phone(contact_data["mobile"])
            validation_methods.append(ValidationMethod.PHONE_PARSING)
        
        # Validate address
        address_result = None
        if contact_data.get("address"):
            address_result = await self._validate_address(contact_data["address"])
            validation_methods.append(ValidationMethod.ADDRESS_STANDARDIZATION)
        
        # Calculate quality scores using classification confidence patterns
        quality_scores = self._calculate_quality_scores(
            email_result, phone_result, mobile_result, address_result, contact_data
        )
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return ContactValidationResult(
            original_contact_data=contact_data,
            email_validation=email_result,
            phone_validation=phone_result,
            mobile_validation=mobile_result,
            address_validation=address_result,
            overall_quality_score=quality_scores["overall"],
            completeness_score=quality_scores["completeness"],
            business_relevance_score=quality_scores["business_relevance"],
            validation_methods_used=validation_methods,
            processing_time_ms=processing_time_ms,
        )
    
    async def _validate_email(self, email: str) -> EmailValidationResult:
        """Validate email address with business context analysis."""
        
        # Basic format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid_format = bool(re.match(email_pattern, email))
        
        if not is_valid_format:
            return EmailValidationResult(
                email=email,
                is_valid_format=False,
            )
        
        # Extract domain
        domain = email.split('@')[1].lower()
        
        # Analyze business context
        personal_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'webmail.co.za', 'mweb.co.za', 'telkomsa.net'
        }
        
        is_business_email = domain not in personal_domains
        likely_personal = domain in personal_domains
        
        # Check for role-based emails
        local_part = email.split('@')[0].lower()
        role_patterns = ['info', 'admin', 'sales', 'support', 'contact', 'hello']
        likely_role_based = any(pattern in local_part for pattern in role_patterns)
        
        # Domain reputation (simplified scoring)
        domain_reputation = 0.8 if is_business_email else 0.3
        
        return EmailValidationResult(
            email=email,
            is_valid_format=True,
            domain=domain,
            is_business_email=is_business_email,
            likely_personal=likely_personal,
            likely_role_based=likely_role_based,
            domain_reputation_score=domain_reputation,
        )
    
    async def _validate_phone(self, phone: str) -> PhoneValidationResult:
        """Validate phone number with South African patterns."""
        
        # Normalize phone number
        normalized = re.sub(r'[^\d+]', '', phone)
        
        # Check SA mobile patterns
        is_mobile = any(re.match(pattern, normalized) for pattern in self._sa_mobile_patterns)
        
        # Check SA landline patterns  
        is_landline = any(re.match(pattern, normalized) for pattern in self._sa_landline_patterns)
        
        is_valid_format = is_mobile or is_landline
        
        # Extract country and area codes
        country_code = None
        area_code = None
        
        if normalized.startswith('+27'):
            country_code = '+27'
            area_code = normalized[3:5] if len(normalized) > 5 else None
        elif normalized.startswith('0'):
            country_code = '+27'  # Assume SA
            area_code = normalized[0:3] if len(normalized) > 3 else None
        
        # Determine region for SA numbers
        region = None
        if area_code:
            area_code_map = {
                '011': 'Gauteng (Johannesburg)',
                '012': 'Gauteng (Pretoria)',
                '021': 'Western Cape (Cape Town)',
                '031': 'KwaZulu-Natal (Durban)',
                '041': 'Eastern Cape (Port Elizabeth)',
                '051': 'Free State (Bloemfontein)',
            }
            region = area_code_map.get(area_code, 'South Africa')
        
        return PhoneValidationResult(
            phone=phone,
            is_valid_format=is_valid_format,
            country_code=country_code,
            area_code=area_code,
            is_mobile=is_mobile,
            is_landline=is_landline,
            likely_business_hours=is_landline,  # Landlines more likely business
            region=region,
        )
    
    async def _validate_address(self, address: str) -> AddressValidationResult:
        """Validate and analyze address completeness."""
        
        if not address or not address.strip():
            return AddressValidationResult(
                address=address,
                is_complete=False,
                completeness_score=0.0,
            )
        
        address_lower = address.lower()
        
        # Check for address components
        has_street = bool(re.search(r'\d+.*\b(street|st|road|rd|avenue|ave|drive|dr)\b', address_lower))
        has_city = any(city in address_lower for city in [
            'johannesburg', 'cape town', 'durban', 'pretoria', 'bloemfontein',
            'port elizabeth', 'east london', 'pietermaritzburg', 'kimberley'
        ])
        has_province = any(province in address_lower for province in self._sa_provinces)
        has_postal_code = bool(re.search(r'\b\d{4}\b', address))
        
        # Calculate completeness score
        components = [has_street, has_city, has_province, has_postal_code]
        completeness_score = sum(components) / len(components)
        
        is_complete = completeness_score >= 0.75
        
        # Check for business district indicators
        business_indicators = ['business', 'industrial', 'office', 'park', 'centre', 'tower']
        is_business_district = any(indicator in address_lower for indicator in business_indicators)
        
        return AddressValidationResult(
            address=address,
            is_complete=is_complete,
            completeness_score=completeness_score,
            is_business_district=is_business_district,
            is_residential_area=not is_business_district,
        )
    
    def _calculate_quality_scores(
        self,
        email_result: Optional[EmailValidationResult],
        phone_result: Optional[PhoneValidationResult],
        mobile_result: Optional[PhoneValidationResult],
        address_result: Optional[AddressValidationResult],
        contact_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate quality scores using classification confidence patterns."""
        
        # Individual component scores
        email_score = 0.0
        if email_result:
            if email_result.is_valid_format:
                email_score = 0.6  # Base score for valid format
                if email_result.is_business_email:
                    email_score += 0.3  # Bonus for business email
                if not email_result.likely_personal:
                    email_score += 0.1  # Bonus for non-personal
        
        phone_score = 0.0
        if phone_result and phone_result.is_valid_format:
            phone_score = 0.7
            if phone_result.is_mobile:
                phone_score += 0.2  # Mobile is preferred
            if phone_result.likely_business_hours:
                phone_score += 0.1
        
        mobile_score = 0.0
        if mobile_result and mobile_result.is_valid_format:
            mobile_score = 0.8  # Mobile is high value
            if mobile_result.is_mobile:
                mobile_score += 0.2
        
        address_score = 0.0
        if address_result:
            address_score = address_result.completeness_score
            if address_result.is_business_district:
                address_score += 0.1  # Bonus for business context
        
        # Combine phone and mobile scores (take the better one)
        phone_combined_score = max(phone_score, mobile_score)
        
        # Calculate completeness (how many fields are present)
        field_count = sum([
            1 if contact_data.get("email") else 0,
            1 if contact_data.get("phone") else 0,
            1 if contact_data.get("mobile") else 0,
            1 if contact_data.get("address") else 0,
        ])
        completeness_score = field_count / 4.0
        
        # Calculate business relevance
        business_relevance = 0.0
        if email_result and email_result.is_business_email:
            business_relevance += 0.4
        if phone_result and phone_result.likely_business_hours:
            business_relevance += 0.3
        if address_result and address_result.is_business_district:
            business_relevance += 0.3
        
        # Calculate overall score using weights (similar to classification confidence)
        overall_score = (
            email_score * self.config.email_weight +
            phone_combined_score * self.config.phone_weight +
            address_score * self.config.address_weight +
            completeness_score * self.config.completeness_weight
        )
        
        return {
            "overall": min(1.0, overall_score),
            "completeness": completeness_score,
            "business_relevance": min(1.0, business_relevance),
            "email": email_score,
            "phone": phone_combined_score,
            "address": address_score,
        }
    
    async def enhance_contact_data(
        self,
        lead: Lead,
        discovered_website: Optional[WebsiteDiscoveryResult] = None,
        linkedin_data: Optional[LinkedInResearchResult] = None
    ) -> EnhancedContactData:
        """Enhance contact data using discovered information.
        
        Integration point with website and LinkedIn research systems.
        """
        
        # Start with original contact data
        enhanced = EnhancedContactData(
            original_email=lead.email_address,
            original_phone=lead.contact_number,
            original_mobile=lead.cell_number,
            original_address=self._build_full_address(lead),
        )
        
        enhancement_methods = []
        
        # Enhance with website data
        if discovered_website and discovered_website.validation_result:
            website_val = discovered_website.validation_result
            
            # Extract contact info from website (mock implementation)
            if website_val.has_contact_info:
                enhanced.website_email = "info@" + discovered_website.discovered_url.split("//")[1]
                enhanced.website_phone = "011-555-0123"  # Mock data
                enhancement_methods.append("website_contact_extraction")
        
        # Enhance with LinkedIn data
        if linkedin_data and linkedin_data.profile_found:
            enhanced.linkedin_company = linkedin_data.current_company
            enhanced.linkedin_industry = linkedin_data.industry
            enhanced.linkedin_location = linkedin_data.location
            enhancement_methods.append("linkedin_professional_data")
        
        # Validate enhanced data
        validation_result = await self.validate_contact_completeness(lead)
        enhanced.validation_result = validation_result
        
        # Calculate quality score
        quality_score = ContactQualityScore(
            email_quality=0.8 if enhanced.best_email else 0.0,
            phone_quality=0.8 if enhanced.best_phone else 0.0,
            address_quality=0.6 if enhanced.best_address else 0.0,
            completeness=validation_result.completeness_score,
            has_business_email=bool(enhanced.website_email),
            has_mobile_number=bool(enhanced.original_mobile),
            has_website=bool(discovered_website),
            has_linkedin=bool(linkedin_data and linkedin_data.profile_found),
            enhanced_by_website=bool(discovered_website),
            enhanced_by_linkedin=bool(linkedin_data),
        )
        quality_score.calculate_overall_score()
        enhanced.quality_score = quality_score
        
        enhanced.enhancement_methods = enhancement_methods
        
        return enhanced
    
    def calculate_contact_quality_score(
        self,
        contact_data: dict
    ) -> ContactQualityScore:
        """Calculate overall contact quality score.
        
        Use proven scoring methodology from classification confidence.
        """
        
        # Analyze contact data
        has_email = bool(contact_data.get("email"))
        has_phone = bool(contact_data.get("phone"))
        has_mobile = bool(contact_data.get("mobile"))
        has_address = bool(contact_data.get("address"))
        
        # Calculate component scores
        email_quality = 0.8 if has_email else 0.0
        phone_quality = 0.9 if has_mobile else (0.6 if has_phone else 0.0)
        address_quality = 0.7 if has_address else 0.0
        
        completeness = sum([has_email, has_phone, has_mobile, has_address]) / 4.0
        
        # Create quality score object
        quality_score = ContactQualityScore(
            email_quality=email_quality,
            phone_quality=phone_quality,
            address_quality=address_quality,
            completeness=completeness,
            has_business_email=has_email,
            has_mobile_number=has_mobile,
            has_complete_address=has_address,
        )
        
        quality_score.calculate_overall_score()
        return quality_score
    
    def _build_full_address(self, lead: Lead) -> str:
        """Build full address from lead components."""
        address_parts = []
        
        if lead.registered_address:
            address_parts.append(lead.registered_address)
        if lead.registered_address_city:
            address_parts.append(lead.registered_address_city)
        if lead.registered_address_province:
            address_parts.append(lead.registered_address_province)
        
        return ", ".join(part for part in address_parts if part)
    
    def _generate_cache_key(self, contact_data: Dict[str, Any]) -> str:
        """Generate cache key for contact validation result."""
        key_parts = []
        for field in ["email", "phone", "mobile", "address"]:
            value = contact_data.get(field, "")
            if value:
                key_parts.append(f"{field}:{value.lower().strip()}")
        return "|".join(key_parts)
    
    def get_validation_stats(self) -> ContactValidationStats:
        """Get current validation statistics."""
        return self.stats
    
    def reset_stats(self) -> ContactValidationStats:
        """Reset statistics and return previous stats."""
        old_stats = self.stats
        self.stats = ContactValidationStats()
        return old_stats