"""Complete lead enrichment pipeline orchestrating all enrichment systems.

Coordinates name classification, website discovery, LinkedIn research,
and contact validation into a unified enrichment workflow.

Key Features:
- End-to-end lead enrichment in <10 seconds per lead
- Async batch processing with optimal concurrency
- Graceful degradation when individual services fail
- Comprehensive error handling and recovery
- Performance monitoring and statistics tracking
- Integration with all Developer B enrichment systems

Architecture Decision: Uses the same async patterns and error handling
as all other systems for consistency and proven reliability.

Developer B - Classification & Enrichment Specialist
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..classification import NameClassifier
from ..core.exceptions import LeadScoutError
from ..models.lead import EnrichedLead, Lead
from .contacts import ContactValidator, EnhancedContactData
from .linkedin import LinkedInResearcher
from .website import WebsiteDiscoverer
from pydantic import BaseModel, Field


class EnrichmentError(LeadScoutError):
    """Errors related to lead enrichment pipeline."""
    pass


class EnrichmentConfig(BaseModel):
    """Configuration for the complete enrichment pipeline."""
    
    # Performance settings
    max_enrichment_time_seconds: float = 10.0
    max_concurrent_leads: int = 10
    batch_size: int = 5
    
    # Service enabling/disabling
    enable_classification: bool = True
    enable_website_discovery: bool = True
    enable_linkedin_research: bool = True
    enable_contact_validation: bool = True
    
    # Quality thresholds
    min_classification_confidence: float = 0.6
    min_website_confidence: float = 0.6
    min_linkedin_confidence: float = 0.5
    min_contact_quality: float = 0.5
    
    # Fallback behavior
    fail_fast: bool = False  # Continue with partial results vs fail completely
    require_classification: bool = True  # Classification is core requirement
    require_website: bool = False
    require_linkedin: bool = False
    require_contact_validation: bool = False
    
    # Timeout settings for individual services
    classification_timeout: float = 5.0
    website_discovery_timeout: float = 8.0
    linkedin_research_timeout: float = 10.0
    contact_validation_timeout: float = 3.0


class EnrichmentResult(BaseModel):
    """Result from individual lead enrichment."""
    
    lead: Lead = Field(..., description="Original lead data")
    enriched_lead: Optional[EnrichedLead] = None
    
    # Individual service results
    classification_success: bool = False
    website_discovery_success: bool = False
    linkedin_research_success: bool = False
    contact_validation_success: bool = False
    
    # Performance metrics
    total_processing_time_ms: float = 0.0
    classification_time_ms: float = 0.0
    website_discovery_time_ms: float = 0.0
    linkedin_research_time_ms: float = 0.0
    contact_validation_time_ms: float = 0.0
    
    # Quality metrics
    overall_confidence: float = 0.0
    data_richness_score: float = 0.0
    
    # Error tracking
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate across all services."""
        services = [
            self.classification_success,
            self.website_discovery_success,
            self.linkedin_research_success,
            self.contact_validation_success
        ]
        return sum(services) / len(services)


class EnrichmentStats(BaseModel):
    """Statistics for enrichment pipeline performance."""
    
    total_leads_processed: int = 0
    successful_enrichments: int = 0
    failed_enrichments: int = 0
    
    # Service success rates
    classification_success_rate: float = 0.0
    website_discovery_success_rate: float = 0.0
    linkedin_research_success_rate: float = 0.0
    contact_validation_success_rate: float = 0.0
    
    # Performance metrics
    average_processing_time_ms: float = 0.0
    average_classification_time_ms: float = 0.0
    average_website_discovery_time_ms: float = 0.0
    average_linkedin_research_time_ms: float = 0.0
    average_contact_validation_time_ms: float = 0.0
    
    # Quality metrics
    average_confidence: float = 0.0
    average_data_richness: float = 0.0
    high_quality_leads: int = 0  # >80% confidence
    medium_quality_leads: int = 0  # 60-80% confidence
    low_quality_leads: int = 0  # <60% confidence
    
    @property
    def overall_success_rate(self) -> float:
        """Calculate overall enrichment success rate."""
        if self.total_leads_processed == 0:
            return 0.0
        return self.successful_enrichments / self.total_leads_processed
    
    def update_with_result(self, result: EnrichmentResult) -> None:
        """Update statistics with a new enrichment result."""
        self.total_leads_processed += 1
        
        if result.enriched_lead:
            self.successful_enrichments += 1
        else:
            self.failed_enrichments += 1
        
        # Update service success rates
        total = self.total_leads_processed
        
        # Calculate running averages for service success rates
        classification_successes = (self.classification_success_rate * (total - 1)) + (1 if result.classification_success else 0)
        self.classification_success_rate = classification_successes / total
        
        website_successes = (self.website_discovery_success_rate * (total - 1)) + (1 if result.website_discovery_success else 0)
        self.website_discovery_success_rate = website_successes / total
        
        linkedin_successes = (self.linkedin_research_success_rate * (total - 1)) + (1 if result.linkedin_research_success else 0)
        self.linkedin_research_success_rate = linkedin_successes / total
        
        contact_successes = (self.contact_validation_success_rate * (total - 1)) + (1 if result.contact_validation_success else 0)
        self.contact_validation_success_rate = contact_successes / total
        
        # Update performance averages
        self.average_processing_time_ms = (
            (self.average_processing_time_ms * (total - 1)) + result.total_processing_time_ms
        ) / total
        
        self.average_classification_time_ms = (
            (self.average_classification_time_ms * (total - 1)) + result.classification_time_ms
        ) / total
        
        self.average_website_discovery_time_ms = (
            (self.average_website_discovery_time_ms * (total - 1)) + result.website_discovery_time_ms
        ) / total
        
        self.average_linkedin_research_time_ms = (
            (self.average_linkedin_research_time_ms * (total - 1)) + result.linkedin_research_time_ms
        ) / total
        
        self.average_contact_validation_time_ms = (
            (self.average_contact_validation_time_ms * (total - 1)) + result.contact_validation_time_ms
        ) / total
        
        # Update quality metrics
        self.average_confidence = (
            (self.average_confidence * (total - 1)) + result.overall_confidence
        ) / total
        
        self.average_data_richness = (
            (self.average_data_richness * (total - 1)) + result.data_richness_score
        ) / total
        
        # Update quality distribution
        if result.overall_confidence >= 0.8:
            self.high_quality_leads += 1
        elif result.overall_confidence >= 0.6:
            self.medium_quality_leads += 1
        else:
            self.low_quality_leads += 1


class LeadEnrichmentPipeline:
    """Master pipeline coordinating all enrichment systems.
    
    Provides complete lead enrichment using all available systems with
    proven async patterns and comprehensive error handling.
    """
    
    def __init__(
        self,
        config: Optional[EnrichmentConfig] = None,
        name_classifier: Optional[NameClassifier] = None,
        website_discoverer: Optional[WebsiteDiscoverer] = None,
        linkedin_researcher: Optional[LinkedInResearcher] = None,
        contact_validator: Optional[ContactValidator] = None,
    ):
        """Initialize enrichment pipeline.
        
        Args:
            config: Pipeline configuration
            name_classifier: Name classification system
            website_discoverer: Website discovery system
            linkedin_researcher: LinkedIn research system
            contact_validator: Contact validation system
        """
        self.config = config or EnrichmentConfig()
        
        # Initialize individual systems
        self.name_classifier = name_classifier or NameClassifier(enable_llm=False)
        self.website_discoverer = website_discoverer or WebsiteDiscoverer()
        self.linkedin_researcher = linkedin_researcher or LinkedInResearcher()
        self.contact_validator = contact_validator or ContactValidator()
        
        # Statistics tracking
        self.stats = EnrichmentStats()
        
        # Performance tracking
        self.total_processed = 0
        self.start_time = datetime.utcnow()
    
    async def enrich_lead(self, lead: Lead) -> EnrichedLead:
        """Complete lead enrichment using all available systems.
        
        Args:
            lead: Lead to enrich
            
        Returns:
            EnrichedLead with all available enrichment data
            
        Raises:
            EnrichmentError: If enrichment fails and fail_fast is enabled
        """
        start_time = time.time()
        
        try:
            # Perform enrichment with timeout
            result = await asyncio.wait_for(
                self._perform_enrichment(lead, start_time),
                timeout=self.config.max_enrichment_time_seconds
            )
            
            # Update statistics
            self.stats.update_with_result(result)
            
            if result.enriched_lead:
                return result.enriched_lead
            else:
                # Create minimal enriched lead with errors
                enriched = EnrichedLead(
                    original_lead=lead,
                    error_messages=result.errors
                )
                if self.config.fail_fast:
                    raise EnrichmentError(f"Enrichment failed: {result.errors}")
                return enriched
                
        except asyncio.TimeoutError:
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Create timeout result
            timeout_result = EnrichmentResult(
                lead=lead,
                total_processing_time_ms=processing_time_ms,
                errors=[f"Enrichment timeout after {self.config.max_enrichment_time_seconds}s"]
            )
            
            self.stats.update_with_result(timeout_result)
            
            # Return minimal enriched lead
            enriched = EnrichedLead(
                original_lead=lead,
                error_messages=timeout_result.errors
            )
            
            if self.config.fail_fast:
                raise EnrichmentError(f"Enrichment timeout: {self.config.max_enrichment_time_seconds}s")
            
            return enriched
    
    async def _perform_enrichment(self, lead: Lead, start_time: float) -> EnrichmentResult:
        """Perform the actual enrichment workflow."""
        
        result = EnrichmentResult(lead=lead)
        enriched = EnrichedLead(original_lead=lead)
        
        # 1. Director name classification (core requirement)
        if self.config.enable_classification:
            classification_start = time.time()
            try:
                classification = await asyncio.wait_for(
                    self.name_classifier.classify_name(lead.director_name),
                    timeout=self.config.classification_timeout
                )
                
                if classification and classification.confidence >= self.config.min_classification_confidence:
                    enriched.classification = classification
                    result.classification_success = True
                else:
                    result.warnings.append("Classification confidence below threshold")
                    
            except Exception as e:
                result.errors.append(f"Classification failed: {str(e)}")
            
            result.classification_time_ms = (time.time() - classification_start) * 1000
        
        # 2. Website discovery
        if self.config.enable_website_discovery:
            website_start = time.time()
            try:
                website_result = await asyncio.wait_for(
                    self.website_discoverer.discover_website(
                        company_name=lead.entity_name,
                        province=lead.registered_address_province,
                        existing_contact=lead.email_address
                    ),
                    timeout=self.config.website_discovery_timeout
                )
                
                if website_result.discovered_url and website_result.confidence >= self.config.min_website_confidence:
                    enriched.website_url = website_result.discovered_url
                    enriched.website_found = True
                    result.website_discovery_success = True
                else:
                    result.warnings.append("Website discovery confidence below threshold or no URL found")
                    
            except Exception as e:
                result.errors.append(f"Website discovery failed: {str(e)}")
            
            result.website_discovery_time_ms = (time.time() - website_start) * 1000
        
        # 3. LinkedIn research (with compliance)
        if self.config.enable_linkedin_research:
            linkedin_start = time.time()
            try:
                linkedin_result = await asyncio.wait_for(
                    self.linkedin_researcher.research_director_profile(
                        director_name=lead.director_name,
                        company_name=lead.entity_name,
                        province=lead.registered_address_province
                    ),
                    timeout=self.config.linkedin_research_timeout
                )
                
                if linkedin_result.profile_found and linkedin_result.confidence >= self.config.min_linkedin_confidence:
                    enriched.linkedin_profile = linkedin_result.profile_url
                    enriched.linkedin_found = True
                    result.linkedin_research_success = True
                else:
                    result.warnings.append("LinkedIn research confidence below threshold or no profile found")
                    
            except Exception as e:
                result.errors.append(f"LinkedIn research failed: {str(e)}")
            
            result.linkedin_research_time_ms = (time.time() - linkedin_start) * 1000
        
        # 4. Contact validation
        if self.config.enable_contact_validation:
            contact_start = time.time()
            try:
                contact_result = await asyncio.wait_for(
                    self.contact_validator.validate_contact_completeness(lead),
                    timeout=self.config.contact_validation_timeout
                )
                
                if contact_result.overall_quality_score >= self.config.min_contact_quality:
                    enriched.contact_quality_score = contact_result.overall_quality_score * 100
                    result.contact_validation_success = True
                else:
                    result.warnings.append("Contact validation quality below threshold")
                    
            except Exception as e:
                result.errors.append(f"Contact validation failed: {str(e)}")
            
            result.contact_validation_time_ms = (time.time() - contact_start) * 1000
        
        # Calculate overall metrics
        result.total_processing_time_ms = (time.time() - start_time) * 1000
        
        # Calculate data richness score
        data_richness = 0.0
        max_score = 0.0
        
        if enriched.classification:
            data_richness += 25  # Classification worth 25 points
        max_score += 25
        
        if enriched.website_found:
            data_richness += 25  # Website worth 25 points
        max_score += 25
        
        if enriched.linkedin_found:
            data_richness += 25  # LinkedIn worth 25 points
        max_score += 25
        
        if enriched.contact_quality_score > 0:
            data_richness += 25  # Contact validation worth 25 points
        max_score += 25
        
        enriched.data_richness_score = (data_richness / max_score) * 100 if max_score > 0 else 0
        result.data_richness_score = enriched.data_richness_score
        
        # Calculate overall confidence
        confidences = []
        if enriched.classification:
            confidences.append(enriched.classification.confidence)
        if enriched.website_found:
            confidences.append(0.8)  # Default website confidence
        if enriched.linkedin_found:
            confidences.append(0.7)  # Default LinkedIn confidence
        if enriched.contact_quality_score > 0:
            confidences.append(enriched.contact_quality_score / 100)
        
        enriched.confidence_level = sum(confidences) / len(confidences) if confidences else 0.0
        result.overall_confidence = enriched.confidence_level
        
        # Calculate priority score (business logic can be customized)
        priority_score = 0.0
        
        # Classification contributes 40%
        if enriched.classification:
            # Adjust scoring based on business requirements
            ethnicity_scores = {
                "african": 30,  # High priority for BEE compliance
                "indian": 25,
                "cape_malay": 25,
                "coloured": 25,
                "white": 15,  # Lower priority
                "unknown": 10
            }
            priority_score += ethnicity_scores.get(enriched.classification.ethnicity.value, 10) * enriched.classification.confidence
        
        # Data richness contributes 30%
        priority_score += (enriched.data_richness_score / 100) * 30
        
        # Contact quality contributes 30%
        priority_score += (enriched.contact_quality_score / 100) * 30
        
        enriched.priority_score = min(100, priority_score)
        
        # Check if enrichment met minimum requirements
        if self.config.require_classification and not result.classification_success:
            result.errors.append("Required classification failed")
        
        if self.config.require_website and not result.website_discovery_success:
            result.errors.append("Required website discovery failed")
        
        if self.config.require_linkedin and not result.linkedin_research_success:
            result.errors.append("Required LinkedIn research failed")
        
        if self.config.require_contact_validation and not result.contact_validation_success:
            result.errors.append("Required contact validation failed")
        
        # Set enriched lead if minimum requirements met
        if not result.errors or not self.config.fail_fast:
            enriched.error_messages = result.errors + result.warnings
            result.enriched_lead = enriched
        
        return result
    
    async def enrich_batch(
        self,
        leads: List[Lead],
        batch_size: Optional[int] = None
    ) -> List[EnrichedLead]:
        """Batch enrichment with optimal async optimization patterns.
        
        Args:
            leads: List of leads to enrich
            batch_size: Optional batch size override
            
        Returns:
            List of enriched leads
        """
        batch_size = batch_size or self.config.batch_size
        semaphore = asyncio.Semaphore(self.config.max_concurrent_leads)
        
        async def enrich_with_semaphore(lead: Lead) -> EnrichedLead:
            async with semaphore:
                return await self.enrich_lead(lead)
        
        # Process in batches to control concurrency
        all_results = []
        
        for i in range(0, len(leads), batch_size):
            batch = leads[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = [enrich_with_semaphore(lead) for lead in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle any exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    # Create error enriched lead
                    error_enriched = EnrichedLead(
                        original_lead=batch[j],
                        error_messages=[f"Enrichment failed: {str(result)}"]
                    )
                    all_results.append(error_enriched)
                else:
                    all_results.append(result)
        
        return all_results
    
    def get_enrichment_statistics(self) -> EnrichmentStats:
        """Provide enrichment performance and success statistics."""
        return self.stats
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get information about the enrichment system configuration."""
        return {
            "config": self.config.dict(),
            "services": {
                "classification": "enabled" if self.config.enable_classification else "disabled",
                "website_discovery": "enabled" if self.config.enable_website_discovery else "disabled",
                "linkedin_research": "enabled" if self.config.enable_linkedin_research else "disabled",
                "contact_validation": "enabled" if self.config.enable_contact_validation else "disabled",
            },
            "performance_targets": {
                "max_enrichment_time": f"{self.config.max_enrichment_time_seconds}s",
                "max_concurrent_leads": self.config.max_concurrent_leads,
                "batch_size": self.config.batch_size,
            },
            "quality_thresholds": {
                "classification_confidence": self.config.min_classification_confidence,
                "website_confidence": self.config.min_website_confidence,
                "linkedin_confidence": self.config.min_linkedin_confidence,
                "contact_quality": self.config.min_contact_quality,
            },
            "statistics": self.stats.dict(),
        }
    
    def reset_stats(self) -> EnrichmentStats:
        """Reset statistics and return previous stats."""
        old_stats = self.stats
        self.stats = EnrichmentStats()
        self.total_processed = 0
        self.start_time = datetime.utcnow()
        return old_stats