"""Classification data models and types.

This module defines the data models used throughout the classification system,
including classification results, confidence scores, and integration models.
These models ensure type safety and consistent data handling across all
classification components.

Key Features:
- Pydantic models for validation and serialization
- Confidence scoring with detailed breakdowns
- Integration models for cache and API communication
- Phonetic matching result structures
- LLM classification response models

Architecture Decision: Uses Pydantic v2 for maximum performance and validation,
with custom validators for South African naming patterns and business rules.

Integration: Core data structures used by all classification modules and
cached by Developer A's caching system.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from .dictionaries import EthnicityType


class ConfidenceLevel(Enum):
    """Confidence levels for classification results."""
    VERY_HIGH = "very_high"  # 95-100%
    HIGH = "high"            # 85-95%
    MEDIUM = "medium"        # 70-85%
    LOW = "low"              # 50-70%
    VERY_LOW = "very_low"    # 0-50%


class ClassificationMethod(Enum):
    """Method used for classification."""
    RULE_BASED = "rule_based"
    PHONETIC = "phonetic"
    LLM = "llm"
    CACHE = "cache"
    MANUAL = "manual"


class Classification(BaseModel):
    """Complete classification result for a name."""
    
    name: str = Field(..., description="Original name that was classified")
    ethnicity: EthnicityType = Field(..., description="Classified ethnicity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    confidence_level: Optional[ConfidenceLevel] = Field(default=None, description="Human-readable confidence level")
    method: ClassificationMethod = Field(..., description="Classification method used")
    
    # Method-specific details
    rule_details: Optional['RuleClassificationDetails'] = None
    phonetic_details: Optional['PhoneticClassificationDetails'] = None
    llm_details: Optional['LLMClassificationDetails'] = None
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[float] = None
    alternative_classifications: List['AlternativeClassification'] = Field(default_factory=list)
    
    @model_validator(mode='after')
    def set_confidence_level(self):
        """Set confidence level based on confidence score if not provided."""
        if self.confidence_level is None:
            if self.confidence >= 0.95:
                self.confidence_level = ConfidenceLevel.VERY_HIGH
            elif self.confidence >= 0.85:
                self.confidence_level = ConfidenceLevel.HIGH
            elif self.confidence >= 0.70:
                self.confidence_level = ConfidenceLevel.MEDIUM
            elif self.confidence >= 0.50:
                self.confidence_level = ConfidenceLevel.LOW
            else:
                self.confidence_level = ConfidenceLevel.VERY_LOW
        return self
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate and normalize the name."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class AlternativeClassification(BaseModel):
    """Alternative classification possibility with lower confidence."""
    
    ethnicity: EthnicityType
    confidence: float = Field(..., ge=0.0, le=1.0)
    method: ClassificationMethod
    reasoning: Optional[str] = None


class RuleClassificationDetails(BaseModel):
    """Details for rule-based classification."""
    
    matched_dictionary: EthnicityType
    matched_name: str
    dictionary_confidence: float
    linguistic_origin: Optional[str] = None
    regional_pattern: Optional[str] = None
    name_type: str = "surname"  # "forename", "surname", "both"
    special_heuristic_applied: Optional[str] = None  # e.g., "month_surname"
    conflicting_matches: List[Dict[str, Any]] = Field(default_factory=list)


class PhoneticMatch(BaseModel):
    """A single phonetic match result."""
    
    matched_name: str
    matched_ethnicity: EthnicityType
    algorithm: str  # "soundex", "metaphone", etc.
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    phonetic_code: str
    original_confidence: float  # Original confidence of the matched name


class PhoneticClassificationDetails(BaseModel):
    """Details for phonetic classification."""
    
    phonetic_codes: Dict[str, str] = Field(..., description="Generated phonetic codes")
    matches: List[PhoneticMatch] = Field(..., description="All phonetic matches found")
    algorithm_weights: Dict[str, float] = Field(..., description="Weights used for algorithms")
    consensus_score: float = Field(..., description="Agreement between algorithms")
    top_algorithm: str = Field(..., description="Algorithm with highest confidence")
    cached_names_searched: int = Field(..., description="Number of cached names searched")


class LLMClassificationDetails(BaseModel):
    """Details for LLM classification."""
    
    model_used: str = Field(..., description="LLM model identifier")
    prompt_tokens: int = Field(..., description="Tokens in prompt")
    completion_tokens: int = Field(..., description="Tokens in completion")
    total_cost: Optional[float] = None
    few_shot_examples: List[Dict[str, Any]] = Field(default_factory=list)
    raw_response: Optional[str] = None
    reasoning: Optional[str] = None
    fallback_used: bool = False
    retry_count: int = 0


class ClassificationRequest(BaseModel):
    """Request for name classification."""
    
    name: str = Field(..., description="Name to classify")
    require_high_confidence: bool = Field(default=False, description="Require >85% confidence")
    use_cache: bool = Field(default=True, description="Check cache first")
    use_phonetic: bool = Field(default=True, description="Use phonetic matching")
    use_llm: bool = Field(default=True, description="Use LLM as fallback")
    context: Optional[Dict[str, Any]] = None  # Additional context like company name
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate the input name."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()


class BatchClassificationRequest(BaseModel):
    """Request for batch classification of multiple names."""
    
    names: List[str] = Field(..., min_items=1, max_items=1000)
    batch_size: int = Field(default=20, ge=1, le=50)
    require_high_confidence: bool = Field(default=False)
    use_cache: bool = Field(default=True)
    use_phonetic: bool = Field(default=True)
    use_llm: bool = Field(default=True)
    
    @field_validator('names')
    @classmethod
    def validate_names(cls, v):
        """Validate the list of names."""
        validated_names = []
        for name in v:
            if name and name.strip() and len(name.strip()) >= 2:
                validated_names.append(name.strip())
        
        if not validated_names:
            raise ValueError("No valid names provided")
        
        return validated_names


class ClassificationCache(BaseModel):
    """Cache entry for classification results."""
    
    name: str
    classification: Classification
    expires_at: datetime
    hit_count: int = 1
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def ttl_seconds(self) -> int:
        """Get time-to-live in seconds."""
        if self.is_expired:
            return 0
        return int((self.expires_at - datetime.utcnow()).total_seconds())


class ClassificationStats(BaseModel):
    """Statistics for classification performance."""
    
    total_classifications: int = 0
    method_breakdown: Dict[ClassificationMethod, int] = Field(default_factory=dict)
    confidence_breakdown: Dict[ConfidenceLevel, int] = Field(default_factory=dict)
    ethnicity_breakdown: Dict[EthnicityType, int] = Field(default_factory=dict)
    average_confidence: float = 0.0
    average_processing_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    llm_usage_rate: float = 0.0
    
    def update_with_classification(self, classification: Classification, from_cache: bool = False):
        """Update statistics with a new classification."""
        self.total_classifications += 1
        
        # Update method breakdown
        method = ClassificationMethod.CACHE if from_cache else classification.method
        self.method_breakdown[method] = self.method_breakdown.get(method, 0) + 1
        
        # Update confidence breakdown
        self.confidence_breakdown[classification.confidence_level] = \
            self.confidence_breakdown.get(classification.confidence_level, 0) + 1
        
        # Update ethnicity breakdown
        self.ethnicity_breakdown[classification.ethnicity] = \
            self.ethnicity_breakdown.get(classification.ethnicity, 0) + 1
        
        # Recalculate averages (simple running average)
        total = self.total_classifications
        self.average_confidence = ((self.average_confidence * (total - 1)) + 
                                 classification.confidence) / total
        
        if classification.processing_time_ms:
            self.average_processing_time_ms = ((self.average_processing_time_ms * (total - 1)) + 
                                             classification.processing_time_ms) / total
        
        # Calculate cache hit rate
        cache_hits = self.method_breakdown.get(ClassificationMethod.CACHE, 0)
        self.cache_hit_rate = cache_hits / total
        
        # Calculate LLM usage rate
        llm_uses = self.method_breakdown.get(ClassificationMethod.LLM, 0)
        self.llm_usage_rate = llm_uses / total


class MultiWordNameAnalysis(BaseModel):
    """Analysis of multi-word names for priority classification."""
    
    original_name: str
    name_parts: List[str]
    individual_classifications: List[Classification]
    priority_classification: Classification  # Based on least European element
    conflicting_ethnicities: bool
    european_elements: List[str] = Field(default_factory=list)
    non_european_elements: List[str] = Field(default_factory=list)
    reasoning: str


class ValidationResult(BaseModel):
    """Result of name validation before classification."""
    
    original_name: str
    normalized_name: str
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    suggested_corrections: List[str] = Field(default_factory=list)
    name_parts: List[str] = Field(default_factory=list)
    is_multi_word: bool = False


# Update forward references
Classification.model_rebuild()
AlternativeClassification.model_rebuild()
RuleClassificationDetails.model_rebuild()
PhoneticClassificationDetails.model_rebuild()
LLMClassificationDetails.model_rebuild()