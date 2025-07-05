"""Name classification models for ethnicity analysis."""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class EthnicityType(str, Enum):
    """Supported ethnicity classifications for South African context.
    
    These categories are designed for business lead prioritization in the
    South African market context.
    """
    
    AFRICAN = "african"
    INDIAN = "indian" 
    COLOURED = "coloured"
    WHITE = "white"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class Classification(BaseModel):
    """Name ethnicity classification result.
    
    Contains the results of ethnicity classification including confidence
    scores and method used for classification.
    
    Attributes:
        name: The original name that was classified
        ethnicity: The predicted ethnicity category
        confidence: Confidence score for the classification (0-1)
        method: Method used for classification (exact, phonetic, llm)
        phonetic_codes: Phonetic algorithm results used
        created_at: When classification was performed
        cached: Whether result came from cache
        
    Example:
        >>> classification = Classification(
        ...     name="Thabo Mthembu",
        ...     ethnicity=EthnicityType.AFRICAN,
        ...     confidence=0.95,
        ...     method="phonetic"
        ... )
    """
    
    name: str = Field(..., min_length=1, max_length=255, description="Original name classified")
    ethnicity: EthnicityType = Field(..., description="Predicted ethnicity category")
    confidence: float = Field(..., ge=0, le=1, description="Classification confidence score")
    method: str = Field(..., description="Classification method used")
    phonetic_codes: Optional[Dict[str, str]] = Field(None, description="Phonetic algorithm results")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Classification timestamp")
    cached: bool = Field(False, description="Whether result came from cache")
    
    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate and clean the name field."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
            
        # Clean up whitespace
        cleaned = ' '.join(v.strip().split())
        
        # Basic validation - ensure it looks like a name
        if len(cleaned) < 2:
            raise ValueError("Name too short for classification")
            
        return cleaned
    
    @validator('method')
    def validate_method(cls, v: str) -> str:
        """Validate classification method."""
        valid_methods = {'exact', 'phonetic', 'llm', 'manual'}
        if v not in valid_methods:
            raise ValueError(f"Invalid classification method. Must be one of: {valid_methods}")
        return v
    
    @validator('confidence')
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence score range."""
        if not 0 <= v <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        return round(v, 3)  # Round to 3 decimal places
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if classification meets high confidence threshold.
        
        Args:
            threshold: Minimum confidence level (default 0.8)
            
        Returns:
            True if confidence meets or exceeds threshold
        """
        return self.confidence >= threshold
    
    def get_confidence_label(self) -> str:
        """Get human-readable confidence label.
        
        Returns:
            String describing confidence level
        """
        if self.confidence >= 0.9:
            return "Very High"
        elif self.confidence >= 0.8:
            return "High"
        elif self.confidence >= 0.6:
            return "Medium"
        elif self.confidence >= 0.4:
            return "Low"
        else:
            return "Very Low"
    
    def to_cache_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for cache storage.
        
        Returns:
            Dictionary representation suitable for caching
        """
        return {
            'name': self.name,
            'ethnicity': self.ethnicity.value,
            'confidence': self.confidence,
            'method': self.method,
            'phonetic_codes': self.phonetic_codes or {},
            'created_at': self.created_at.isoformat(),
            'cached': True
        }
    
    @classmethod
    def from_cache_dict(cls, data: Dict[str, Any]) -> 'Classification':
        """Create Classification from cached dictionary.
        
        Args:
            data: Dictionary from cache storage
            
        Returns:
            Classification instance
        """
        # Parse datetime if it's a string
        created_at = data['created_at']
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
        return cls(
            name=data['name'],
            ethnicity=EthnicityType(data['ethnicity']),
            confidence=data['confidence'],
            method=data['method'],
            phonetic_codes=data.get('phonetic_codes'),
            created_at=created_at,
            cached=True
        )


class PhoneticResult(BaseModel):
    """Result from phonetic matching algorithms.
    
    Used internally by the classification system to store and compare
    phonetic algorithm results.
    
    Attributes:
        algorithm: Name of phonetic algorithm used
        code: Generated phonetic code
        original_name: Name that was processed
        weight: Algorithm weight for scoring (0-1)
    """
    
    algorithm: str = Field(..., description="Phonetic algorithm name")
    code: str = Field(..., description="Generated phonetic code")
    original_name: str = Field(..., description="Original name processed")
    weight: float = Field(1.0, ge=0, le=1, description="Algorithm weight for scoring")
    
    @validator('algorithm')
    def validate_algorithm(cls, v: str) -> str:
        """Validate algorithm name."""
        valid_algorithms = {
            'soundex', 'metaphone', 'double_metaphone', 
            'nysiis', 'jaro_winkler', 'custom_sa'
        }
        if v not in valid_algorithms:
            raise ValueError(f"Invalid algorithm. Must be one of: {valid_algorithms}")
        return v


class ClassificationMatch(BaseModel):
    """Match result when comparing names for classification.
    
    Used when searching for similar names in the classification cache
    or when performing phonetic matching.
    
    Attributes:
        original_name: Name being classified
        matched_name: Name that was matched
        similarity_score: Similarity score (0-1)
        matched_classification: Classification of the matched name
        match_method: How the match was found
    """
    
    original_name: str = Field(..., description="Name being classified")
    matched_name: str = Field(..., description="Name that was matched")
    similarity_score: float = Field(..., ge=0, le=1, description="Similarity score")
    matched_classification: Classification = Field(..., description="Classification of matched name")
    match_method: str = Field(..., description="Method used to find match")
    
    @validator('match_method')
    def validate_match_method(cls, v: str) -> str:
        """Validate match method."""
        valid_methods = {'exact', 'phonetic', 'fuzzy', 'substring'}
        if v not in valid_methods:
            raise ValueError(f"Invalid match method. Must be one of: {valid_methods}")
        return v
    
    def is_reliable_match(self, threshold: float = 0.8) -> bool:
        """Check if match is reliable enough for classification.
        
        Args:
            threshold: Minimum similarity score
            
        Returns:
            True if match is reliable
        """
        return (self.similarity_score >= threshold and 
                self.matched_classification.is_high_confidence())


class ClassificationStats(BaseModel):
    """Statistics for classification performance tracking.
    
    Used for monitoring and optimizing the classification system
    performance over time.
    
    Attributes:
        total_classifications: Total number of classifications performed
        cache_hits: Number of exact cache hits
        phonetic_matches: Number of phonetic matches used
        llm_calls: Number of LLM API calls made
        high_confidence_results: Number of high-confidence results
        processing_time_ms: Average processing time in milliseconds
        accuracy_rate: Estimated accuracy rate (when validation available)
        updated_at: When statistics were last updated
    """
    
    total_classifications: int = Field(0, ge=0, description="Total classifications performed")
    cache_hits: int = Field(0, ge=0, description="Exact cache hits")
    phonetic_matches: int = Field(0, ge=0, description="Phonetic matches used")
    llm_calls: int = Field(0, ge=0, description="LLM API calls made")
    high_confidence_results: int = Field(0, ge=0, description="High-confidence results")
    processing_time_ms: float = Field(0.0, ge=0, description="Average processing time")
    accuracy_rate: Optional[float] = Field(None, ge=0, le=1, description="Estimated accuracy rate")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage.
        
        Returns:
            Cache hit rate as percentage (0-100)
        """
        if self.total_classifications == 0:
            return 0.0
        return (self.cache_hits / self.total_classifications) * 100
    
    def get_llm_usage_rate(self) -> float:
        """Calculate LLM usage rate percentage.
        
        Returns:
            LLM usage rate as percentage (0-100)
        """
        if self.total_classifications == 0:
            return 0.0
        return (self.llm_calls / self.total_classifications) * 100
    
    def get_high_confidence_rate(self) -> float:
        """Calculate high-confidence result rate.
        
        Returns:
            High-confidence rate as percentage (0-100)
        """
        if self.total_classifications == 0:
            return 0.0
        return (self.high_confidence_results / self.total_classifications) * 100