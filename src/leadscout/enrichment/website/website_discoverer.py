"""Website discovery and validation system for lead enrichment.

Uses multiple strategies to find and validate company websites,
building on the proven async patterns from the classification system.

Key Features:
- Multiple discovery strategies (domain patterns, search engines, email domains)
- Async processing with timeout management
- Confidence scoring similar to classification system
- Website validation with quality assessment
- Caching integration for performance optimization

Architecture Decision: Uses the same async/timeout patterns as the classification
system for consistency and proven reliability.

Developer B - Classification & Enrichment Specialist
"""

import asyncio
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from pydantic import ValidationError

from ...core.exceptions import LeadScoutError
from .models import (
    DiscoveryMethod,
    DomainPattern,
    SearchQuery,
    WebsiteDiscoveryConfig,
    WebsiteDiscoveryResult,
    WebsiteDiscoveryStats,
    WebsiteStatus,
    WebsiteValidationResult,
)


class WebsiteDiscoveryError(LeadScoutError):
    """Errors related to website discovery."""
    pass


class WebsiteDiscoverer:
    """Discover and validate company websites using multiple strategies.
    
    Uses proven async patterns from the classification system to provide
    reliable, fast website discovery with confidence scoring and validation.
    """
    
    def __init__(
        self,
        config: Optional[WebsiteDiscoveryConfig] = None,
        enable_caching: bool = True,
    ):
        """Initialize website discoverer.
        
        Args:
            config: Discovery configuration
            enable_caching: Whether to enable result caching
        """
        self.config = config or WebsiteDiscoveryConfig()
        self.enable_caching = enable_caching
        
        # Statistics tracking (similar to classification system)
        self.stats = WebsiteDiscoveryStats()
        
        # Cache for discovery results (placeholder for Developer A integration)
        self._cache: Dict[str, WebsiteDiscoveryResult] = {}
        
        # HTTP client for website validation
        self._http_client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.request_timeout_seconds),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            verify=False,  # Allow self-signed certificates for validation
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()
    
    async def discover_website(
        self,
        company_name: str,
        province: Optional[str] = None,
        existing_contact: Optional[str] = None
    ) -> WebsiteDiscoveryResult:
        """Discover company website using multiple strategies.
        
        Args:
            company_name: Company name to search for
            province: Optional province for localized search
            existing_contact: Optional existing contact info (email/phone)
            
        Returns:
            WebsiteDiscoveryResult with discovered URL and confidence
            
        Raises:
            WebsiteDiscoveryError: If discovery process fails
        """
        start_time = time.time()
        
        try:
            # Input validation
            if not company_name or not company_name.strip():
                raise WebsiteDiscoveryError("Company name is required")
            
            company_name = company_name.strip()
            cache_key = self._generate_cache_key(company_name, province)
            
            # Check cache first (similar to classification system pattern)
            if self.enable_caching and cache_key in self._cache:
                cached_result = self._cache[cache_key]
                return cached_result
            
            # Try multiple discovery strategies with timeout
            discovery_timeout = self.config.total_discovery_timeout_seconds
            
            try:
                result = await asyncio.wait_for(
                    self._discover_with_strategies(company_name, province, existing_contact),
                    timeout=discovery_timeout
                )
            except asyncio.TimeoutError:
                # Return empty result on timeout
                result = WebsiteDiscoveryResult(
                    company_name=company_name,
                    confidence=0.0,
                )
            
            # Add processing time
            processing_time_ms = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time_ms
            
            # Cache the result
            if self.enable_caching:
                self._cache[cache_key] = result
            
            # Update statistics
            self.stats.update_with_result(result)
            
            return result
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Return error result
            error_result = WebsiteDiscoveryResult(
                company_name=company_name,
                confidence=0.0,
                processing_time_ms=processing_time_ms,
            )
            
            self.stats.update_with_result(error_result)
            return error_result
    
    async def _discover_with_strategies(
        self,
        company_name: str,
        province: Optional[str],
        existing_contact: Optional[str]
    ) -> WebsiteDiscoveryResult:
        """Try multiple discovery strategies in order of priority."""
        
        # Strategy 1: Email domain extraction (highest confidence if available)
        if existing_contact and "@" in existing_contact:
            result = await self._try_email_domain_strategy(company_name, existing_contact)
            if result and result.confidence >= self.config.min_confidence_threshold:
                return result
        
        # Strategy 2: Domain pattern matching (fast and reliable)
        result = await self._try_domain_pattern_strategy(company_name)
        if result and result.confidence >= self.config.min_confidence_threshold:
            return result
        
        # Strategy 3: Search engine discovery (slower but comprehensive)
        if self.config.search_engine_enabled:
            result = await self._try_search_engine_strategy(company_name, province)
            if result and result.confidence >= self.config.min_confidence_threshold:
                return result
        
        # Return best result found or empty result
        return WebsiteDiscoveryResult(
            company_name=company_name,
            confidence=0.0,
        )
    
    async def _try_email_domain_strategy(
        self,
        company_name: str,
        email_address: str
    ) -> Optional[WebsiteDiscoveryResult]:
        """Extract and validate domain from email address."""
        
        try:
            # Extract domain from email
            domain = email_address.split("@")[1].lower()
            
            # Skip common email providers
            common_providers = {
                "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", 
                "webmail.co.za", "mweb.co.za", "telkomsa.net"
            }
            
            if domain in common_providers:
                return None
            
            # Try both http and https
            for protocol in ["https", "http"]:
                url = f"{protocol}://{domain}"
                
                validation_result = await self.validate_website(url)
                
                if validation_result.status == WebsiteStatus.ACTIVE:
                    # Check if domain relates to company
                    relevance_score = self._calculate_relevance_score(
                        company_name, domain, validation_result
                    )
                    
                    if relevance_score >= 0.6:  # Good relevance threshold
                        return WebsiteDiscoveryResult(
                            company_name=company_name,
                            discovered_url=url,
                            confidence=min(0.9, relevance_score + 0.2),  # High confidence for email domains
                            discovery_method=DiscoveryMethod.EMAIL_DOMAIN,
                            validation_result=validation_result,
                        )
                        
                # Try www variant
                www_url = f"{protocol}://www.{domain}"
                validation_result = await self.validate_website(www_url)
                
                if validation_result.status == WebsiteStatus.ACTIVE:
                    relevance_score = self._calculate_relevance_score(
                        company_name, domain, validation_result
                    )
                    
                    if relevance_score >= 0.6:
                        return WebsiteDiscoveryResult(
                            company_name=company_name,
                            discovered_url=www_url,
                            confidence=min(0.9, relevance_score + 0.2),
                            discovery_method=DiscoveryMethod.EMAIL_DOMAIN,
                            validation_result=validation_result,
                        )
            
            return None
            
        except Exception:
            return None
    
    async def _try_domain_pattern_strategy(
        self,
        company_name: str
    ) -> Optional[WebsiteDiscoveryResult]:
        """Try systematic domain patterns for company."""
        
        # Generate domain patterns
        patterns = [
            DomainPattern(pattern="https://{company}.co.za", priority=1),
            DomainPattern(pattern="https://www.{company}.co.za", priority=2),
            DomainPattern(pattern="https://{company}.com", priority=3),
            DomainPattern(pattern="https://www.{company}.com", priority=4),
            DomainPattern(pattern="https://{company}.org", priority=5),
        ]
        
        # Test patterns concurrently
        validation_tasks = []
        urls_to_test = []
        
        for pattern in patterns[:self.config.max_domain_patterns]:
            url = pattern.generate_url(company_name)
            urls_to_test.append((url, pattern.priority))
            validation_tasks.append(self.validate_website(url))
        
        # Wait for validations with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.config.max_concurrent_validations)
        
        async def validate_with_semaphore(task):
            async with semaphore:
                return await task
        
        validation_results = await asyncio.gather(
            *[validate_with_semaphore(task) for task in validation_tasks],
            return_exceptions=True
        )
        
        # Find best result
        best_result = None
        best_score = 0.0
        
        for i, (url, priority) in enumerate(urls_to_test):
            if i >= len(validation_results):
                continue
                
            validation_result = validation_results[i]
            
            if isinstance(validation_result, Exception):
                continue
                
            if validation_result.status == WebsiteStatus.ACTIVE:
                # Calculate confidence based on validation quality and pattern priority
                quality_score = validation_result.overall_quality_score
                priority_score = 1.0 - (priority - 1) * 0.1  # Higher priority = higher score
                confidence = (quality_score * 0.7) + (priority_score * 0.3)
                
                if confidence > best_score:
                    best_score = confidence
                    best_result = WebsiteDiscoveryResult(
                        company_name=company_name,
                        discovered_url=url,
                        confidence=confidence,
                        discovery_method=DiscoveryMethod.DOMAIN_PATTERN,
                        validation_result=validation_result,
                    )
        
        return best_result
    
    async def _try_search_engine_strategy(
        self,
        company_name: str,
        province: Optional[str] = None
    ) -> Optional[WebsiteDiscoveryResult]:
        """Use search engines to find company website.
        
        Note: This is a placeholder implementation. In production,
        you would integrate with search APIs like Google Custom Search.
        """
        
        # Generate search queries
        queries = self._build_search_queries(company_name, province)
        
        # For now, return None as this requires external API integration
        # In production, implement with search API:
        # 1. Execute search queries
        # 2. Extract URLs from search results
        # 3. Validate discovered URLs
        # 4. Return best match with confidence scoring
        
        return None
    
    def _build_search_queries(
        self,
        company_name: str,
        province: Optional[str] = None
    ) -> List[SearchQuery]:
        """Build search queries for website discovery.
        
        Leverages name analysis expertise for query optimization.
        """
        queries = []
        
        # Basic company search
        queries.append(SearchQuery(
            query=f'"{company_name}" website',
            priority=1,
        ))
        
        # Company with location
        if province:
            queries.append(SearchQuery(
                query=f'"{company_name}" {province} website',
                priority=2,
            ))
        
        # Company with South African context
        queries.append(SearchQuery(
            query=f'"{company_name}" South Africa site:co.za',
            priority=3,
        ))
        
        return queries
    
    async def validate_website(self, url: str) -> WebsiteValidationResult:
        """Validate discovered website quality and relevance.
        
        Args:
            url: URL to validate
            
        Returns:
            WebsiteValidationResult with status and quality scores
        """
        start_time = time.time()
        
        try:
            if not self._http_client:
                # Create temporary client if not in context manager
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.config.request_timeout_seconds)
                ) as client:
                    return await self._perform_validation(client, url, start_time)
            else:
                return await self._perform_validation(self._http_client, url, start_time)
                
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            return WebsiteValidationResult(
                url=url,
                status=WebsiteStatus.NOT_FOUND,
                response_time_ms=response_time_ms,
                error_message=str(e),
            )
    
    async def _perform_validation(
        self,
        client: httpx.AsyncClient,
        url: str,
        start_time: float
    ) -> WebsiteValidationResult:
        """Perform the actual website validation."""
        
        try:
            response = await client.get(url, follow_redirects=True)
            response_time_ms = (time.time() - start_time) * 1000
            
            # Determine status
            status = WebsiteStatus.ACTIVE if response.status_code == 200 else WebsiteStatus.INACTIVE
            
            # Check SSL
            ssl_valid = url.startswith("https://") and response.status_code == 200
            
            # Analyze content
            content = response.text.lower() if response.status_code == 200 else ""
            
            business_relevance = self._analyze_business_relevance(content)
            professional_appearance = self._analyze_professional_appearance(content, response)
            has_contact_info = self._has_contact_info(content)
            
            return WebsiteValidationResult(
                url=url,
                status=status,
                response_time_ms=response_time_ms,
                ssl_valid=ssl_valid,
                status_code=response.status_code,
                business_relevance_score=business_relevance,
                professional_appearance=professional_appearance,
                has_contact_info=has_contact_info,
            )
            
        except httpx.TimeoutException:
            response_time_ms = (time.time() - start_time) * 1000
            return WebsiteValidationResult(
                url=url,
                status=WebsiteStatus.TIMEOUT,
                response_time_ms=response_time_ms,
                error_message="Request timeout",
            )
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return WebsiteValidationResult(
                url=url,
                status=WebsiteStatus.NOT_FOUND,
                response_time_ms=response_time_ms,
                error_message=str(e),
            )
    
    def _analyze_business_relevance(self, content: str) -> float:
        """Analyze content for business relevance indicators."""
        if not content:
            return 0.0
        
        business_keywords = [
            "about us", "services", "products", "contact", "company",
            "business", "solutions", "team", "experience", "professional"
        ]
        
        score = 0.0
        for keyword in business_keywords:
            if keyword in content:
                score += 0.1
        
        return min(1.0, score)
    
    def _analyze_professional_appearance(
        self,
        content: str,
        response: httpx.Response
    ) -> float:
        """Analyze website for professional appearance indicators."""
        if not content:
            return 0.0
        
        score = 0.0
        
        # Check for professional elements
        professional_indicators = [
            "<meta", "<!doctype", "css", "javascript", "navigation"
        ]
        
        for indicator in professional_indicators:
            if indicator in content:
                score += 0.2
        
        # Check content length (professional sites have more content)
        if len(content) > 5000:
            score += 0.2
        elif len(content) > 2000:
            score += 0.1
        
        return min(1.0, score)
    
    def _has_contact_info(self, content: str) -> bool:
        """Check if website has contact information."""
        if not content:
            return False
        
        contact_patterns = [
            r'\b\d{10,}\b',  # Phone numbers
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            "contact", "phone", "email", "address"
        ]
        
        for pattern in contact_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def _calculate_relevance_score(
        self,
        company_name: str,
        domain: str,
        validation_result: WebsiteValidationResult
    ) -> float:
        """Calculate how relevant a website is to the company."""
        
        score = 0.0
        company_lower = company_name.lower()
        domain_lower = domain.lower()
        
        # Check domain similarity to company name
        company_words = company_lower.replace("holdings", "").replace("pty", "").replace("ltd", "").split()
        
        for word in company_words:
            if len(word) > 2 and word in domain_lower:
                score += 0.3
        
        # Add validation quality
        score += validation_result.overall_quality_score * 0.4
        
        return min(1.0, score)
    
    def _generate_cache_key(
        self,
        company_name: str,
        province: Optional[str] = None
    ) -> str:
        """Generate cache key for discovery result."""
        key_parts = [company_name.lower().strip()]
        if province:
            key_parts.append(province.lower().strip())
        return "|".join(key_parts)
    
    def get_discovery_stats(self) -> WebsiteDiscoveryStats:
        """Get current discovery statistics."""
        return self.stats
    
    def reset_stats(self) -> WebsiteDiscoveryStats:
        """Reset statistics and return previous stats."""
        old_stats = self.stats
        self.stats = WebsiteDiscoveryStats()
        return old_stats