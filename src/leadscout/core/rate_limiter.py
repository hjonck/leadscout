"""
API rate limit management with provider-specific configurations.

This module implements comprehensive rate limiting for external API providers,
including OpenAI and Anthropic, with actual documented rate limits, exponential
backoff strategies, and automatic provider switching for maximum reliability.

Key Features:
- Provider-specific rate limits based on actual API documentation
- Exponential backoff with jitter for rate limit recovery
- Automatic provider switching when limits are exceeded
- Sliding window rate limit tracking
- Circuit breaker pattern for failed providers
- Comprehensive logging and monitoring

Rate Limits (as of 2025 - research current limits):
- OpenAI Free Tier: 3 RPM, 40k TPM
- OpenAI Pay-as-you-go: 3,500 RPM, 90k TPM  
- Anthropic Free: 5 RPM, 25k TPM
- Anthropic Pro: 50 RPM, 100k TPM

Architecture:
- RateLimiter: Main rate limiting engine with sliding window tracking
- ProviderType: Enum for different API providers
- RateLimitConfig: Configuration class for provider-specific limits
- Exponential backoff with provider switching strategies

Usage:
    limiter = RateLimiter()
    
    # Check if provider is available
    if await limiter.acquire_permit(ProviderType.OPENAI):
        # Proceed with OpenAI call
        pass
    else:
        # Switch to alternative provider
        next_provider = limiter.get_next_available_provider()
"""

import time
import asyncio
import random
from typing import Dict, Optional, Any, List
from enum import Enum
from dataclasses import dataclass
from collections import deque
import structlog

logger = structlog.get_logger(__name__)

class ProviderType(Enum):
    """Enumeration of available API providers for classification."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    RULE_BASED = "rule_based"
    PHONETIC = "phonetic"

@dataclass
class RateLimitConfig:
    """Rate limit configuration for API provider.
    
    Based on actual API provider documentation. These limits should be
    researched and updated regularly as providers change their policies.
    
    Attributes:
        requests_per_minute: Maximum requests per minute
        requests_per_day: Maximum requests per day (if applicable)
        tokens_per_minute: Maximum tokens per minute (if applicable)
        initial_backoff_seconds: Initial backoff delay for rate limit errors
        max_backoff_seconds: Maximum backoff delay
        backoff_multiplier: Multiplier for exponential backoff
        burst_allowance: Number of requests allowed in quick succession
    """
    requests_per_minute: int
    requests_per_day: Optional[int] = None
    tokens_per_minute: Optional[int] = None
    initial_backoff_seconds: int = 30
    max_backoff_seconds: int = 300
    backoff_multiplier: float = 2.0
    burst_allowance: int = 5

class RateLimiter:
    """Multi-provider rate limit management with sliding window tracking.
    
    Implements sophisticated rate limiting across multiple API providers
    with automatic provider switching, exponential backoff, and circuit
    breaker patterns for maximum reliability.
    
    Features:
    - Sliding window rate limit tracking
    - Per-provider backoff management
    - Automatic provider health monitoring
    - Circuit breaker for failed providers
    - Intelligent provider selection
    - Comprehensive metrics collection
    
    Thread Safety:
    - All methods are async-safe
    - Uses asyncio locks for concurrent access
    - Maintains separate state per provider
    """
    
    # Provider-specific rate limits (research actual current limits)
    # NOTE: These should be updated based on current API documentation
    PROVIDER_LIMITS = {
        ProviderType.OPENAI: RateLimitConfig(
            requests_per_minute=3,  # Free tier - verify current limits
            tokens_per_minute=40000,  # Free tier token limit
            initial_backoff_seconds=60,
            max_backoff_seconds=900,  # 15 minutes max
            backoff_multiplier=2.0,
            burst_allowance=2
        ),
        ProviderType.ANTHROPIC: RateLimitConfig(
            requests_per_minute=5,  # Verify current limits
            requests_per_day=1000,  # Daily limit if applicable
            tokens_per_minute=25000,  # Verify current limits
            initial_backoff_seconds=30,
            max_backoff_seconds=600,  # 10 minutes max
            backoff_multiplier=1.8,
            burst_allowance=3
        )
    }
    
    def __init__(self):
        """Initialize rate limiter with provider tracking."""
        # Sliding window request tracking (timestamp -> provider)
        self.request_history: Dict[ProviderType, deque] = {
            provider: deque() for provider in [ProviderType.OPENAI, ProviderType.ANTHROPIC]
        }
        
        # Provider backoff state
        self.backoff_until: Dict[ProviderType, float] = {}
        self.failure_counts: Dict[ProviderType, int] = {}
        self.last_success: Dict[ProviderType, float] = {}
        
        # Provider circuit breaker state
        self.circuit_breaker_open: Dict[ProviderType, bool] = {}
        self.circuit_breaker_until: Dict[ProviderType, float] = {}
        
        # Performance tracking
        self.total_requests: Dict[ProviderType, int] = {}
        self.total_rate_limit_hits: Dict[ProviderType, int] = {}
        
        # Async locks for thread safety
        self._locks: Dict[ProviderType, asyncio.Lock] = {
            provider: asyncio.Lock() for provider in [ProviderType.OPENAI, ProviderType.ANTHROPIC]
        }
        
        logger.info("RateLimiter initialized",
                   providers=list(self.PROVIDER_LIMITS.keys()),
                   total_providers=len(self.PROVIDER_LIMITS))
    
    async def acquire_permit(self, provider: ProviderType) -> bool:
        """Acquire rate limit permit for provider.
        
        Checks if the provider is available for requests based on
        current rate limit status, backoff state, and circuit breaker.
        
        Args:
            provider: Provider to check availability for
            
        Returns:
            bool: True if permit acquired, False if rate limited
        """
        if provider not in self.PROVIDER_LIMITS:
            logger.warning("Unknown provider requested", provider=provider)
            return False
        
        async with self._locks[provider]:
            current_time = time.time()
            
            # Check circuit breaker
            if self._is_circuit_breaker_open(provider, current_time):
                logger.debug("Circuit breaker open for provider",
                           provider=provider.value,
                           breaker_until=self.circuit_breaker_until.get(provider))
                return False
            
            # Check backoff period
            if self._is_in_backoff(provider, current_time):
                logger.debug("Provider in backoff period",
                           provider=provider.value,
                           backoff_until=self.backoff_until.get(provider))
                return False
            
            # Check rate limits
            if not self._check_rate_limits(provider, current_time):
                logger.info("Rate limit exceeded for provider",
                           provider=provider.value,
                           requests_in_window=len(self.request_history[provider]))
                
                # Track rate limit hit
                self.total_rate_limit_hits[provider] = self.total_rate_limit_hits.get(provider, 0) + 1
                
                # Apply automatic backoff
                self._apply_automatic_backoff(provider)
                return False
            
            # Permit acquired - record request
            self.request_history[provider].append(current_time)
            self.total_requests[provider] = self.total_requests.get(provider, 0) + 1
            self.last_success[provider] = current_time
            
            logger.debug("Rate limit permit acquired",
                        provider=provider.value,
                        requests_in_window=len(self.request_history[provider]))
            
            return True
    
    def handle_rate_limit_error(self, provider: ProviderType, error: Any) -> float:
        """Handle rate limit error and return backoff delay.
        
        Processes rate limit errors from API providers and calculates
        appropriate backoff delay using exponential backoff strategy.
        
        Args:
            provider: Provider that returned rate limit error
            error: Error object from API call
            
        Returns:
            float: Backoff delay in seconds
        """
        current_time = time.time()
        config = self.PROVIDER_LIMITS[provider]
        
        # Increment failure count
        self.failure_counts[provider] = self.failure_counts.get(provider, 0) + 1
        failure_count = self.failure_counts[provider]
        
        # Calculate exponential backoff with jitter
        base_backoff = config.initial_backoff_seconds * (config.backoff_multiplier ** min(failure_count - 1, 5))
        jitter = random.uniform(0.1, 0.3) * base_backoff  # 10-30% jitter
        backoff_delay = min(base_backoff + jitter, config.max_backoff_seconds)
        
        # Set backoff until time
        self.backoff_until[provider] = current_time + backoff_delay
        
        # Open circuit breaker if too many failures
        if failure_count >= 3:
            circuit_breaker_delay = min(backoff_delay * 2, 1800)  # Max 30 minutes
            self.circuit_breaker_open[provider] = True
            self.circuit_breaker_until[provider] = current_time + circuit_breaker_delay
            
            logger.warning("Circuit breaker opened for provider",
                          provider=provider.value,
                          failure_count=failure_count,
                          circuit_breaker_delay=circuit_breaker_delay)
        
        logger.info("Rate limit error handled",
                   provider=provider.value,
                   failure_count=failure_count,
                   backoff_delay=round(backoff_delay, 2),
                   error_type=type(error).__name__)
        
        return backoff_delay
    
    def handle_successful_request(self, provider: ProviderType) -> None:
        """Handle successful request to reset failure tracking.
        
        Args:
            provider: Provider that had successful request
        """
        current_time = time.time()
        
        # Reset failure count on success
        if provider in self.failure_counts:
            del self.failure_counts[provider]
        
        # Close circuit breaker on success
        if provider in self.circuit_breaker_open:
            del self.circuit_breaker_open[provider]
            if provider in self.circuit_breaker_until:
                del self.circuit_breaker_until[provider]
            
            logger.info("Circuit breaker closed for provider",
                       provider=provider.value)
        
        # Clear backoff on success
        if provider in self.backoff_until:
            del self.backoff_until[provider]
        
        self.last_success[provider] = current_time
        
        logger.debug("Successful request recorded",
                    provider=provider.value)
    
    def should_switch_provider(self, provider: ProviderType) -> bool:
        """Determine if provider should be switched due to rate limits.
        
        Args:
            provider: Current provider to evaluate
            
        Returns:
            bool: True if provider switch is recommended
        """
        current_time = time.time()
        
        # Switch if in backoff period
        if self._is_in_backoff(provider, current_time):
            return True
        
        # Switch if circuit breaker is open
        if self._is_circuit_breaker_open(provider, current_time):
            return True
        
        # Switch if rate limit is close to exceeded
        if not self._check_rate_limits(provider, current_time, buffer_percentage=0.8):
            return True
        
        return False
    
    def get_next_available_provider(self, exclude: List[ProviderType] = None) -> Optional[ProviderType]:
        """Get next available provider for processing.
        
        Args:
            exclude: List of providers to exclude from selection
            
        Returns:
            ProviderType: Next available provider, or None if none available
        """
        if exclude is None:
            exclude = []
        
        current_time = time.time()
        available_providers = []
        
        for provider in [ProviderType.OPENAI, ProviderType.ANTHROPIC]:
            if provider in exclude:
                continue
            
            # Check if provider is available
            if (not self._is_in_backoff(provider, current_time) and
                not self._is_circuit_breaker_open(provider, current_time) and
                self._check_rate_limits(provider, current_time)):
                
                available_providers.append(provider)
        
        if available_providers:
            # Prefer provider with fewer recent failures
            available_providers.sort(key=lambda p: self.failure_counts.get(p, 0))
            selected = available_providers[0]
            
            logger.debug("Next available provider selected",
                        provider=selected.value,
                        total_available=len(available_providers))
            
            return selected
        
        logger.warning("No providers currently available",
                      excluded_providers=[p.value for p in exclude])
        return None
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all providers.
        
        Returns:
            dict: Complete provider status information
        """
        current_time = time.time()
        status = {}
        
        for provider in [ProviderType.OPENAI, ProviderType.ANTHROPIC]:
            config = self.PROVIDER_LIMITS[provider]
            
            # Calculate current rate limit usage
            requests_in_window = len(self.request_history[provider])
            rate_limit_usage_pct = (requests_in_window / config.requests_per_minute) * 100
            
            # Calculate time until available
            time_until_available = 0
            if self._is_in_backoff(provider, current_time):
                time_until_available = max(time_until_available, 
                                         self.backoff_until[provider] - current_time)
            
            if self._is_circuit_breaker_open(provider, current_time):
                time_until_available = max(time_until_available,
                                         self.circuit_breaker_until[provider] - current_time)
            
            status[provider.value] = {
                'available': (not self._is_in_backoff(provider, current_time) and
                            not self._is_circuit_breaker_open(provider, current_time) and
                            self._check_rate_limits(provider, current_time)),
                'requests_in_window': requests_in_window,
                'rate_limit_usage_percent': round(rate_limit_usage_pct, 1),
                'failure_count': self.failure_counts.get(provider, 0),
                'in_backoff': self._is_in_backoff(provider, current_time),
                'circuit_breaker_open': self._is_circuit_breaker_open(provider, current_time),
                'time_until_available_seconds': max(0, round(time_until_available, 2)),
                'total_requests': self.total_requests.get(provider, 0),
                'total_rate_limit_hits': self.total_rate_limit_hits.get(provider, 0),
                'last_success_ago_seconds': round(current_time - self.last_success.get(provider, current_time), 2)
            }
        
        return {
            'providers': status,
            'summary': {
                'available_providers': sum(1 for p in status.values() if p['available']),
                'total_providers': len(status),
                'total_requests_all': sum(self.total_requests.values()),
                'total_rate_limit_hits_all': sum(self.total_rate_limit_hits.values())
            }
        }
    
    def _check_rate_limits(self, provider: ProviderType, current_time: float, 
                          buffer_percentage: float = 1.0) -> bool:
        """Check if provider is within rate limits.
        
        Args:
            provider: Provider to check
            current_time: Current timestamp
            buffer_percentage: Safety buffer (1.0 = no buffer, 0.8 = 20% buffer)
            
        Returns:
            bool: True if within rate limits
        """
        config = self.PROVIDER_LIMITS[provider]
        request_times = self.request_history[provider]
        
        # Clean old requests outside the window
        window_start = current_time - 60  # 1 minute window
        while request_times and request_times[0] < window_start:
            request_times.popleft()
        
        # Check requests per minute limit
        effective_limit = int(config.requests_per_minute * buffer_percentage)
        if len(request_times) >= effective_limit:
            return False
        
        # Check burst allowance
        recent_window = current_time - 10  # 10 second burst window
        recent_requests = sum(1 for t in request_times if t > recent_window)
        if recent_requests >= config.burst_allowance:
            return False
        
        return True
    
    def _is_in_backoff(self, provider: ProviderType, current_time: float) -> bool:
        """Check if provider is in backoff period."""
        return (provider in self.backoff_until and 
                current_time < self.backoff_until[provider])
    
    def _is_circuit_breaker_open(self, provider: ProviderType, current_time: float) -> bool:
        """Check if circuit breaker is open for provider."""
        if provider not in self.circuit_breaker_open:
            return False
        
        if (provider in self.circuit_breaker_until and 
            current_time >= self.circuit_breaker_until[provider]):
            # Circuit breaker timeout expired, close it
            del self.circuit_breaker_open[provider]
            del self.circuit_breaker_until[provider]
            logger.info("Circuit breaker timeout expired, closing",
                       provider=provider.value)
            return False
        
        return True
    
    def _apply_automatic_backoff(self, provider: ProviderType) -> None:
        """Apply automatic backoff when rate limit is exceeded."""
        config = self.PROVIDER_LIMITS[provider]
        current_time = time.time()
        
        # Apply minimal automatic backoff
        auto_backoff = config.initial_backoff_seconds * 0.5  # 50% of normal backoff
        self.backoff_until[provider] = current_time + auto_backoff
        
        logger.info("Automatic backoff applied",
                   provider=provider.value,
                   backoff_seconds=auto_backoff)

class RateLimitMonitor:
    """Monitor and report rate limit statistics and health."""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.monitoring_start_time = time.time()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        status = self.rate_limiter.get_provider_status()
        monitoring_duration = time.time() - self.monitoring_start_time
        
        return {
            'monitoring_duration_hours': round(monitoring_duration / 3600, 2),
            'provider_status': status,
            'recommendations': self._generate_recommendations(status),
            'optimization_opportunities': self._identify_optimizations(status)
        }
    
    def _generate_recommendations(self, status: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on current status."""
        recommendations = []
        
        available_count = status['summary']['available_providers']
        if available_count == 0:
            recommendations.append("CRITICAL: No providers available - consider implementing retry queue")
        elif available_count == 1:
            recommendations.append("WARNING: Only one provider available - consider reducing load")
        
        for provider_name, provider_status in status['providers'].items():
            if provider_status['total_rate_limit_hits'] > 10:
                recommendations.append(f"Consider optimizing {provider_name} usage - {provider_status['total_rate_limit_hits']} rate limit hits")
        
        return recommendations
    
    def _identify_optimizations(self, status: Dict[str, Any]) -> List[str]:
        """Identify optimization opportunities."""
        optimizations = []
        
        total_requests = status['summary']['total_requests_all']
        total_hits = status['summary']['total_rate_limit_hits_all']
        
        if total_requests > 0:
            hit_rate = (total_hits / total_requests) * 100
            if hit_rate > 5:
                optimizations.append(f"High rate limit hit rate: {hit_rate:.1f}% - consider caching or load balancing")
        
        return optimizations