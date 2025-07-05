"""Unit tests for LLM classification with Claude 3.5 Haiku (research-validated).

Tests the LLM classifier implementation with optimized prompts, cost monitoring,
batch processing, and few-shot learning capabilities.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from leadscout.classification.dictionaries import EthnicityType
from leadscout.classification.exceptions import LLMClassificationError
from leadscout.classification.llm import CostMonitor, LLMClassifier
from leadscout.classification.models import Classification, ClassificationMethod


class TestCostMonitor:
    """Test cost monitoring and circuit breaker functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = CostMonitor(session_limit=1.0, per_classification_limit=0.001)

    def test_initialization(self):
        """Test cost monitor initialization."""
        assert self.monitor.session_limit == 1.0
        assert self.monitor.per_classification_limit == 0.001
        assert self.monitor.session_cost == 0.0
        assert self.monitor.classification_count == 0

    def test_track_usage(self):
        """Test usage tracking."""
        self.monitor.track_usage(0.0005)
        
        assert self.monitor.session_cost == 0.0005
        assert self.monitor.classification_count == 1

    def test_should_allow_request_within_limits(self):
        """Test that requests are allowed within limits."""
        assert self.monitor.should_allow_request() is True
        
        # Add some usage within limits
        self.monitor.track_usage(0.0005)
        assert self.monitor.should_allow_request() is True

    def test_should_deny_request_session_limit_exceeded(self):
        """Test that requests are denied when session limit exceeded."""
        # Exceed session limit
        self.monitor.track_usage(1.5)
        assert self.monitor.should_allow_request() is False

    def test_should_deny_request_per_classification_too_high(self):
        """Test that requests are denied when per-classification cost too high."""
        # Add usage that exceeds per-classification safety margin (5x)
        self.monitor.track_usage(0.006)  # 0.006 > 0.001 * 5
        assert self.monitor.should_allow_request() is False

    def test_get_stats(self):
        """Test statistics retrieval."""
        self.monitor.track_usage(0.0003)
        self.monitor.track_usage(0.0002)
        
        stats = self.monitor.get_stats()
        
        assert stats["session_cost"] == 0.0005
        assert stats["classification_count"] == 2
        assert stats["avg_cost_per_classification"] == 0.00025
        assert stats["remaining_budget"] == 0.9995


class TestLLMClassifier:
    """Test LLM classifier with research-validated approach."""

    def setup_method(self):
        """Set up test fixtures with mocked LLM clients."""
        # Create classifier without actual API clients
        self.classifier = LLMClassifier(
            claude_api_key=None,  # No real API key
            openai_api_key=None,  # No real API key
            cost_limit_per_session=1.0,
        )
        
        # Mock the clients to avoid actual API calls
        self.mock_claude_response = MagicMock()
        self.mock_claude_response.content = [MagicMock()]
        self.mock_claude_response.content[0].text = "african"
        self.mock_claude_response.usage.input_tokens = 100
        self.mock_claude_response.usage.output_tokens = 10
        
        self.mock_openai_response = MagicMock()
        self.mock_openai_response.choices = [MagicMock()]
        self.mock_openai_response.choices[0].message.content = "indian"
        self.mock_openai_response.usage.prompt_tokens = 95
        self.mock_openai_response.usage.completion_tokens = 8

    def test_initialization_no_providers(self):
        """Test initialization when no providers are available."""
        with pytest.raises(LLMClassificationError):
            LLMClassifier()  # No API keys provided

    def test_initialization_with_claude(self):
        """Test initialization with Claude API key."""
        with patch('leadscout.classification.llm.ANTHROPIC_AVAILABLE', True):
            with patch('leadscout.classification.llm.anthropic.AsyncAnthropic') as mock_anthropic:
                classifier = LLMClassifier(claude_api_key="test_key")
                
                assert classifier.claude_client is not None
                assert classifier.primary_model == "claude-3-5-haiku-20241022"
                mock_anthropic.assert_called_once_with(api_key="test_key")

    def test_initialization_with_openai_fallback(self):
        """Test initialization with OpenAI as fallback."""
        with patch('leadscout.classification.llm.OPENAI_AVAILABLE', True):
            with patch('leadscout.classification.llm.openai.AsyncOpenAI') as mock_openai:
                classifier = LLMClassifier(openai_api_key="test_key")
                
                assert classifier.openai_client is not None
                assert classifier.fallback_model == "gpt-4o-mini"
                mock_openai.assert_called_once_with(api_key="test_key")

    def test_get_few_shot_examples(self):
        """Test few-shot examples generation from SA dictionary."""
        examples = self.classifier._get_few_shot_examples("TestName")
        
        assert isinstance(examples, list)
        assert len(examples) <= 15  # Limited for prompt efficiency
        
        # Check that examples contain valid ethnicity values
        for name, ethnicity in examples:
            assert isinstance(name, str)
            assert ethnicity in ["african", "indian", "cape_malay", "coloured", "white"]

    def test_get_optimized_prompt_structure(self):
        """Test research-validated optimized prompt generation."""
        few_shot_examples = [("Thabo", "african"), ("Pillay", "indian")]
        prompt = self.classifier._get_optimized_prompt(
            "TestName", 
            few_shot_examples=few_shot_examples
        )
        
        # Should contain research-validated elements
        assert "TestName" in prompt
        assert "african|indian|cape_malay|coloured|white|unknown" in prompt
        assert "Nguni, Tamil, Cape Muslim, Afrikaans" in prompt
        assert "Thabo: african" in prompt
        assert "Pillay: indian" in prompt

    def test_get_batch_prompt_structure(self):
        """Test batch prompt generation for optimal processing."""
        names = ["Name1", "Name2", "Name3"]
        few_shot_examples = [("Thabo", "african")]
        
        prompt = self.classifier._get_batch_prompt(names, few_shot_examples)
        
        # Should contain all names with numbering
        assert "1. Name1" in prompt
        assert "2. Name2" in prompt  
        assert "3. Name3" in prompt
        assert "Thabo: african" in prompt
        assert "1. name: ethnicity" in prompt

    def test_calculate_cost_claude_haiku(self):
        """Test cost calculation for Claude 3.5 Haiku."""
        cost = self.classifier._calculate_cost(
            "claude-3-5-haiku-20241022", 
            prompt_tokens=100, 
            completion_tokens=20
        )
        
        # Research-validated pricing: $0.00025 input, $0.00125 output per 1k tokens
        expected = (100/1000 * 0.00025) + (20/1000 * 0.00125)
        assert abs(cost - expected) < 0.000001

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation for unknown model."""
        cost = self.classifier._calculate_cost("unknown-model", 100, 20)
        assert cost == 0.0

    def test_parse_single_response(self):
        """Test parsing of single name classification response."""
        test_cases = [
            ("african", EthnicityType.AFRICAN, 0.85),
            ("indian", EthnicityType.INDIAN, 0.85),
            ("cape_malay", EthnicityType.CAPE_MALAY, 0.85),
            ("coloured", EthnicityType.COLOURED, 0.85),
            ("white", EthnicityType.WHITE, 0.85),
            ("unknown response", EthnicityType.UNKNOWN, 0.60),
        ]
        
        for response_text, expected_ethnicity, expected_confidence in test_cases:
            ethnicity, confidence = self.classifier._parse_single_response(
                response_text, "TestName"
            )
            assert ethnicity == expected_ethnicity
            assert confidence == expected_confidence

    def test_parse_batch_response(self):
        """Test parsing of batch classification response."""
        batch_response = """1. Thabo: african
2. Pillay: indian
3. Smith: white"""
        
        names = ["Thabo", "Pillay", "Smith"]
        results = self.classifier._parse_batch_response(batch_response, names)
        
        assert len(results) == 3
        assert results[0] == (EthnicityType.AFRICAN, 0.85)
        assert results[1] == (EthnicityType.INDIAN, 0.85)
        assert results[2] == (EthnicityType.WHITE, 0.85)

    def test_parse_batch_response_incomplete(self):
        """Test parsing batch response with missing entries."""
        batch_response = """1. Thabo: african
3. Smith: white"""  # Missing entry 2
        
        names = ["Thabo", "Unknown", "Smith"]
        results = self.classifier._parse_batch_response(batch_response, names)
        
        assert len(results) == 3
        assert results[0] == (EthnicityType.AFRICAN, 0.85)
        assert results[1] == (EthnicityType.UNKNOWN, 0.60)  # Not found in response
        assert results[2] == (EthnicityType.WHITE, 0.85)

    @pytest.mark.asyncio
    async def test_call_claude_success(self):
        """Test successful Claude API call (mocked)."""
        # Mock Claude client
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = self.mock_claude_response
        self.classifier.claude_client = mock_client
        
        parsed_response, llm_details = await self.classifier._call_claude("test prompt")
        
        assert parsed_response["content"] == "african"
        assert llm_details.model_used == "claude-3-5-haiku-20241022"
        assert llm_details.prompt_tokens == 100
        assert llm_details.completion_tokens == 10
        assert llm_details.fallback_used is False
        assert llm_details.total_cost > 0

    @pytest.mark.asyncio
    async def test_call_claude_failure(self):
        """Test Claude API call failure."""
        # Mock Claude client to raise exception
        mock_client = AsyncMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        self.classifier.claude_client = mock_client
        
        with pytest.raises(LLMClassificationError):
            await self.classifier._call_claude("test prompt")

    @pytest.mark.asyncio
    async def test_call_openai_success(self):
        """Test successful OpenAI API call (mocked)."""
        # Mock OpenAI client
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = self.mock_openai_response
        self.classifier.openai_client = mock_client
        
        parsed_response, llm_details = await self.classifier._call_openai("test prompt")
        
        assert parsed_response["content"] == "indian"
        assert llm_details.model_used == "gpt-4o-mini"
        assert llm_details.prompt_tokens == 95
        assert llm_details.completion_tokens == 8
        assert llm_details.fallback_used is True  # OpenAI is fallback
        assert llm_details.total_cost > 0

    @pytest.mark.asyncio
    async def test_classify_name_claude_primary(self):
        """Test single name classification using Claude primary."""
        # Mock Claude client to succeed
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = self.mock_claude_response
        self.classifier.claude_client = mock_client
        
        result = await self.classifier.classify_name("TestName")
        
        assert result is not None
        assert result.ethnicity == EthnicityType.AFRICAN  # Response: "african"
        assert result.method == ClassificationMethod.LLM
        assert result.confidence == 0.85
        assert result.llm_details is not None
        assert result.llm_details.fallback_used is False

    @pytest.mark.asyncio
    async def test_classify_name_fallback_to_openai(self):
        """Test fallback to OpenAI when Claude fails."""
        # Mock Claude to fail, OpenAI to succeed
        mock_claude = AsyncMock()
        mock_claude.messages.create.side_effect = Exception("Claude failed")
        self.classifier.claude_client = mock_claude
        
        mock_openai = AsyncMock()
        mock_openai.chat.completions.create.return_value = self.mock_openai_response
        self.classifier.openai_client = mock_openai
        
        result = await self.classifier.classify_name("TestName")
        
        assert result is not None
        assert result.ethnicity == EthnicityType.INDIAN  # Response: "indian"
        assert result.method == ClassificationMethod.LLM
        assert result.llm_details.fallback_used is True

    @pytest.mark.asyncio
    async def test_classify_name_cost_limit_reached(self):
        """Test classification blocked by cost limits."""
        # Set cost monitor to deny requests
        self.classifier.cost_monitor.session_cost = 2.0  # Exceeds limit of 1.0
        
        result = await self.classifier.classify_name("TestName")
        
        assert result is None  # Should be blocked by cost limit

    @pytest.mark.asyncio
    async def test_classify_name_retry_mechanism(self):
        """Test retry mechanism with exponential backoff."""
        # Mock to fail twice then succeed
        call_count = 0
        
        async def mock_call_claude(prompt):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise LLMClassificationError("Temporary failure")
            return {"content": "african"}, MagicMock()
        
        self.classifier.claude_client = MagicMock()
        
        with patch.object(self.classifier, '_call_claude', side_effect=mock_call_claude):
            with patch('asyncio.sleep'):  # Skip actual sleep for test speed
                result = await self.classifier.classify_name("TestName")
                
                assert call_count == 3  # Failed twice, succeeded on third try
                # Note: result will be None because our mock doesn't return proper details

    @pytest.mark.asyncio
    async def test_classify_batch_optimal_size(self):
        """Test batch classification with research-optimal batch size."""
        names = ["Name1", "Name2", "Name3"] * 10  # 30 names (optimal range)
        
        # Mock Claude client
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "\n".join([f"{i+1}. {name}: african" for i, name in enumerate(names[:25])])
        mock_response.usage.input_tokens = 500
        mock_response.usage.output_tokens = 100
        mock_client.messages.create.return_value = mock_response
        self.classifier.claude_client = mock_client
        
        results = await self.classifier.classify_batch(names, batch_size=25)
        
        assert len(results) == 30
        # Should make 2 batch calls (25 + 5)
        assert mock_client.messages.create.call_count == 2

    @pytest.mark.asyncio
    async def test_classify_batch_cost_limit_blocks(self):
        """Test that batch classification respects cost limits."""
        # Set cost limit to deny
        self.classifier.cost_monitor.session_cost = 2.0
        
        names = ["Name1", "Name2", "Name3"]
        results = await self.classifier.classify_batch(names)
        
        assert len(results) == 3
        assert all(result is None for result in results)

    def test_get_usage_stats(self):
        """Test usage statistics retrieval."""
        # Add some mock usage
        self.classifier.cost_monitor.track_usage(0.001)
        self.classifier.total_response_time = 2500.0
        
        stats = self.classifier.get_usage_stats()
        
        assert "cost_monitoring" in stats
        assert "performance" in stats
        assert "providers" in stats
        assert "research_validation" in stats
        
        assert stats["providers"]["primary"] == "claude-3-5-haiku-20241022"
        assert stats["providers"]["fallback"] == "gpt-4o-mini"
        assert stats["research_validation"]["cost_target_per_classification"] == 0.001

    def test_get_cost_estimate(self):
        """Test cost estimation for batch vs single requests."""
        estimate = self.classifier.get_cost_estimate(100)
        
        assert "num_names" in estimate
        assert "single_requests" in estimate
        assert "batch_requests" in estimate
        assert "research_targets" in estimate
        
        # Batch should be cheaper than single
        assert estimate["batch_requests"]["cost_per_name"] < estimate["single_requests"]["cost_per_name"]
        
        # Should show savings percentage
        assert estimate["batch_requests"]["savings_vs_single"] > 0

    def test_cost_estimate_meets_research_targets(self):
        """Test that cost estimates meet research targets."""
        estimate = self.classifier.get_cost_estimate(1000)
        
        # Research target: <$0.001 per classification
        batch_cost_per_name = estimate["batch_requests"]["cost_per_name"]
        assert batch_cost_per_name <= 0.001, f"Cost {batch_cost_per_name} exceeds research target"
        
        # Should indicate target is met
        assert estimate["research_targets"]["meets_target"] is True


class TestLLMIntegrationScenarios:
    """Test integration scenarios and edge cases."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.classifier = LLMClassifier(
            claude_api_key=None,
            openai_api_key=None,
            cost_limit_per_session=1.0,
        )

    @pytest.mark.asyncio
    async def test_few_shot_learning_improves_accuracy(self):
        """Test that few-shot examples improve classification accuracy."""
        # This would be a more complex test requiring actual API calls
        # For unit testing, we verify the few-shot examples are included
        
        examples = self.classifier._get_few_shot_examples("TestName")
        prompt_with_examples = self.classifier._get_optimized_prompt(
            "TestName", 
            few_shot_examples=examples
        )
        prompt_without_examples = self.classifier._get_optimized_prompt("TestName")
        
        # Prompt with examples should be longer and contain example patterns
        assert len(prompt_with_examples) > len(prompt_without_examples)
        assert "Examples:" in prompt_with_examples

    @pytest.mark.asyncio
    async def test_batch_processing_efficiency(self):
        """Test that batch processing is more efficient than individual calls."""
        names = ["Name1", "Name2", "Name3", "Name4", "Name5"]
        
        # Mock batch processing
        batch_prompt = self.classifier._get_batch_prompt(names)
        individual_prompts = [
            self.classifier._get_optimized_prompt(name) for name in names
        ]
        
        # Batch prompt should be more token-efficient than sum of individual prompts
        total_individual_length = sum(len(prompt) for prompt in individual_prompts)
        assert len(batch_prompt) < total_individual_length * 0.8  # At least 20% savings

    def test_sa_specific_optimization(self):
        """Test South African specific optimizations."""
        prompt = self.classifier._get_optimized_prompt("TestName")
        
        # Should include SA-specific cultural patterns
        assert "Nguni" in prompt
        assert "Tamil" in prompt
        assert "Cape Muslim" in prompt
        assert "Afrikaans" in prompt
        
        # Should use SA ethnicity categories
        assert "cape_malay" in prompt
        assert "coloured" in prompt

    def test_research_validated_token_efficiency(self):
        """Test that prompts meet research-validated token efficiency."""
        # Research target: ~95 tokens for optimized prompts
        base_prompt = self.classifier._get_optimized_prompt("TestName")
        
        # Rough token estimate (1 token ~= 4 characters)
        estimated_tokens = len(base_prompt) / 4
        
        # Should be in efficient range (allowing for few-shot examples)
        assert 80 <= estimated_tokens <= 150, f"Prompt tokens {estimated_tokens} outside efficient range"