"""Unit tests for rule-based classification module."""

import pytest

from leadscout.classification.dictionaries import EthnicityType
from leadscout.classification.models import ConfidenceLevel
from leadscout.classification.rules import RuleBasedClassifier
from tests.fixtures.sa_test_names import get_test_dataset


class TestRuleBasedClassifier:
    """Test suite for RuleBasedClassifier class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = RuleBasedClassifier()

    def test_initialization(self):
        """Test classifier initialization."""
        assert self.classifier.dictionaries is not None
        assert hasattr(self.classifier, "month_surnames")
        assert isinstance(self.classifier.month_surnames, set)
        assert len(self.classifier.month_surnames) == 12

    def test_classify_single_word_african_name(self):
        """Test classification of single African names."""
        result = self.classifier.classify_name("Thabo")
        assert result is not None
        assert result.ethnicity == EthnicityType.AFRICAN
        assert result.confidence >= 0.8
        assert result.confidence_level in [
            ConfidenceLevel.HIGH,
            ConfidenceLevel.VERY_HIGH,
        ]

    def test_classify_single_word_indian_name(self):
        """Test classification of single Indian names."""
        result = self.classifier.classify_name("Pillay")
        assert result is not None
        assert result.ethnicity == EthnicityType.INDIAN
        assert result.confidence >= 0.8

    def test_classify_single_word_cape_malay_name(self):
        """Test classification of single Cape Malay names."""
        result = self.classifier.classify_name("Cassiem")
        assert result is not None
        assert result.ethnicity == EthnicityType.CAPE_MALAY
        assert result.confidence >= 0.8

    def test_classify_month_surname(self):
        """Test classification of month surnames (Coloured)."""
        month_names = ["September", "April", "October", "January", "December"]

        for month in month_names:
            result = self.classifier.classify_name(month)
            assert result is not None
            assert result.ethnicity == EthnicityType.COLOURED
            assert (
                result.confidence >= 0.9
            )  # Month surnames are very high confidence

    def test_classify_full_name_african(self):
        """Test classification of full African names."""
        test_cases = [
            "Thabo Mthembu",
            "Bongani Nkomo",
            "Nomsa Dlamini",
            "Nelson Mandela",
        ]

        for name in test_cases:
            result = self.classifier.classify_name(name)
            assert result is not None, f"Failed to classify {name}"
            assert result.ethnicity == EthnicityType.AFRICAN
            assert result.confidence >= 0.8

    def test_classify_full_name_indian(self):
        """Test classification of full Indian names."""
        test_cases = [
            "Priya Pillay",
            "Rajesh Naidoo",
            "Ashwin Patel",
            "Kavitha Reddy",
        ]

        for name in test_cases:
            result = self.classifier.classify_name(name)
            assert result is not None, f"Failed to classify {name}"
            assert result.ethnicity == EthnicityType.INDIAN
            assert result.confidence >= 0.8

    def test_classify_full_name_cape_malay(self):
        """Test classification of full Cape Malay names."""
        test_cases = [
            "Abdullah Cassiem",
            "Fatima Hendricks",
            "Mohamed Adams",
            "Ayesha Isaacs",
        ]

        for name in test_cases:
            result = self.classifier.classify_name(name)
            assert result is not None, f"Failed to classify {name}"
            assert result.ethnicity == EthnicityType.CAPE_MALAY
            assert result.confidence >= 0.8

    def test_classify_full_name_white(self):
        """Test classification of full White names."""
        test_cases = [
            "Pieter van der Merwe",
            "Johannes Botha",
            "John Smith",
            "Anna du Plessis",
        ]

        for name in test_cases:
            result = self.classifier.classify_name(name)
            assert result is not None, f"Failed to classify {name}"
            assert result.ethnicity == EthnicityType.WHITE
            assert result.confidence >= 0.8

    def test_classify_coloured_names(self):
        """Test classification of Coloured names."""
        test_cases = [
            "John September",
            "Mary April",
            "David October",
            "Sharon Booysen",
        ]

        for name in test_cases:
            result = self.classifier.classify_name(name)
            assert result is not None, f"Failed to classify {name}"
            assert result.ethnicity == EthnicityType.COLOURED
            assert result.confidence >= 0.8

    def test_unknown_name_returns_none(self):
        """Test that unknown names return None."""
        unknown_names = [
            "Xyz Unknown",
            "Fictional Person",
            "Nonexistent Name",
            "Zzz Test",
        ]

        for name in unknown_names:
            result = self.classifier.classify_name(name)
            assert result is None, f"Should not classify unknown name: {name}"

    def test_case_insensitive_classification(self):
        """Test that classification is case insensitive."""
        test_cases = [
            ("thabo", EthnicityType.AFRICAN),
            ("PILLAY", EthnicityType.INDIAN),
            ("cassiem", EthnicityType.CAPE_MALAY),
            ("september", EthnicityType.COLOURED),
            ("BOTHA", EthnicityType.WHITE),
        ]

        for name, expected_ethnicity in test_cases:
            result = self.classifier.classify_name(name)
            assert result is not None, f"Failed to classify {name}"
            assert result.ethnicity == expected_ethnicity

    def test_whitespace_handling(self):
        """Test that extra whitespace is handled properly."""
        test_cases = [
            "  Thabo  ",
            " Thabo Mthembu ",
            "Thabo\t\tMthembu",
            "  Priya   Pillay  ",
        ]

        for name in test_cases:
            result = self.classifier.classify_name(name)
            assert (
                result is not None
            ), f"Failed to handle whitespace in: '{name}'"

    def test_priority_logic_african_dominance(self):
        """Test priority logic - African names get precedence."""
        # Test a name that could be ambiguous but African should win
        result = self.classifier.classify_name(
            "Thabo Adams"
        )  # Thabo=African, Adams=Cape Malay
        assert result is not None
        assert (
            result.ethnicity == EthnicityType.AFRICAN
        )  # African should take priority

    def test_priority_logic_indian_over_others(self):
        """Test priority logic - Indian names have priority over Cape Malay/Coloured/White."""
        result = self.classifier.classify_name(
            "Priya Brown"
        )  # Priya=Indian, Brown=Coloured/White
        assert result is not None
        assert result.ethnicity == EthnicityType.INDIAN

    def test_empty_and_invalid_input(self):
        """Test handling of empty and invalid input."""
        invalid_inputs = ["", " ", None, "   "]

        for invalid_input in invalid_inputs:
            if invalid_input is None:
                with pytest.raises(TypeError):
                    self.classifier.classify_name(invalid_input)
            else:
                result = self.classifier.classify_name(invalid_input)
                assert result is None

    def test_single_character_names(self):
        """Test handling of single character names."""
        single_chars = ["A", "B", "Z", "1"]

        for char in single_chars:
            result = self.classifier.classify_name(char)
            assert result is None  # Single characters should not classify

    def test_very_long_names(self):
        """Test handling of very long names."""
        long_name = (
            "This is a very long name that should still be processed correctly"
        )
        result = self.classifier.classify_name(long_name)
        # Should handle gracefully, may or may not classify

    def test_get_coverage_stats(self):
        """Test coverage statistics method."""
        stats = self.classifier.get_coverage_stats()

        assert isinstance(stats, dict)
        assert "total_names" in stats
        assert "ethnicity_breakdown" in stats

        assert stats["total_names"] > 300  # Should have 366+ names

        # Check all ethnicities are present
        breakdown = stats["ethnicity_breakdown"]
        for ethnicity in EthnicityType:
            if ethnicity != EthnicityType.UNKNOWN:
                assert ethnicity in breakdown
                assert breakdown[ethnicity] > 0

    def test_month_surname_detection(self):
        """Test month surname detection."""
        assert self.classifier._is_month_surname("September")
        assert self.classifier._is_month_surname("april")
        assert self.classifier._is_month_surname("OCTOBER")
        assert not self.classifier._is_month_surname("Smith")
        assert not self.classifier._is_month_surname("Mthembu")

    def test_name_parts_extraction(self):
        """Test name parts extraction."""
        test_cases = [
            ("John Smith", ["john", "smith"]),
            ("  Mary  Jane  ", ["mary", "jane"]),
            ("Pieter van der Merwe", ["pieter", "van", "der", "merwe"]),
            ("Single", ["single"]),
        ]

        for name, expected_parts in test_cases:
            parts = self.classifier._extract_name_parts(name)
            assert parts == expected_parts

    def test_performance_benchmark(self):
        """Test that classification performance meets targets."""
        import time

        test_names = [
            "Thabo Mthembu",  # Should hit rules immediately
            "Priya Pillay",  # Should hit rules immediately
            "SingleUnknown",  # Should fail rules quickly (single word)
        ]

        times = []
        for name in test_names:
            start_time = time.time()
            for _ in range(100):  # 100 classifications
                try:
                    self.classifier.classify_name(name)
                except Exception:
                    # Expected for unknown names - still measure the time
                    pass
            end_time = time.time()

            avg_time_ms = (end_time - start_time) * 1000 / 100
            times.append(avg_time_ms)

        # Print timing results for debugging
        for i, name in enumerate(test_names):
            print(f"{name}: {times[i]:.2f}ms avg")

        # All should be under 10ms target
        max_time = max(times)
        assert (
            max_time < 10.0
        ), f"Classification too slow: {max_time:.2f}ms > 10ms target"

    def test_comprehensive_sa_dataset(self):
        """Test classification accuracy on comprehensive SA dataset."""
        test_data = get_test_dataset()

        correct = 0
        total = 0
        classification_errors = 0
        failures = []
        errors = []

        for test_case in test_data:
            name = test_case["name"]
            expected = test_case["expected_ethnicity"]

            try:
                result = self.classifier.classify_name(name)

                if result is None:
                    failures.append(
                        f"{name} -> None (expected {expected.value})"
                    )
                elif result.ethnicity == expected:
                    correct += 1
                else:
                    failures.append(
                        f"{name} -> {result.ethnicity.value} (expected {expected.value})"
                    )

                total += 1

            except Exception as e:
                # Count classification errors separately
                classification_errors += 1
                errors.append(f"{name} -> ERROR: {str(e)[:100]}...")

        accuracy = correct / total if total > 0 else 0
        coverage = total / len(test_data) if len(test_data) > 0 else 0

        # Print detailed results
        print(f"\nRule-based classification results:")
        print(f"Total test cases: {len(test_data)}")
        print(f"Successfully classified: {total}")
        print(f"Classification errors: {classification_errors}")
        print(f"Coverage: {coverage:.1%}")
        print(f"Accuracy (on classified): {correct}/{total} ({accuracy:.1%})")

        # Print some failures for debugging
        if failures:
            print(f"\nClassification failures ({len(failures)}):")
            for failure in failures[:5]:  # Show first 5
                print(f"  {failure}")
            if len(failures) > 5:
                print(f"  ... and {len(failures) - 5} more")

        # Print some errors for debugging
        if errors:
            print(f"\nClassification errors ({len(errors)}):")
            for error in errors[:3]:  # Show first 3
                print(f"  {error}")
            if len(errors) > 3:
                print(f"  ... and {len(errors) - 3} more")

        # Adjust target based on coverage - if we can classify it, should be >95% accurate
        # But we expect some names not to be in our dictionary
        expected_coverage = 0.80  # Expect to classify 80% of test names
        assert (
            coverage >= expected_coverage
        ), f"Coverage {coverage:.1%} below {expected_coverage:.1%} target"

        # For names we can classify, should achieve >95% accuracy
        if total > 0:
            assert (
                accuracy >= 0.95
            ), f"Rule-based accuracy {accuracy:.1%} below 95% target"

    def test_ethnicity_specific_accuracy(self):
        """Test accuracy for each ethnicity separately."""
        test_data = get_test_dataset()

        ethnicity_stats = {}
        for ethnicity in EthnicityType:
            if ethnicity == EthnicityType.UNKNOWN:
                continue
            ethnicity_stats[ethnicity] = {
                "correct": 0,
                "total": 0,
                "errors": 0,
            }

        for test_case in test_data:
            name = test_case["name"]
            expected = test_case["expected_ethnicity"]

            try:
                result = self.classifier.classify_name(name)

                ethnicity_stats[expected]["total"] += 1
                if result and result.ethnicity == expected:
                    ethnicity_stats[expected]["correct"] += 1

            except Exception as e:
                ethnicity_stats[expected]["errors"] += 1

        # Check each ethnicity meets accuracy target
        print(f"\nEthnicity-specific accuracy:")
        for ethnicity, stats in ethnicity_stats.items():
            if stats["total"] > 0:
                accuracy = stats["correct"] / stats["total"]
                print(
                    f"{ethnicity.value}: {stats['correct']}/{stats['total']} ({accuracy:.1%}) [errors: {stats['errors']}]"
                )

                # Ethnicities with good coverage should have >90% accuracy
                if (
                    stats["total"] >= 5
                ):  # Only check ethnicities with reasonable test coverage
                    assert (
                        accuracy >= 0.90
                    ), f"{ethnicity.value} accuracy {accuracy:.1%} below 90%"
            elif stats["errors"] > 0:
                print(
                    f"{ethnicity.value}: 0/0 (N/A) [errors: {stats['errors']}]"
                )
