"""Unit tests for SA name dictionaries."""

import pytest
from leadscout.classification.dictionaries import (
    NameDictionaries, EthnicityType, NameEntry, get_dictionaries
)


class TestNameDictionaries:
    """Test suite for NameDictionaries class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.dictionaries = NameDictionaries()
    
    def test_dictionaries_loaded(self):
        """Test that all dictionaries are loaded."""
        assert len(self.dictionaries.dictionaries) == 5
        assert EthnicityType.AFRICAN in self.dictionaries.dictionaries
        assert EthnicityType.INDIAN in self.dictionaries.dictionaries
        assert EthnicityType.CAPE_MALAY in self.dictionaries.dictionaries
        assert EthnicityType.COLOURED in self.dictionaries.dictionaries
        assert EthnicityType.WHITE in self.dictionaries.dictionaries
    
    def test_african_names_loaded(self):
        """Test that African names are properly loaded."""
        african_dict = self.dictionaries.dictionaries[EthnicityType.AFRICAN]
        
        # Test some known Nguni names
        assert "mthembu" in african_dict
        assert "mandela" in african_dict
        assert "bongani" in african_dict
        assert "thabo" in african_dict
        
        # Verify metadata
        mthembu_entry = african_dict["mthembu"]
        assert mthembu_entry.ethnicity == EthnicityType.AFRICAN
        assert mthembu_entry.confidence >= 0.90
        assert mthembu_entry.linguistic_origin in ["Nguni", "Sotho", "Venda"]
    
    def test_indian_names_loaded(self):
        """Test that Indian names are properly loaded."""
        indian_dict = self.dictionaries.dictionaries[EthnicityType.INDIAN]
        
        # Test Tamil names
        assert "pillay" in indian_dict
        assert "naidoo" in indian_dict
        assert "reddy" in indian_dict
        
        # Test Gujarati names
        assert "patel" in indian_dict
        assert "shah" in indian_dict
        
        # Verify metadata
        pillay_entry = indian_dict["pillay"]
        assert pillay_entry.ethnicity == EthnicityType.INDIAN
        assert pillay_entry.confidence >= 0.90
        assert pillay_entry.linguistic_origin in ["Tamil", "Telugu", "Hindi", "Gujarati"]
    
    def test_cape_malay_names_loaded(self):
        """Test that Cape Malay names are properly loaded."""
        cape_malay_dict = self.dictionaries.dictionaries[EthnicityType.CAPE_MALAY]
        
        assert "cassiem" in cape_malay_dict
        assert "hendricks" in cape_malay_dict
        assert "adams" in cape_malay_dict
        assert "abdullah" in cape_malay_dict
        assert "fatima" in cape_malay_dict
        
        # Verify metadata
        cassiem_entry = cape_malay_dict["cassiem"]
        assert cassiem_entry.ethnicity == EthnicityType.CAPE_MALAY
        assert cassiem_entry.regional_pattern == "Western Cape"
    
    def test_coloured_names_loaded(self):
        """Test that Coloured names including month surnames are loaded."""
        coloured_dict = self.dictionaries.dictionaries[EthnicityType.COLOURED]
        
        # Test month surnames
        assert "september" in coloured_dict
        assert "april" in coloured_dict
        assert "october" in coloured_dict
        assert "january" in coloured_dict
        
        # Test other Coloured surnames
        assert "brown" in coloured_dict
        assert "booysen" in coloured_dict
        
        # Verify month surname metadata
        september_entry = coloured_dict["september"]
        assert september_entry.ethnicity == EthnicityType.COLOURED
        assert september_entry.confidence >= 0.90
        assert "slave naming" in september_entry.historical_context.lower()
    
    def test_white_names_loaded(self):
        """Test that White (Afrikaans/English) names are loaded."""
        white_dict = self.dictionaries.dictionaries[EthnicityType.WHITE]
        
        # Test Afrikaans names
        assert "van der merwe" in white_dict
        assert "botha" in white_dict
        assert "johannes" in white_dict
        assert "pieter" in white_dict
        
        # Test English names
        assert "smith" in white_dict
        assert "jones" in white_dict
        
        # Verify metadata
        botha_entry = white_dict["botha"]
        assert botha_entry.ethnicity == EthnicityType.WHITE
        assert botha_entry.linguistic_origin in ["Afrikaans", "English"]
    
    def test_month_surname_detection(self):
        """Test month surname detection method."""
        assert self.dictionaries.is_month_surname("September")
        assert self.dictionaries.is_month_surname("april")
        assert self.dictionaries.is_month_surname("OCTOBER")
        assert not self.dictionaries.is_month_surname("Smith")
        assert not self.dictionaries.is_month_surname("Mthembu")
    
    def test_lookup_name_single_match(self):
        """Test looking up a name with single ethnicity match."""
        result = self.dictionaries.lookup_name("Mthembu")
        assert result is not None
        assert result.ethnicity == EthnicityType.AFRICAN
        assert result.confidence >= 0.90
    
    def test_lookup_name_not_found(self):
        """Test looking up a name not in dictionaries."""
        result = self.dictionaries.lookup_name("XyzUnknown")
        assert result is None
    
    def test_lookup_name_specific_ethnicity(self):
        """Test looking up name in specific ethnicity dictionary."""
        result = self.dictionaries.lookup_name("pillay", EthnicityType.INDIAN)
        assert result is not None
        assert result.ethnicity == EthnicityType.INDIAN
        
        # Should not find African name in Indian dictionary
        result = self.dictionaries.lookup_name("mthembu", EthnicityType.INDIAN)
        assert result is None
    
    def test_get_name_metadata_single_match(self):
        """Test getting complete metadata for name with single match."""
        metadata = self.dictionaries.get_name_metadata("Cassiem")
        assert metadata is not None
        assert metadata.name == "Cassiem"
        assert metadata.primary_ethnicity == EthnicityType.CAPE_MALAY
        assert len(metadata.matches) == 1
        assert not metadata.conflicting_origins
    
    def test_get_name_metadata_no_match(self):
        """Test getting metadata for unknown name."""
        metadata = self.dictionaries.get_name_metadata("UnknownName")
        assert metadata is None
    
    def test_get_ethnicity_coverage(self):
        """Test ethnicity coverage statistics."""
        coverage = self.dictionaries.get_ethnicity_coverage()
        
        assert isinstance(coverage, dict)
        assert len(coverage) == 5
        
        # Should have substantial coverage for each ethnicity
        assert coverage[EthnicityType.AFRICAN] > 50
        assert coverage[EthnicityType.INDIAN] > 30
        assert coverage[EthnicityType.CAPE_MALAY] > 20
        assert coverage[EthnicityType.COLOURED] > 15
        assert coverage[EthnicityType.WHITE] > 30
        
        # Total should be around 366 names
        total = sum(coverage.values())
        assert 350 <= total <= 400
    
    def test_name_entry_structure(self):
        """Test that NameEntry objects have proper structure."""
        african_dict = self.dictionaries.dictionaries[EthnicityType.AFRICAN]
        entry = african_dict["mthembu"]
        
        assert isinstance(entry, NameEntry)
        assert entry.name == "Mthembu"
        assert entry.ethnicity == EthnicityType.AFRICAN
        assert 0.0 <= entry.confidence <= 1.0
        assert entry.frequency > 0
        assert entry.name_type in ["forename", "surname", "both"]
        
        if entry.linguistic_origin:
            assert isinstance(entry.linguistic_origin, str)
        if entry.regional_pattern:
            assert isinstance(entry.regional_pattern, str)
        if entry.historical_context:
            assert isinstance(entry.historical_context, str)
    
    def test_global_dictionaries_singleton(self):
        """Test that get_dictionaries returns singleton instance."""
        dict1 = get_dictionaries()
        dict2 = get_dictionaries()
        assert dict1 is dict2
    
    def test_case_insensitive_lookup(self):
        """Test that lookups are case insensitive."""
        # Test various cases
        result1 = self.dictionaries.lookup_name("MTHEMBU")
        result2 = self.dictionaries.lookup_name("mthembu") 
        result3 = self.dictionaries.lookup_name("Mthembu")
        
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None
        assert result1.ethnicity == result2.ethnicity == result3.ethnicity
    
    def test_whitespace_handling(self):
        """Test that whitespace is handled properly."""
        result1 = self.dictionaries.lookup_name("  Mthembu  ")
        result2 = self.dictionaries.lookup_name("Mthembu")
        
        assert result1 is not None
        assert result2 is not None
        assert result1.ethnicity == result2.ethnicity
    
    def test_confidence_scores_valid(self):
        """Test that all confidence scores are valid."""
        for ethnicity, dictionary in self.dictionaries.dictionaries.items():
            for name, entry in dictionary.items():
                assert 0.0 <= entry.confidence <= 1.0, f"Invalid confidence for {name}: {entry.confidence}"
    
    def test_no_duplicate_entries(self):
        """Test that there are no duplicate entries across ethnicities for problematic names."""
        # Note: Some names may legitimately appear in multiple ethnicities
        # This test is to ensure we're aware of such cases
        
        all_names = set()
        duplicates = set()
        
        for ethnicity, dictionary in self.dictionaries.dictionaries.items():
            for name in dictionary.keys():
                if name in all_names:
                    duplicates.add(name)
                all_names.add(name)
        
        # Log duplicates for awareness (some may be legitimate)
        if duplicates:
            print(f"Names appearing in multiple dictionaries: {duplicates}")
        
        # Common legitimate duplicates we expect
        expected_duplicates = {"brown", "adams", "williams"}  # Names that can span ethnicities
        unexpected_duplicates = duplicates - expected_duplicates
        
        # Should have very few unexpected duplicates
        assert len(unexpected_duplicates) < 5, f"Too many unexpected duplicate names: {unexpected_duplicates}"