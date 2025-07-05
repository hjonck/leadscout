"""Unit tests for classification models and data structures."""

from datetime import datetime

import pytest

from leadscout.classification.models import (
    BatchClassificationRequest,
    Classification,
    ClassificationMethod,
    ClassificationRequest,
    ClassificationStats,
    ConfidenceLevel,
    EthnicityType,
    PhoneticMatch,
    RuleClassificationDetails,
    ValidationResult,
)


class TestClassification:
    """Test suite for Classification model."""

    def test_classification_creation(self):
        """Test creating a basic classification."""
        classification = Classification(
            name="John Smith",
            ethnicity=EthnicityType.WHITE,
            confidence=0.85,
            method=ClassificationMethod.RULE_BASED,
        )

        assert classification.name == "John Smith"
        assert classification.ethnicity == EthnicityType.WHITE
        assert classification.confidence == 0.85
        assert classification.method == ClassificationMethod.RULE_BASED
        assert classification.confidence_level == ConfidenceLevel.HIGH
        assert isinstance(classification.timestamp, datetime)

    def test_confidence_level_auto_assignment(self):
        """Test that confidence levels are automatically assigned."""
        # Very high confidence
        c1 = Classification(
            name="Test",
            ethnicity=EthnicityType.AFRICAN,
            confidence=0.97,
            method=ClassificationMethod.RULE_BASED,
        )
        assert c1.confidence_level == ConfidenceLevel.VERY_HIGH

        # High confidence
        c2 = Classification(
            name="Test",
            ethnicity=EthnicityType.AFRICAN,
            confidence=0.88,
            method=ClassificationMethod.RULE_BASED,
        )
        assert c2.confidence_level == ConfidenceLevel.HIGH

        # Medium confidence
        c3 = Classification(
            name="Test",
            ethnicity=EthnicityType.AFRICAN,
            confidence=0.75,
            method=ClassificationMethod.PHONETIC,
        )
        assert c3.confidence_level == ConfidenceLevel.MEDIUM

        # Low confidence
        c4 = Classification(
            name="Test",
            ethnicity=EthnicityType.AFRICAN,
            confidence=0.60,
            method=ClassificationMethod.PHONETIC,
        )
        assert c4.confidence_level == ConfidenceLevel.LOW

        # Very low confidence
        c5 = Classification(
            name="Test",
            ethnicity=EthnicityType.AFRICAN,
            confidence=0.40,
            method=ClassificationMethod.LLM,
        )
        assert c5.confidence_level == ConfidenceLevel.VERY_LOW

    def test_name_validation(self):
        """Test that name validation works."""
        # Valid name
        c1 = Classification(
            name="Valid Name",
            ethnicity=EthnicityType.AFRICAN,
            confidence=0.85,
            method=ClassificationMethod.RULE_BASED,
        )
        assert c1.name == "Valid Name"

        # Name with extra whitespace
        c2 = Classification(
            name="  Trimmed Name  ",
            ethnicity=EthnicityType.AFRICAN,
            confidence=0.85,
            method=ClassificationMethod.RULE_BASED,
        )
        assert c2.name == "Trimmed Name"

        # Empty name should raise validation error
        with pytest.raises(ValueError, match="Name cannot be empty"):
            Classification(
                name="",
                ethnicity=EthnicityType.AFRICAN,
                confidence=0.85,
                method=ClassificationMethod.RULE_BASED,
            )

    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Valid confidence
        c1 = Classification(
            name="Test",
            ethnicity=EthnicityType.AFRICAN,
            confidence=0.75,
            method=ClassificationMethod.RULE_BASED,
        )
        assert c1.confidence == 0.75

        # Invalid confidence - too low
        with pytest.raises(ValueError):
            Classification(
                name="Test",
                ethnicity=EthnicityType.AFRICAN,
                confidence=-0.1,
                method=ClassificationMethod.RULE_BASED,
            )

        # Invalid confidence - too high
        with pytest.raises(ValueError):
            Classification(
                name="Test",
                ethnicity=EthnicityType.AFRICAN,
                confidence=1.1,
                method=ClassificationMethod.RULE_BASED,
            )


class TestRuleClassificationDetails:
    """Test suite for RuleClassificationDetails."""

    def test_rule_details_creation(self):
        """Test creating rule classification details."""
        details = RuleClassificationDetails(
            matched_dictionary=EthnicityType.AFRICAN,
            matched_name="Mthembu",
            dictionary_confidence=0.95,
            linguistic_origin="Nguni",
            regional_pattern="KwaZulu-Natal",
            name_type="surname",
        )

        assert details.matched_dictionary == EthnicityType.AFRICAN
        assert details.matched_name == "Mthembu"
        assert details.dictionary_confidence == 0.95
        assert details.linguistic_origin == "Nguni"
        assert details.regional_pattern == "KwaZulu-Natal"
        assert details.name_type == "surname"


class TestPhoneticMatch:
    """Test suite for PhoneticMatch model."""

    def test_phonetic_match_creation(self):
        """Test creating a phonetic match."""
        match = PhoneticMatch(
            matched_name="Mthembu",
            matched_ethnicity=EthnicityType.AFRICAN,
            algorithm="soundex",
            similarity_score=0.85,
            phonetic_code="M351",
            original_confidence=0.90,
        )

        assert match.matched_name == "Mthembu"
        assert match.matched_ethnicity == EthnicityType.AFRICAN
        assert match.algorithm == "soundex"
        assert match.similarity_score == 0.85
        assert match.phonetic_code == "M351"
        assert match.original_confidence == 0.90


class TestClassificationRequest:
    """Test suite for ClassificationRequest model."""

    def test_request_creation(self):
        """Test creating a classification request."""
        request = ClassificationRequest(name="John Smith")

        assert request.name == "John Smith"
        assert request.require_high_confidence is False
        assert request.use_cache is True
        assert request.use_phonetic is True
        assert request.use_llm is True
        assert request.context is None

    def test_request_name_validation(self):
        """Test request name validation."""
        # Valid name
        request = ClassificationRequest(name="Valid Name")
        assert request.name == "Valid Name"

        # Name with whitespace
        request = ClassificationRequest(name="  Trimmed  ")
        assert request.name == "Trimmed"

        # Empty name
        with pytest.raises(ValueError, match="Name cannot be empty"):
            ClassificationRequest(name="")

        # Too short name
        with pytest.raises(
            ValueError, match="Name must be at least 2 characters"
        ):
            ClassificationRequest(name="A")

    def test_request_with_options(self):
        """Test creating request with custom options."""
        request = ClassificationRequest(
            name="Test Name",
            require_high_confidence=True,
            use_cache=False,
            use_phonetic=False,
            use_llm=False,
            context={"company": "Test Corp"},
        )

        assert request.name == "Test Name"
        assert request.require_high_confidence is True
        assert request.use_cache is False
        assert request.use_phonetic is False
        assert request.use_llm is False
        assert request.context == {"company": "Test Corp"}


class TestBatchClassificationRequest:
    """Test suite for BatchClassificationRequest model."""

    def test_batch_request_creation(self):
        """Test creating a batch classification request."""
        request = BatchClassificationRequest(
            names=["John Smith", "Mary Johnson", "David Brown"]
        )

        assert len(request.names) == 3
        assert "John Smith" in request.names
        assert request.batch_size == 20
        assert request.require_high_confidence is False

    def test_batch_request_name_validation(self):
        """Test batch request name validation."""
        # Valid names
        request = BatchClassificationRequest(
            names=["Valid Name", "Another Name", "  Trimmed  "]
        )
        assert len(request.names) == 3
        assert "Trimmed" in request.names

        # Filter out invalid names
        request = BatchClassificationRequest(
            names=["Valid Name", "", "A", "Another Valid Name"]
        )
        assert len(request.names) == 2
        assert "Valid Name" in request.names
        assert "Another Valid Name" in request.names

        # No valid names
        with pytest.raises(ValueError, match="No valid names provided"):
            BatchClassificationRequest(names=["", "A", "  "])


class TestValidationResult:
    """Test suite for ValidationResult model."""

    def test_validation_result_creation(self):
        """Test creating a validation result."""
        result = ValidationResult(
            original_name="John Smith",
            normalized_name="John Smith",
            is_valid=True,
            name_parts=["John", "Smith"],
            is_multi_word=True,
        )

        assert result.original_name == "John Smith"
        assert result.normalized_name == "John Smith"
        assert result.is_valid is True
        assert result.name_parts == ["John", "Smith"]
        assert result.is_multi_word is True
        assert len(result.validation_errors) == 0
        assert len(result.suggested_corrections) == 0


class TestClassificationStats:
    """Test suite for ClassificationStats model."""

    def test_stats_creation(self):
        """Test creating classification statistics."""
        stats = ClassificationStats()

        assert stats.total_classifications == 0
        assert stats.average_confidence == 0.0
        assert stats.cache_hit_rate == 0.0
        assert stats.llm_usage_rate == 0.0
        assert len(stats.method_breakdown) == 0
        assert len(stats.confidence_breakdown) == 0
        assert len(stats.ethnicity_breakdown) == 0

    def test_stats_update_with_classification(self):
        """Test updating stats with a classification."""
        stats = ClassificationStats()

        classification = Classification(
            name="Test",
            ethnicity=EthnicityType.AFRICAN,
            confidence=0.85,
            method=ClassificationMethod.RULE_BASED,
            processing_time_ms=5.0,
        )

        # Update stats
        stats.update_with_classification(classification, from_cache=False)

        assert stats.total_classifications == 1
        assert stats.average_confidence == 0.85
        assert stats.average_processing_time_ms == 5.0
        assert stats.method_breakdown[ClassificationMethod.RULE_BASED] == 1
        assert stats.confidence_breakdown[ConfidenceLevel.HIGH] == 1
        assert stats.ethnicity_breakdown[EthnicityType.AFRICAN] == 1
        assert stats.cache_hit_rate == 0.0  # Not from cache
        assert stats.llm_usage_rate == 0.0  # Not LLM

        # Add another classification from cache
        stats.update_with_classification(classification, from_cache=True)

        assert stats.total_classifications == 2
        assert stats.cache_hit_rate == 0.5  # 1 out of 2 from cache

    def test_stats_multiple_updates(self):
        """Test updating stats with multiple classifications."""
        stats = ClassificationStats()

        # Add rule-based classification
        rule_classification = Classification(
            name="Test1",
            ethnicity=EthnicityType.AFRICAN,
            confidence=0.90,
            method=ClassificationMethod.RULE_BASED,
        )
        stats.update_with_classification(rule_classification)

        # Add LLM classification
        llm_classification = Classification(
            name="Test2",
            ethnicity=EthnicityType.INDIAN,
            confidence=0.75,
            method=ClassificationMethod.LLM,
        )
        stats.update_with_classification(llm_classification)

        # Add cache hit
        stats.update_with_classification(rule_classification, from_cache=True)

        assert stats.total_classifications == 3
        assert stats.average_confidence == (0.90 + 0.75 + 0.90) / 3
        assert stats.method_breakdown[ClassificationMethod.RULE_BASED] == 1
        assert stats.method_breakdown[ClassificationMethod.LLM] == 1
        assert stats.method_breakdown[ClassificationMethod.CACHE] == 1
        assert stats.cache_hit_rate == 1 / 3  # 1 out of 3 from cache
        assert stats.llm_usage_rate == 1 / 3  # 1 out of 3 used LLM
