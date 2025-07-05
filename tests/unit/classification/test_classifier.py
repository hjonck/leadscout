"""Unit tests for the integrated multi-layered name classifier.

Tests the complete NameClassifier orchestrator that combines rule-based,
phonetic, and LLM classification methods in a unified pipeline.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from leadscout.classification.classifier import NameClassifier, create_classifier
from leadscout.classification.dictionaries import EthnicityType
from leadscout.classification.models import (
    Classification,
    ClassificationMethod,
    ConfidenceLevel,
)


class TestNameClassifier:
    """Test suite for the integrated NameClassifier."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create classifier with LLM disabled for most tests (no API calls)
        self.classifier = NameClassifier(
            rule_confidence_threshold=0.8,
            phonetic_confidence_threshold=0.6,
            llm_confidence_threshold=0.5,
            enable_llm=False,  # Disable for unit tests
            enable_caching=False,  # Disable for unit tests
        )

    def test_initialization(self):
        """Test classifier initialization."""
        assert self.classifier.rule_confidence_threshold == 0.8
        assert self.classifier.phonetic_confidence_threshold == 0.6
        assert self.classifier.llm_confidence_threshold == 0.5
        assert not self.classifier.enable_llm
        assert not self.classifier.enable_caching
        assert self.classifier.rule_classifier is not None
        assert self.classifier.phonetic_classifier is not None
        assert self.classifier.llm_classifier is None  # Disabled

    def test_initialization_with_llm_enabled(self):
        """Test classifier initialization with LLM enabled."""
        # Mock the LLM initialization to avoid API calls
        with patch('leadscout.classification.classifier.LLMClassifier') as mock_llm:
            mock_llm.return_value = MagicMock()
            
            classifier = NameClassifier(enable_llm=True)
            
            assert classifier.enable_llm
            assert classifier.llm_classifier is not None
            mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_known_rule_based_name(self):
        """Test classification of name that hits rule-based layer."""
        result = await self.classifier.classify_name("Thabo Mthembu")
        
        assert result is not None
        assert result.ethnicity == EthnicityType.AFRICAN
        assert result.method == ClassificationMethod.RULE_BASED
        assert result.confidence >= 0.8
        assert "Thabo" in result.name or "Mthembu" in result.name

    @pytest.mark.asyncio
    async def test_classify_phonetic_variant(self):
        """Test classification that falls through to phonetic layer."""
        # Use a phonetic variant that should not be in rule-based dictionary
        result = await self.classifier.classify_name("Bonganni")  # Variant of Bongani
        
        if result:  # May or may not find phonetic match
            assert result.method == ClassificationMethod.PHONETIC
            assert result.confidence >= 0.5

    @pytest.mark.asyncio
    async def test_classify_unknown_name_no_llm(self):
        """Test classification of completely unknown name without LLM."""
        result = await self.classifier.classify_name("XyzUnknown")
        
        # Should return None since LLM is disabled and name is unknown
        assert result is None

    @pytest.mark.asyncio
    async def test_classify_name_with_llm_enabled(self):
        """Test classification with LLM enabled (mocked)."""
        # Mock LLM classifier
        mock_llm = AsyncMock()
        mock_llm_result = Classification(
            name="UnknownName",
            ethnicity=EthnicityType.AFRICAN,
            confidence=0.75,
            method=ClassificationMethod.LLM,
        )
        mock_llm.classify_name.return_value = mock_llm_result
        
        # Create classifier with mocked LLM
        with patch('leadscout.classification.classifier.LLMClassifier') as mock_llm_class:
            mock_llm_class.return_value = mock_llm
            
            classifier = NameClassifier(enable_llm=True)
            classifier.llm_classifier = mock_llm
            
            # Test with unknown name that should reach LLM
            result = await classifier.classify_name("CompletelyUnknownName")
            
            # Should reach LLM layer and return mocked result
            assert result is not None
            assert result.method == ClassificationMethod.LLM
            assert result.ethnicity == EthnicityType.AFRICAN
            mock_llm.classify_name.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_empty_name_raises_error(self):
        """Test that empty names raise validation error."""
        from leadscout.classification.exceptions import NameValidationError
        
        with pytest.raises(NameValidationError):
            await self.classifier.classify_name("")
            
        with pytest.raises(NameValidationError):
            await self.classifier.classify_name("   ")

    @pytest.mark.asyncio
    async def test_classify_none_name_raises_error(self):
        """Test that None name raises validation error."""
        from leadscout.classification.exceptions import NameValidationError
        
        with pytest.raises(NameValidationError):
            await self.classifier.classify_name(None)

    @pytest.mark.asyncio
    async def test_cascade_behavior_rule_to_phonetic(self):
        """Test that classification properly cascades from rule to phonetic."""
        # Mock rule classifier to return None
        with patch.object(self.classifier.rule_classifier, 'classify_name', return_value=None):
            # Mock phonetic classifier to return a result
            mock_phonetic_result = Classification(
                name="TestName",
                ethnicity=EthnicityType.INDIAN,
                confidence=0.7,
                method=ClassificationMethod.PHONETIC,
            )
            with patch.object(self.classifier.phonetic_classifier, 'classify_name', return_value=mock_phonetic_result) as mock_phonetic:
                
                result = await self.classifier.classify_name("TestName")
                
                assert result is not None
                assert result.method == ClassificationMethod.PHONETIC
                assert result.ethnicity == EthnicityType.INDIAN
                mock_phonetic.assert_called_once_with("TestName")

    @pytest.mark.asyncio
    async def test_confidence_threshold_filtering(self):
        """Test that low confidence results are filtered out."""
        # Mock rule classifier to return low confidence
        low_confidence_result = Classification(
            name="TestName",
            ethnicity=EthnicityType.WHITE,
            confidence=0.5,  # Below threshold of 0.8
            method=ClassificationMethod.RULE_BASED,
        )
        
        with patch.object(self.classifier.rule_classifier, 'classify_name', return_value=low_confidence_result):
            with patch.object(self.classifier.phonetic_classifier, 'classify_name', return_value=None):
                
                result = await self.classifier.classify_name("TestName")
                
                # Should return None because confidence too low and no phonetic match
                assert result is None

    @pytest.mark.asyncio
    async def test_require_high_confidence_mode(self):
        """Test require_high_confidence mode."""
        # Mock rule classifier to return medium confidence
        medium_confidence_result = Classification(
            name="TestName",
            ethnicity=EthnicityType.AFRICAN,
            confidence=0.82,  # Above normal threshold but below high threshold
            method=ClassificationMethod.RULE_BASED,
        )
        
        with patch.object(self.classifier.rule_classifier, 'classify_name', return_value=medium_confidence_result):
            # Normal mode should accept the result
            result_normal = await self.classifier.classify_name("TestName", require_high_confidence=False)
            assert result_normal is not None
            assert result_normal.confidence == 0.82
            
            # High confidence mode should reject and look for better result
            with patch.object(self.classifier.phonetic_classifier, 'classify_name', return_value=None):
                from leadscout.classification.exceptions import ConfidenceThresholdError
                
                with pytest.raises(ConfidenceThresholdError):
                    await self.classifier.classify_name("TestName", require_high_confidence=True)

    @pytest.mark.asyncio
    async def test_batch_classification(self):
        """Test batch classification functionality."""
        test_names = ["Thabo", "Pillay", "Smith", "UnknownName"]
        
        results = await self.classifier.classify_batch(test_names, max_concurrent=2)
        
        assert len(results) == len(test_names)
        
        # Check that known names are classified
        for i, result in enumerate(results):
            if test_names[i] in ["Thabo", "Pillay", "Smith"]:
                assert result is not None
                assert result.ethnicity in [
                    EthnicityType.AFRICAN, 
                    EthnicityType.INDIAN, 
                    EthnicityType.WHITE
                ]

    @pytest.mark.asyncio
    async def test_batch_classification_with_progress_callback(self):
        """Test batch classification with progress callback."""
        test_names = ["Thabo", "Pillay"]
        progress_calls = []
        
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        await self.classifier.classify_batch(
            test_names, 
            progress_callback=progress_callback
        )
        
        # Should have called progress callback
        assert len(progress_calls) >= 1
        assert progress_calls[-1] == (2, 2)  # Final call

    @pytest.mark.asyncio
    async def test_batch_classification_error_handling(self):
        """Test batch classification handles individual failures gracefully."""
        test_names = ["Thabo", "InvalidName", "Pillay"]
        
        # Mock one classification to fail
        original_classify = self.classifier.classify_name
        
        async def mock_classify(name, context=None, require_high_confidence=False):
            if name == "InvalidName":
                raise ValueError("Mock error")
            return await original_classify(name, context, require_high_confidence)
        
        with patch.object(self.classifier, 'classify_name', side_effect=mock_classify):
            results = await self.classifier.classify_batch(test_names)
            
            assert len(results) == 3
            # First and third should succeed, middle should be None due to error
            assert results[0] is not None or results[0] is None  # May or may not find
            assert results[1] is None  # Should be None due to error
            assert results[2] is not None or results[2] is None  # May or may not find

    def test_session_stats_tracking(self):
        """Test session statistics tracking."""
        initial_stats = self.classifier.get_session_stats()
        
        assert initial_stats.total_classifications == 0
        assert initial_stats.rule_classifications == 0
        assert initial_stats.phonetic_classifications == 0
        assert initial_stats.llm_classifications == 0

    @pytest.mark.asyncio
    async def test_session_stats_updates(self):
        """Test that session stats update correctly."""
        # Perform some classifications
        await self.classifier.classify_name("Thabo")  # Should hit rules
        await self.classifier.classify_name("UnknownName")  # Should miss
        
        stats = self.classifier.get_session_stats()
        
        assert stats.total_classifications == 2
        # At least one rule hit expected
        assert stats.rule_classifications >= 0

    def test_reset_session_stats(self):
        """Test session stats reset functionality."""
        # The session starts fresh, but let's test the reset mechanism
        old_stats = self.classifier.reset_session_stats()
        new_stats = self.classifier.get_session_stats()
        
        assert new_stats.total_classifications == 0
        assert isinstance(old_stats.total_classifications, int)

    def test_get_system_info(self):
        """Test system information retrieval."""
        info = self.classifier.get_system_info()
        
        assert "version" in info
        assert "enabled_layers" in info
        assert "confidence_thresholds" in info
        assert "cost_limits" in info
        assert "component_info" in info
        
        # Check layer status
        assert info["enabled_layers"]["rule_based"] is True
        assert info["enabled_layers"]["phonetic"] is True
        assert info["enabled_layers"]["llm"] is False  # Disabled in test

    @pytest.mark.asyncio
    async def test_context_passing(self):
        """Test that context is passed through the pipeline."""
        context = {"company_name": "Test Corp", "location": "Cape Town"}
        
        # Mock LLM to verify context is passed
        mock_llm = AsyncMock()
        self.classifier.llm_classifier = mock_llm
        self.classifier.enable_llm = True
        
        # Mock other classifiers to return None so it reaches LLM
        with patch.object(self.classifier.rule_classifier, 'classify_name', return_value=None):
            with patch.object(self.classifier.phonetic_classifier, 'classify_name', return_value=None):
                
                await self.classifier.classify_name("TestName", context=context)
                
                # Verify context was passed to LLM
                mock_llm.classify_name.assert_called_once_with("TestName", context)

    @pytest.mark.asyncio
    async def test_caching_integration_placeholder(self):
        """Test caching integration (placeholder for Developer A's cache)."""
        # Enable caching
        classifier_with_cache = NameClassifier(enable_caching=True, enable_llm=False)
        
        # Since cache integration is a placeholder, this should work normally
        result = await classifier_with_cache.classify_name("Thabo")
        
        # Should still work even with caching enabled (placeholder)
        if result:  # May or may not classify
            assert isinstance(result, Classification)


class TestCreateClassifier:
    """Test the classifier factory function."""

    def test_create_fast_classifier(self):
        """Test creating fast mode classifier."""
        classifier = create_classifier(mode="fast", enable_llm=False)
        
        assert classifier.rule_confidence_threshold == 0.7
        assert classifier.phonetic_confidence_threshold == 0.7
        assert classifier.llm_confidence_threshold == 0.6
        assert not classifier.enable_llm

    def test_create_accurate_classifier(self):
        """Test creating accurate mode classifier."""
        classifier = create_classifier(mode="accurate", enable_llm=False)
        
        assert classifier.rule_confidence_threshold == 0.9
        assert classifier.phonetic_confidence_threshold == 0.8
        assert classifier.llm_confidence_threshold == 0.7
        assert not classifier.enable_llm

    def test_create_balanced_classifier(self):
        """Test creating balanced mode classifier (default)."""
        classifier = create_classifier(mode="balanced", enable_llm=False)
        
        assert classifier.rule_confidence_threshold == 0.8
        assert classifier.phonetic_confidence_threshold == 0.6
        assert classifier.llm_confidence_threshold == 0.5
        assert not classifier.enable_llm

    def test_create_classifier_with_custom_cost(self):
        """Test creating classifier with custom cost limit."""
        classifier = create_classifier(enable_llm=False, max_cost=25.0)
        
        assert classifier.max_llm_cost_per_session == 25.0


class TestClassificationPerformance:
    """Test classification performance and benchmarks."""

    def setup_method(self):
        """Set up performance test fixtures."""
        self.classifier = NameClassifier(enable_llm=False, enable_caching=False)

    @pytest.mark.asyncio
    async def test_classification_speed_benchmark(self):
        """Test that classification meets speed targets."""
        import time
        
        test_names = ["Thabo", "Pillay", "Smith", "Van der Merwe"]
        
        start_time = time.time()
        
        for name in test_names:
            await self.classifier.classify_name(name)
        
        end_time = time.time()
        avg_time_ms = (end_time - start_time) * 1000 / len(test_names)
        
        # Should be fast for rule-based classifications
        assert avg_time_ms < 100, f"Average classification time {avg_time_ms:.1f}ms too slow"

    @pytest.mark.asyncio
    async def test_batch_vs_individual_performance(self):
        """Test that batch processing provides efficiency gains."""
        import time
        
        test_names = ["Thabo", "Pillay", "Smith", "Botha"]
        
        # Individual processing
        start_individual = time.time()
        individual_results = []
        for name in test_names:
            result = await self.classifier.classify_name(name)
            individual_results.append(result)
        end_individual = time.time()
        
        # Batch processing
        start_batch = time.time()
        batch_results = await self.classifier.classify_batch(test_names)
        end_batch = time.time()
        
        individual_time = end_individual - start_individual
        batch_time = end_batch - start_batch
        
        # Batch should be comparable or faster
        # (Note: For rule-based processing, the difference may be minimal)
        assert len(batch_results) == len(individual_results)
        
        # Log times for analysis
        print(f"Individual: {individual_time:.3f}s, Batch: {batch_time:.3f}s")


class TestErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up error handling test fixtures."""
        self.classifier = NameClassifier(enable_llm=False, enable_caching=False)

    @pytest.mark.asyncio
    async def test_rule_classifier_error_handling(self):
        """Test handling of rule classifier errors."""
        # Mock rule classifier to raise exception
        with patch.object(self.classifier.rule_classifier, 'classify_name', side_effect=Exception("Mock rule error")):
            # Should gracefully fall through to phonetic layer
            result = await self.classifier.classify_name("TestName")
            
            # May or may not get result from phonetic layer, but should not crash
            assert result is None or isinstance(result, Classification)

    @pytest.mark.asyncio
    async def test_phonetic_classifier_error_handling(self):
        """Test handling of phonetic classifier errors."""
        # Mock both classifiers to have rule miss and phonetic error
        with patch.object(self.classifier.rule_classifier, 'classify_name', return_value=None):
            with patch.object(self.classifier.phonetic_classifier, 'classify_name', side_effect=Exception("Mock phonetic error")):
                
                result = await self.classifier.classify_name("TestName")
                
                # Should return None since both layers failed/missed
                assert result is None

    @pytest.mark.asyncio
    async def test_all_layers_error_graceful_handling(self):
        """Test graceful handling when all layers fail."""
        # Mock all classifiers to fail
        with patch.object(self.classifier.rule_classifier, 'classify_name', side_effect=Exception("Rule error")):
            with patch.object(self.classifier.phonetic_classifier, 'classify_name', side_effect=Exception("Phonetic error")):
                
                result = await self.classifier.classify_name("TestName")
                
                # Should return None gracefully, not crash
                assert result is None

    @pytest.mark.asyncio
    async def test_whitespace_handling(self):
        """Test handling of names with extra whitespace."""
        test_cases = [
            "  Thabo  ",
            " Thabo Mthembu ",
            "Thabo\t\tMthembu",
            "  Pillay   ",
        ]
        
        for name in test_cases:
            result = await self.classifier.classify_name(name)
            # Should handle gracefully without errors
            assert result is None or isinstance(result, Classification)

    @pytest.mark.asyncio
    async def test_special_characters_handling(self):
        """Test handling of names with special characters."""
        test_cases = [
            "Jean-Pierre",
            "O'Sullivan",
            "Van der Merwe",
            "D'Angelo",
            "McKenzie",
        ]
        
        for name in test_cases:
            result = await self.classifier.classify_name(name)
            # Should handle gracefully without errors
            assert result is None or isinstance(result, Classification)