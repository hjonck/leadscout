"""Unit tests for phonetic classification module."""


import pytest

from leadscout.classification.dictionaries import EthnicityType
from leadscout.classification.models import PhoneticMatch
from leadscout.classification.phonetic import PhoneticClassifier
from tests.fixtures.sa_test_names import get_phonetic_variants_dataset


class TestPhoneticClassifier:
    """Test suite for PhoneticClassifier class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = PhoneticClassifier()

    def test_initialization(self):
        """Test classifier initialization."""
        assert self.classifier.dictionaries is not None
        assert hasattr(self.classifier, "phonetic_cache")
        assert isinstance(self.classifier.phonetic_cache, dict)
        assert (
            len(self.classifier.phonetic_cache) > 0
        )  # Should have precomputed cache

    def test_jellyfish_availability(self):
        """Test that jellyfish algorithms are available."""
        stats = self.classifier.get_phonetic_stats()
        assert stats["jellyfish_available"] is True

        expected_algorithms = {
            "soundex",
            "metaphone",
            "dmetaphone",
            "nysiis",
            "jaro_winkler",
        }
        available_algorithms = set(stats["algorithms_available"])
        assert expected_algorithms.issubset(available_algorithms)

    @pytest.mark.asyncio
    async def test_phonetic_cache_generation(self):
        """Test that phonetic cache is properly generated."""
        # Cache should be populated on initialization
        assert len(self.classifier.phonetic_cache) > 0

        # Should have entries for all algorithms
        for algorithm in ["soundex", "metaphone", "dmetaphone", "nysiis"]:
            assert algorithm in self.classifier.phonetic_cache
            assert len(self.classifier.phonetic_cache[algorithm]) > 0

    def test_generate_phonetic_codes(self):
        """Test phonetic code generation for names."""
        test_name = "Thabo"
        codes = self.classifier.generate_phonetic_codes(test_name)

        assert isinstance(codes, dict)
        assert "soundex" in codes
        assert "metaphone" in codes
        assert "dmetaphone" in codes
        assert "nysiis" in codes

        # Check codes are strings and not empty
        for algorithm, code in codes.items():
            if (
                code is not None
            ):  # Some algorithms may return None for certain names
                assert isinstance(code, str)
                assert len(code) > 0

    @pytest.mark.asyncio
    async def test_classify_phonetic_variant_african(self):
        """Test classification of African name variants."""
        test_cases = [
            ("Bonganni", EthnicityType.AFRICAN),  # Variant of Bongani
            ("Thapho", EthnicityType.AFRICAN),  # Variant of Thabo
            ("Nomza", EthnicityType.AFRICAN),  # Variant of Nomsa
        ]

        for name, expected_ethnicity in test_cases:
            result = await self.classifier.classify_name(name)
            assert (
                result is not None
            ), f"Failed to classify phonetic variant: {name}"
            assert result.ethnicity == expected_ethnicity
            assert (
                result.confidence >= 0.5
            )  # Lower threshold for phonetic matches
            assert (
                hasattr(result, "phonetic_details")
                and result.phonetic_details is not None
            )

    @pytest.mark.asyncio
    async def test_classify_phonetic_variant_indian(self):
        """Test classification of Indian name variants."""
        test_cases = [
            ("Pilai", EthnicityType.INDIAN),  # Variant of Pillay
            ("Reddi", EthnicityType.INDIAN),  # Variant of Reddy
            ("Naideau", EthnicityType.INDIAN),  # Variant of Naidoo
            ("Patell", EthnicityType.INDIAN),  # Variant of Patel
        ]

        for name, expected_ethnicity in test_cases:
            result = await self.classifier.classify_name(name)
            assert (
                result is not None
            ), f"Failed to classify phonetic variant: {name}"
            assert result.ethnicity == expected_ethnicity
            assert result.confidence >= 0.5

    @pytest.mark.asyncio
    async def test_classify_phonetic_variant_cape_malay(self):
        """Test classification of Cape Malay name variants."""
        test_cases = [
            ("Cassim", EthnicityType.CAPE_MALAY),  # Variant of Cassiem
            ("Hendrix", EthnicityType.CAPE_MALAY),  # Variant of Hendricks
            ("Abdulla", EthnicityType.CAPE_MALAY),  # Variant of Abdullah
        ]

        for name, expected_ethnicity in test_cases:
            result = await self.classifier.classify_name(name)
            assert (
                result is not None
            ), f"Failed to classify phonetic variant: {name}"
            assert result.ethnicity == expected_ethnicity
            assert result.confidence >= 0.5

    @pytest.mark.asyncio
    async def test_classify_phonetic_variant_white(self):
        """Test classification of White name variants."""
        test_cases = [
            ("Boter", EthnicityType.WHITE),  # Variant of Botha
            ("Smyth", EthnicityType.WHITE),  # Variant of Smith
        ]

        for name, expected_ethnicity in test_cases:
            result = await self.classifier.classify_name(name)
            assert (
                result is not None
            ), f"Failed to classify phonetic variant: {name}"
            assert result.ethnicity == expected_ethnicity
            assert result.confidence >= 0.5

    @pytest.mark.asyncio
    async def test_unknown_name_returns_none(self):
        """Test that completely unknown names return None."""
        unknown_names = [
            "Xylophen",
            "Qwertyuiop",
            "Fictional123",
            "CompletelyUnknown",
        ]

        for name in unknown_names:
            result = await self.classifier.classify_name(name)
            assert result is None, f"Should not classify unknown name: {name}"

    @pytest.mark.asyncio
    async def test_phonetic_details_structure(self):
        """Test that phonetic details are properly structured."""
        result = await self.classifier.classify_name(
            "Bonganni"
        )  # Known variant

        assert result is not None
        assert (
            hasattr(result, "phonetic_details")
            and result.phonetic_details is not None
        )

        details = result.phonetic_details
        assert hasattr(details, "matches")
        assert hasattr(details, "top_algorithm")
        assert hasattr(details, "consensus_score")

        assert isinstance(details.matches, list)
        assert len(details.matches) > 0
        assert isinstance(details.top_algorithm, str)
        assert 0.0 <= details.consensus_score <= 1.0

        # Check match structure
        for match in details.matches:
            assert isinstance(match, PhoneticMatch)
            assert hasattr(match, "algorithm")
            assert hasattr(match, "matched_name")
            assert hasattr(match, "matched_ethnicity")
            assert hasattr(match, "similarity_score")

    def test_find_similar_names(self):
        """Test finding similar names functionality."""
        test_name = "Bonganni"
        similar_names = self.classifier.find_similar_names(test_name, limit=5)

        assert isinstance(similar_names, list)
        assert len(similar_names) <= 5

        if similar_names:  # If any matches found
            for match in similar_names:
                assert isinstance(match, PhoneticMatch)
                assert (
                    match.matched_name != test_name
                )  # Should be different from input
                assert 0.0 <= match.similarity_score <= 1.0

    def test_find_similar_names_with_limit(self):
        """Test similar names with different limits."""
        test_name = "Thabo"

        # Test different limits
        for limit in [1, 3, 5, 10]:
            similar_names = self.classifier.find_similar_names(
                test_name, limit=limit
            )
            assert len(similar_names) <= limit

    @pytest.mark.asyncio
    async def test_case_insensitive_phonetic_matching(self):
        """Test that phonetic matching is case insensitive."""
        test_cases = [
            ("bonganni", "Bonganni"),
            ("PILAI", "pilai"),
            ("Reddi", "REDDI"),
        ]

        for name1, name2 in test_cases:
            result1 = await self.classifier.classify_name(name1)
            result2 = await self.classifier.classify_name(name2)

            # Both should give same result (or both None)
            if result1 is None:
                assert result2 is None
            else:
                assert result2 is not None
                assert result1.ethnicity == result2.ethnicity

    @pytest.mark.asyncio
    async def test_performance_benchmark(self):
        """Test phonetic classification performance."""
        import time

        test_names = [
            "Bonganni",  # Should hit phonetic cache
            "Pilai",  # Should hit phonetic cache
            "Xylophen",  # Should fail all algorithms
        ]

        times = []
        for name in test_names:
            start_time = time.time()
            for _ in range(10):  # 10 classifications (async operations)
                await self.classifier.classify_name(name)
            end_time = time.time()

            avg_time_ms = (end_time - start_time) * 1000 / 10
            times.append(avg_time_ms)

        # Should be under 50ms target per classification
        max_time = max(times)
        assert (
            max_time < 50.0
        ), f"Phonetic classification too slow: {max_time:.2f}ms > 50ms target"

    @pytest.mark.asyncio
    async def test_comprehensive_phonetic_variants(self):
        """Test accuracy on comprehensive phonetic variants dataset."""
        phonetic_data = get_phonetic_variants_dataset()

        correct = 0
        total = 0
        failures = []

        for test_case in phonetic_data:
            name = test_case["name"]
            expected = test_case["expected_ethnicity"]

            result = await self.classifier.classify_name(name)

            if result is None:
                failures.append(f"{name} -> None (expected {expected.value})")
            elif result.ethnicity == expected:
                correct += 1
            else:
                failures.append(
                    f"{name} -> {result.ethnicity.value} (expected {expected.value})"
                )

            total += 1

        accuracy = correct / total if total > 0 else 0

        # Print failures for debugging
        if failures:
            print(f"\nPhonetic classification failures ({len(failures)}):")
            for failure in failures[:10]:  # Show first 10
                print(f"  {failure}")
            if len(failures) > 10:
                print(f"  ... and {len(failures) - 10} more")

        print(
            f"\nPhonetic variants accuracy: {correct}/{total} ({accuracy:.1%})"
        )

        # Should achieve >70% accuracy on phonetic variants
        assert (
            accuracy >= 0.70
        ), f"Phonetic variants accuracy {accuracy:.1%} below 70% target"

    def test_phonetic_cache_efficiency(self):
        """Test that phonetic cache improves efficiency."""
        # Test that cache is populated
        assert len(self.classifier.phonetic_cache) > 0

        # Test cache coverage
        for algorithm in ["soundex", "metaphone", "dmetaphone", "nysiis"]:
            assert algorithm in self.classifier.phonetic_cache
            cache_size = len(self.classifier.phonetic_cache[algorithm])
            assert (
                cache_size > 100
            ), f"{algorithm} cache too small: {cache_size}"

    @pytest.mark.asyncio
    async def test_multiple_algorithm_consensus(self):
        """Test that multiple algorithms contribute to consensus."""
        result = await self.classifier.classify_name(
            "Bonganni"
        )  # Known good variant

        if (
            result
            and hasattr(result, "phonetic_details")
            and result.phonetic_details
        ):
            # Should have matches from multiple algorithms
            algorithms_used = {
                match.algorithm for match in result.phonetic_details.matches
            }
            assert (
                len(algorithms_used) >= 2
            ), "Should use multiple algorithms for consensus"

            # Consensus score should reflect agreement
            assert result.phonetic_details.consensus_score > 0.0

    @pytest.mark.asyncio
    async def test_confidence_calculation(self):
        """Test confidence calculation for phonetic matches."""
        # Test strong phonetic match
        strong_result = await self.classifier.classify_name(
            "Bonganni"
        )  # Close variant
        if strong_result:
            assert strong_result.confidence >= 0.5

        # Test weaker phonetic match (if any)
        # Note: All our test variants are quite strong, so this may not trigger

    def test_get_phonetic_stats(self):
        """Test phonetic statistics reporting."""
        stats = self.classifier.get_phonetic_stats()

        assert isinstance(stats, dict)
        assert "jellyfish_available" in stats
        assert "algorithms_available" in stats
        assert "cached_phonetic_mappings" in stats

        assert stats["jellyfish_available"] is True
        assert len(stats["algorithms_available"]) >= 4  # At least 4 algorithms

        # Check cache statistics
        cache_stats = stats["cached_phonetic_mappings"]
        for algorithm in ["soundex", "metaphone", "dmetaphone", "nysiis"]:
            assert algorithm in cache_stats
            assert cache_stats[algorithm] > 0

    @pytest.mark.asyncio
    async def test_empty_and_invalid_input_phonetic(self):
        """Test handling of empty and invalid input in phonetic classifier."""
        invalid_inputs = ["", " ", "   "]

        for invalid_input in invalid_inputs:
            result = await self.classifier.classify_name(invalid_input)
            assert result is None

    @pytest.mark.asyncio
    async def test_single_character_phonetic(self):
        """Test handling of single character names in phonetic classifier."""
        single_chars = ["A", "B", "Z", "1"]

        for char in single_chars:
            result = await self.classifier.classify_name(char)
            assert result is None  # Single characters should not classify

    @pytest.mark.asyncio
    async def test_algorithm_specific_strengths(self):
        """Test that different algorithms excel at different types of variants."""
        # This test verifies that our multi-algorithm approach captures
        # different types of phonetic variations

        test_variants = [
            "Bonganni",  # Double consonant variation
            "Thapho",  # Consonant substitution
            "Pilai",  # Vowel ending variation
            "Smyth",  # Historical spelling variation
        ]

        algorithm_hits = {
            algo: 0
            for algo in ["soundex", "metaphone", "dmetaphone", "nysiis"]
        }

        for variant in test_variants:
            result = await self.classifier.classify_name(variant)
            if (
                result
                and hasattr(result, "phonetic_details")
                and result.phonetic_details
            ):
                for match in result.phonetic_details.matches:
                    algorithm_hits[match.algorithm] += 1

        # Each algorithm should contribute to at least one match
        working_algorithms = sum(
            1 for hits in algorithm_hits.values() if hits > 0
        )
        assert (
            working_algorithms >= 3
        ), f"Only {working_algorithms} algorithms contributing to matches"
