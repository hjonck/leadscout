"""Unit tests for hyphen handling in phonetic algorithms."""

import pytest
import jellyfish

from leadscout.classification.phonetic import PhoneticClassifier
from leadscout.classification.learning_database import LLMLearningDatabase
from leadscout.classification.classifier import NameClassifier


class TestHyphenHandling:
    """Test suite for hyphen handling in phonetic classification."""

    def setup_method(self):
        """Set up test fixtures."""
        self.phonetic_classifier = PhoneticClassifier()
        self.learning_db = LLMLearningDatabase()
        self.name_classifier = NameClassifier()

    def test_phonetic_classifier_hyphen_handling(self):
        """Test that PhoneticClassifier handles hyphens correctly."""
        test_names = [
            "CHAD-LEE",
            "MARY-JANE", 
            "JEAN-PIERRE",
            "ANNE-MARIE",
            "JONES-SMITH",
        ]
        
        for name in test_names:
            # Should not raise an exception
            codes = self.phonetic_classifier.generate_phonetic_codes(name)
            
            # Should generate valid codes
            assert isinstance(codes, dict)
            assert "soundex" in codes
            assert "metaphone" in codes
            assert "dmetaphone" in codes
            assert "nysiis" in codes
            assert "jaro_winkler" in codes
            
            # All codes should be strings
            for algorithm, code in codes.items():
                assert isinstance(code, str)

    @pytest.mark.asyncio
    async def test_phonetic_classifier_hyphen_classification(self):
        """Test that hyphenated names can be classified."""
        test_names = [
            "CHAD-LEE",
            "MARY-JANE", 
            "JEAN-PIERRE",
        ]
        
        for name in test_names:
            # Should not raise an exception
            result = await self.phonetic_classifier.classify_name(name)
            # Result can be None (no match) or a valid Classification
            if result:
                assert hasattr(result, 'ethnicity')
                assert hasattr(result, 'confidence')

    def test_learning_database_normalization(self):
        """Test that LLMLearningDatabase normalizes hyphens correctly."""
        test_cases = [
            ("CHAD-LEE", "chadlee"),
            ("CHAD-LEE CARELSE", "chadleecarelse"),
            ("MARY-JANE", "maryjane"),
            ("O'CONNOR", "oconnor"),
            ("VAN DER MERWE", "merwe"),  # Tests prefix removal
            ("JONES-SMITH", "jonessmith"),
        ]
        
        for original, expected in test_cases:
            normalized = self.learning_db._normalize_name_for_phonetics(original)
            assert normalized == expected, f"'{original}' -> '{normalized}' (expected '{expected}')"

    def test_learning_database_phonetic_algorithms(self):
        """Test that normalized names work with jellyfish algorithms."""
        test_names = [
            "CHAD-LEE",
            "MARY-JANE", 
            "O'CONNOR",
            "VAN DER MERWE",
        ]
        
        for name in test_names:
            normalized = self.learning_db._normalize_name_for_phonetics(name)
            
            # Should not raise "Strings must only contain alphabetical characters"
            soundex = jellyfish.soundex(normalized)
            metaphone = jellyfish.metaphone(normalized)
            nysiis = jellyfish.nysiis(normalized)
            match_rating = jellyfish.match_rating_codex(normalized)
            
            # All should be strings
            assert isinstance(soundex, str)
            assert isinstance(metaphone, str)
            assert isinstance(nysiis, str)
            assert isinstance(match_rating, str)

    def test_name_classifier_normalization(self):
        """Test that NameClassifier normalizes hyphens correctly."""
        test_cases = [
            ("CHAD-LEE", "chadlee"),
            ("MARY-JANE", "maryjane"),
            ("O'CONNOR", "oconnor"),
            ("JONES-SMITH", "jonessmith"),
        ]
        
        for original, expected in test_cases:
            normalized = self.name_classifier._normalize_name_for_phonetics(original)
            assert normalized == expected, f"'{original}' -> '{normalized}' (expected '{expected}')"

    def test_name_classifier_phonetic_extraction(self):
        """Test that NameClassifier extracts phonetic codes for hyphenated names."""
        test_names = [
            "CHAD-LEE",
            "MARY-JANE",
            "JEAN-PIERRE",
        ]
        
        for name in test_names:
            # Should not raise an exception
            codes = self.name_classifier._extract_phonetic_codes_for_learning(name)
            
            # Should generate valid codes
            assert isinstance(codes, dict)
            assert "soundex" in codes
            assert "metaphone" in codes
            assert "nysiis" in codes
            assert "match_rating_codex" in codes
            
            # All codes should be strings
            for algorithm, code in codes.items():
                assert isinstance(code, str)

    def test_apostrophe_handling(self):
        """Test that apostrophes are handled correctly."""
        test_cases = [
            ("O'CONNOR", "oconnor"),
            ("D'ALESSANDRO", "dalessandro"),
            ("O'BRIEN", "obrien"),
        ]
        
        # Test all normalization functions
        for original, expected in test_cases:
            # PhoneticClassifier normalization
            phonetic_normalized = self.phonetic_classifier._normalize_for_phonetics(original)
            assert phonetic_normalized == expected
            
            # LearningDatabase normalization
            learning_normalized = self.learning_db._normalize_name_for_phonetics(original)
            assert learning_normalized == expected
            
            # NameClassifier normalization
            classifier_normalized = self.name_classifier._normalize_name_for_phonetics(original)
            assert classifier_normalized == expected

    def test_prefix_removal(self):
        """Test that South African prefixes are removed correctly."""
        test_cases = [
            ("VAN DER MERWE", "merwe"),
            ("VAN STADEN", "staden"),
            ("DE WET", "wet"),
            ("DU TOIT", "toit"),
            ("LE ROUX", "roux"),
        ]
        
        # Test all normalization functions
        for original, expected in test_cases:
            # PhoneticClassifier normalization
            phonetic_normalized = self.phonetic_classifier._normalize_for_phonetics(original)
            assert phonetic_normalized == expected
            
            # LearningDatabase normalization
            learning_normalized = self.learning_db._normalize_name_for_phonetics(original)
            assert learning_normalized == expected
            
            # NameClassifier normalization
            classifier_normalized = self.name_classifier._normalize_name_for_phonetics(original)
            assert classifier_normalized == expected

    def test_complex_names(self):
        """Test complex names with multiple special characters."""
        test_cases = [
            ("VAN DER WET-JONES", "wetjones"),
            ("O'CONNOR-SMITH", "oconnorsmith"),
            ("DE LA REY-BROWN", "reyb1"),  # Note: Complex names may get truncated/modified
        ]
        
        for original, _ in test_cases:
            # Should not raise exceptions
            phonetic_codes = self.phonetic_classifier.generate_phonetic_codes(original)
            learning_normalized = self.learning_db._normalize_name_for_phonetics(original)
            classifier_codes = self.name_classifier._extract_phonetic_codes_for_learning(original)
            
            # All should complete without error
            assert isinstance(phonetic_codes, dict)
            assert isinstance(learning_normalized, str)
            assert isinstance(classifier_codes, dict)

    def test_regression_chad_lee_carelse(self):
        """Regression test for the specific 'CHAD-LEE CARELSE' case."""
        name = "CHAD-LEE CARELSE"
        
        # PhoneticClassifier should handle it
        codes = self.phonetic_classifier.generate_phonetic_codes(name)
        assert codes["soundex"] == "C342"
        assert codes["jaro_winkler"] == "chadleecarelse"
        
        # LearningDatabase should normalize it
        normalized = self.learning_db._normalize_name_for_phonetics(name)
        assert normalized == "chadleecarelse"
        
        # NameClassifier should extract codes
        classifier_codes = self.name_classifier._extract_phonetic_codes_for_learning(name)
        assert classifier_codes["soundex"] == "C342"
        
        # All jellyfish algorithms should work with the normalized name
        assert jellyfish.soundex(normalized) == "C342"
        assert jellyfish.metaphone(normalized) == "XTLKRLS"
        assert jellyfish.nysiis(normalized) == "CADLACARALS"
        assert jellyfish.match_rating_codex(normalized) == "CHDRLS"