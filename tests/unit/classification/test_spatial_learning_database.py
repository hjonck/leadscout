"""
Tests for spatial learning database functionality.

Tests the spatial ethnicity learning system that extracts patterns from
human confirmations to enhance ethnicity predictions through geographic
context and name-place correlations.
"""

import asyncio
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from src.leadscout.classification.spatial_learning_database import (
    SpatialLearningDatabase,
    SpatialEthnicityPattern,
    ConfirmationRecord
)
from src.leadscout.classification.models import Classification, ClassificationMethod, EthnicityType


class TestSpatialLearningDatabase:
    """Test suite for spatial learning database functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_spatial.db"
            yield SpatialLearningDatabase(db_path)
    
    @pytest.fixture
    def sample_confirmation_record(self, temp_db):
        """Create sample confirmation record for testing."""
        # Generate proper spatial hash using the database method
        spatial_hash = temp_db.generate_spatial_context_hash(
            "Thabo Mthembu", "Sandton", "Johannesburg", "Gauteng"
        )
        
        return ConfirmationRecord(
            confirmation_id="test_conf_001",
            source_file_identifier="test_file_abc123",
            source_row_number=25,
            source_job_id="job_test_001",
            original_entity_name="Test Company (Pty) Ltd",
            original_director_name="Thabo Mthembu",
            original_registered_address="123 Main Street",
            original_registered_city="Johannesburg",
            original_registered_province="Gauteng",
            canonical_suburb="Sandton",
            canonical_city="Johannesburg", 
            canonical_province="Gauteng",
            spatial_context_hash=spatial_hash,
            ai_predicted_ethnicity="african",
            ai_confidence_score=0.85,
            ai_classification_method="llm",
            confirmed_ethnicity="african",
            confirmed_by="sales_rep_1",
            confirmed_at=datetime.now(),
            confirmation_notes="Confirmed during qualification call",
            confirmation_source="phone_call",
            created_at=datetime.now()
        )
    
    def test_database_initialization(self, temp_db):
        """Test that database initializes properly with required tables."""
        # Verify tables exist by querying schema
        with temp_db._db_lock:
            import sqlite3
            with sqlite3.connect(temp_db.db_path) as conn:
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN (
                        'spatial_ethnicity_patterns', 
                        'ethnicity_confirmations',
                        'canonical_ethnicities'
                    )
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                assert 'spatial_ethnicity_patterns' in tables
                assert 'ethnicity_confirmations' in tables
                assert 'canonical_ethnicities' in tables
    
    def test_spatial_context_hash_generation(self, temp_db):
        """Test spatial context hash generation for consistent lookups."""
        # Test consistent hash generation
        hash1 = temp_db.generate_spatial_context_hash(
            "John Smith", "Sandton", "Johannesburg", "Gauteng"
        )
        hash2 = temp_db.generate_spatial_context_hash(
            "John Smith", "Sandton", "Johannesburg", "Gauteng"
        )
        assert hash1 == hash2
        assert len(hash1) == 16  # 16-character hash
        
        # Test different inputs produce different hashes
        hash3 = temp_db.generate_spatial_context_hash(
            "Jane Doe", "Sandton", "Johannesburg", "Gauteng"
        )
        assert hash1 != hash3
        
        # Test case insensitivity and normalization
        hash4 = temp_db.generate_spatial_context_hash(
            "john smith", "SANDTON", "  Johannesburg  ", "gauteng"
        )
        assert hash1 == hash4  # Should normalize to same hash
    
    @pytest.mark.asyncio
    async def test_store_confirmation_record(self, temp_db, sample_confirmation_record):
        """Test storing confirmation records."""
        result = await temp_db.store_confirmation_record(sample_confirmation_record)
        assert result is True
        
        # Verify record was stored by checking database
        with temp_db._db_lock:
            import sqlite3
            with sqlite3.connect(temp_db.db_path) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM ethnicity_confirmations WHERE confirmation_id = ?",
                    (sample_confirmation_record.confirmation_id,)
                )
                count = cursor.fetchone()[0]
                assert count == 1
    
    def test_extract_name_components(self, temp_db):
        """Test name component extraction for pattern learning."""
        # Test simple name
        components = temp_db._extract_name_components("John Smith")
        assert "john" in components
        assert "smith" in components
        assert len(components) >= 2
        
        # Test complex South African name
        components = temp_db._extract_name_components("Thabo Johannes Mthembu")
        assert "thabo" in components
        assert "johannes" in components 
        assert "mthembu" in components
        
        # Test single name
        components = temp_db._extract_name_components("Mandela")
        assert "mandela" in components
        
        # Test empty/invalid names
        components = temp_db._extract_name_components("")
        assert len(components) == 0
        
        components = temp_db._extract_name_components("A")  # Too short
        assert len(components) == 0
    
    @pytest.mark.asyncio
    async def test_extract_patterns_from_confirmations(self, temp_db, sample_confirmation_record):
        """Test pattern extraction from confirmation records."""
        # Store confirmation record first
        await temp_db.store_confirmation_record(sample_confirmation_record)
        
        # Extract patterns
        patterns = await temp_db.extract_patterns_from_confirmations(days_lookback=1)
        
        # Verify patterns were extracted
        assert len(patterns) > 0
        
        # Check pattern properties
        pattern = patterns[0]
        assert isinstance(pattern, SpatialEthnicityPattern)
        assert pattern.ethnicity_code == "african"
        assert pattern.confirmation_count == 1
        assert pattern.success_rate == 1.0
        assert pattern.confidence_score == 1.0
    
    @pytest.mark.asyncio
    async def test_enhanced_ethnicity_prediction(self, temp_db, sample_confirmation_record):
        """Test enhanced ethnicity prediction using spatial patterns."""
        # Store confirmation and extract patterns
        await temp_db.store_confirmation_record(sample_confirmation_record)
        await temp_db.extract_patterns_from_confirmations(days_lookback=1)
        
        # Test prediction for similar spatial context
        prediction = await temp_db.enhanced_ethnicity_prediction(
            name="Sipho Mthembu",  # Similar surname to confirmed pattern
            city="Johannesburg",
            province="Gauteng",
            suburb="Sandton"
        )
        
        # Should find spatial match
        assert prediction is not None
        assert prediction.ethnicity == EthnicityType.AFRICAN
        assert prediction.confidence >= 0.6
        assert prediction.method == ClassificationMethod.RULE_BASED
    
    @pytest.mark.asyncio
    async def test_spatial_match_scoring(self, temp_db):
        """Test spatial match scoring algorithm."""
        # Test exact match
        score = temp_db._calculate_spatial_match_score(
            "Sandton", "Johannesburg", "Gauteng",
            "Sandton", "Johannesburg", "Gauteng"
        )
        assert score == 1.0
        
        # Test partial match (city + province)
        score = temp_db._calculate_spatial_match_score(
            "Rosebank", "Johannesburg", "Gauteng",
            "Sandton", "Johannesburg", "Gauteng"
        )
        assert 0.5 < score < 1.0  # Should get city + province match
        
        # Test province only match
        score = temp_db._calculate_spatial_match_score(
            "Rosebank", "Johannesburg", "Gauteng",
            "Sandton", "Cape Town", "Gauteng"
        )
        assert 0.0 < score < 0.5  # Should get province match only
        
        # Test no match
        score = temp_db._calculate_spatial_match_score(
            "Sandton", "Johannesburg", "Gauteng",
            "Observatory", "Cape Town", "Western Cape"
        )
        assert score < 0.5  # No significant matches
    
    @pytest.mark.asyncio
    async def test_pattern_update_from_multiple_confirmations(self, temp_db):
        """Test pattern updates when multiple confirmations support same pattern."""
        # Create multiple confirmations for same pattern (same spatial context)
        confirmations = []
        for i in range(3):
            # Use different first names but same surname and spatial context
            first_names = ["Thabo", "Sipho", "Mandla"]
            director_name = f"{first_names[i]} Mthembu"
            confirmation = ConfirmationRecord(
                confirmation_id=f"test_conf_{i:03d}",
                source_file_identifier=f"test_file_{i}",
                source_row_number=i + 1,
                source_job_id="job_test_001",
                original_entity_name=f"Test Company {i} (Pty) Ltd",
                original_director_name=director_name,  # Similar surname pattern
                original_registered_address=f"12{i} Main Street",
                original_registered_city="Johannesburg",
                original_registered_province="Gauteng",
                canonical_suburb="Sandton",
                canonical_city="Johannesburg",
                canonical_province="Gauteng",
                spatial_context_hash=temp_db.generate_spatial_context_hash(
                    director_name, "Sandton", "Johannesburg", "Gauteng"
                ),
                ai_predicted_ethnicity="african",
                ai_confidence_score=0.8 + (i * 0.05),
                ai_classification_method="llm",
                confirmed_ethnicity="african",
                confirmed_by=f"sales_rep_{i}",
                confirmed_at=datetime.now() + timedelta(hours=i),
                confirmation_notes=f"Confirmation {i}",
                confirmation_source="phone_call",
                created_at=datetime.now()
            )
            confirmations.append(confirmation)
            await temp_db.store_confirmation_record(confirmation)
        
        # Extract patterns
        patterns = await temp_db.extract_patterns_from_confirmations(days_lookback=1)
        
        # Find pattern for 'mthembu' component (should be strengthened by multiple confirmations)
        mthembu_patterns = [p for p in patterns if 'mthembu' in p.name_component.lower()]
        assert len(mthembu_patterns) > 0
        
        # Find the pattern with the highest confirmation count (should be the merged one)
        pattern = max(mthembu_patterns, key=lambda p: p.confirmation_count)
        assert pattern.confirmation_count >= 2  # Should have multiple confirmations
        assert pattern.success_rate >= 0.8      # High success rate
    
    @pytest.mark.asyncio
    async def test_spatial_learning_analytics(self, temp_db, sample_confirmation_record):
        """Test spatial learning analytics generation."""
        # Store confirmation data
        await temp_db.store_confirmation_record(sample_confirmation_record)
        await temp_db.extract_patterns_from_confirmations(days_lookback=1)
        
        # Get analytics
        analytics = await temp_db.get_spatial_learning_analytics()
        
        # Verify analytics structure
        assert 'pattern_statistics' in analytics
        assert 'confirmation_statistics' in analytics
        assert 'ethnicity_distribution' in analytics
        assert 'geographic_coverage' in analytics
        assert 'learning_efficiency' in analytics
        
        # Verify data
        assert analytics['pattern_statistics']['total_patterns'] > 0
        assert analytics['confirmation_statistics']['total_confirmations'] > 0
        assert analytics['learning_efficiency'] > 0.0
    
    @pytest.mark.asyncio
    async def test_no_prediction_for_insufficient_confidence(self, temp_db):
        """Test that low-confidence spatial patterns don't produce predictions."""
        # Create confirmation with different ethnicity than query
        director_name = "John Smith"  # English name
        confirmation = ConfirmationRecord(
            confirmation_id="test_conf_low",
            source_file_identifier="test_file_low",
            source_row_number=1,
            source_job_id="job_test_001",
            original_entity_name="Test Company",
            original_director_name=director_name,
            original_registered_address="123 Main Street",
            original_registered_city="Johannesburg",
            original_registered_province="Gauteng",
            canonical_suburb="Sandton",
            canonical_city="Johannesburg",
            canonical_province="Gauteng",
            spatial_context_hash=temp_db.generate_spatial_context_hash(
                director_name, "Sandton", "Johannesburg", "Gauteng"
            ),
            ai_predicted_ethnicity="white",
            ai_confidence_score=0.85,
            ai_classification_method="llm",
            confirmed_ethnicity="white",
            confirmed_by="sales_rep_1",
            confirmed_at=datetime.now(),
            confirmation_notes="Confirmed",
            confirmation_source="phone_call",
            created_at=datetime.now()
        )
        
        await temp_db.store_confirmation_record(confirmation)
        await temp_db.extract_patterns_from_confirmations(days_lookback=1)
        
        # Test prediction for very different name in same area
        prediction = await temp_db.enhanced_ethnicity_prediction(
            name="Thandiwe Mthembu",  # Different ethnic pattern
            city="Johannesburg",
            province="Gauteng", 
            suburb="Sandton"
        )
        
        # Should not get confident prediction due to name-ethnicity mismatch
        if prediction:
            assert prediction.confidence < 0.8  # Low confidence due to mismatch
    
    @pytest.mark.asyncio
    async def test_pattern_extraction_performance(self, temp_db):
        """Test that pattern extraction performs within acceptable time limits."""
        import time
        
        # Create multiple confirmations for performance testing
        confirmations = []
        for i in range(10):  # Reasonable number for unit test
            director_name = f"Test Name {i}"
            suburb = f"Suburb_{i % 3}"  # Vary suburbs
            confirmation = ConfirmationRecord(
                confirmation_id=f"perf_test_{i:03d}",
                source_file_identifier=f"perf_file_{i}",
                source_row_number=i + 1,
                source_job_id="job_perf_test",
                original_entity_name=f"Performance Test Company {i}",
                original_director_name=director_name,
                original_registered_address=f"Address {i}",
                original_registered_city="Johannesburg",
                original_registered_province="Gauteng",
                canonical_suburb=suburb,
                canonical_city="Johannesburg",
                canonical_province="Gauteng",
                spatial_context_hash=temp_db.generate_spatial_context_hash(
                    director_name, suburb, "Johannesburg", "Gauteng"
                ),
                ai_predicted_ethnicity="african",
                ai_confidence_score=0.8,
                ai_classification_method="llm",
                confirmed_ethnicity="african",
                confirmed_by="sales_rep_test",
                confirmed_at=datetime.now(),
                confirmation_notes="Performance test",
                confirmation_source="phone_call",
                created_at=datetime.now()
            )
            confirmations.append(confirmation)
            await temp_db.store_confirmation_record(confirmation)
        
        # Time pattern extraction
        start_time = time.time()
        patterns = await temp_db.extract_patterns_from_confirmations(days_lookback=1)
        extraction_time = time.time() - start_time
        
        # Verify performance
        assert extraction_time < 2.0  # Should complete within 2 seconds
        assert len(patterns) > 0  # Should extract patterns
        
        # Time prediction
        start_time = time.time()
        prediction = await temp_db.enhanced_ethnicity_prediction(
            name="Test Name 5", 
            city="Johannesburg",
            province="Gauteng",
            suburb="Suburb_2"
        )
        prediction_time = time.time() - start_time
        
        # Verify prediction performance  
        assert prediction_time < 0.1  # Should be very fast (<100ms)
    
    @pytest.mark.asyncio
    async def test_enhanced_name_component_extraction(self, temp_db):
        """Test enhanced name component extraction for Phase 1.2."""
        # Test complex South African name
        components = temp_db._extract_name_components("Thabo Johannes van der Merwe")
        
        # Should extract various component types
        assert "thabo" in components
        assert "johannes" in components
        assert "merwe" in components  # 'van der' should be handled
        assert "first:thabo" in components  # Tagged first name
        assert "last:merwe" in components   # Tagged last name
        
        # Should extract prefixes and suffixes
        prefix_components = [c for c in components if c.startswith("prefix")]
        suffix_components = [c for c in components if c.startswith("suffix")]
        trigram_components = [c for c in components if c.startswith("trigram")]
        
        assert len(prefix_components) > 0
        assert len(suffix_components) > 0
        assert len(trigram_components) > 0
    
    @pytest.mark.asyncio
    async def test_confirmation_learning_status(self, temp_db, sample_confirmation_record):
        """Test confirmation learning status monitoring."""
        # Store confirmation and extract patterns
        await temp_db.store_confirmation_record(sample_confirmation_record)
        await temp_db.extract_patterns_from_confirmations(days_lookback=1)
        
        # Get learning status
        status = await temp_db.get_confirmation_learning_status()
        
        # Verify status structure
        assert 'confirmation_activity' in status
        assert 'pattern_effectiveness' in status
        assert 'learning_efficiency_trend' in status
        assert 'integration_health' in status
        
        # Verify data integrity
        assert status['confirmation_activity']['total_confirmations'] > 0
        assert status['pattern_effectiveness']['total_patterns'] > 0
        assert status['integration_health']['patterns_per_confirmation'] > 0
    
    @pytest.mark.asyncio
    async def test_spatial_correlation_pattern_extraction(self, temp_db):
        """Test spatial correlation pattern extraction for geographic ethnicity analysis."""
        # Create multiple confirmations in same spatial context with strong correlation
        for i in range(5):
            confirmation = ConfirmationRecord(
                confirmation_id=f"spatial_corr_{i}",
                source_file_identifier=f"spatial_file_{i}",
                source_row_number=i + 1,
                source_job_id="spatial_test",
                original_entity_name=f"Spatial Test {i}",
                original_director_name=f"African Name {i}",
                original_registered_address="123 Test Street",
                original_registered_city="Johannesburg",
                original_registered_province="Gauteng",
                canonical_suburb="Sandton",
                canonical_city="Johannesburg",
                canonical_province="Gauteng",
                spatial_context_hash=temp_db.generate_spatial_context_hash(
                    f"African Name {i}", "Sandton", "Johannesburg", "Gauteng"
                ),
                ai_predicted_ethnicity="african",
                ai_confidence_score=0.85,
                ai_classification_method="llm",
                confirmed_ethnicity="african",  # Strong correlation: all African
                confirmed_by=f"sales_rep_{i}",
                confirmed_at=datetime.now(),
                confirmation_notes="Strong spatial correlation test",
                confirmation_source="phone_call",
                created_at=datetime.now()
            )
            await temp_db.store_confirmation_record(confirmation)
        
        # Extract patterns (should create spatial correlation patterns)
        patterns = await temp_db.extract_patterns_from_confirmations(days_lookback=1)
        
        # Should have extracted patterns (many individual name component patterns)
        assert len(patterns) > 0
        
        # Should have patterns with multiple confirmations from the same spatial context
        multi_confirmed_patterns = [p for p in patterns if p.confirmation_count >= 3]
        assert len(multi_confirmed_patterns) > 0
        
        # Should have high confidence and success rates for patterns with strong evidence
        strong_patterns = [p for p in patterns if p.confirmation_count >= 3 and p.success_rate >= 0.8]
        assert len(strong_patterns) > 0
        
        # Verify spatial context is properly recorded
        spatial_patterns = [p for p in patterns if p.suburb == "Sandton" and p.city == "Johannesburg"]
        assert len(spatial_patterns) > 0
    
    @pytest.mark.asyncio
    async def test_enhanced_ethnicity_prediction_with_confirmations_spatial_priority(self, temp_db, sample_confirmation_record):
        """Test Phase 1.3: Enhanced prediction with spatial pattern priority."""
        # Store confirmation and extract patterns
        await temp_db.store_confirmation_record(sample_confirmation_record)
        await temp_db.extract_patterns_from_confirmations(days_lookback=1)
        
        # Test spatial pattern priority (should use confirmed patterns first)
        prediction = await temp_db.enhanced_ethnicity_prediction_with_confirmations(
            name="Thabo Mthembu",  # Similar to confirmed pattern
            city="Johannesburg",
            province="Gauteng",
            suburb="Sandton"
        )
        
        # Should get prediction from spatial patterns
        assert prediction is not None
        assert prediction.ethnicity == EthnicityType.AFRICAN
        assert prediction.confidence >= 0.6
        assert prediction.context is not None
        assert prediction.context['spatial_enhanced'] is True
        assert prediction.context['prediction_source'] == 'confirmed_spatial_patterns'
        assert prediction.processing_time_ms is not None
        assert prediction.processing_time_ms < 100  # Performance requirement
    
    @pytest.mark.asyncio
    async def test_enhanced_ethnicity_prediction_fallback_with_spatial_boost(self, temp_db, sample_confirmation_record):
        """Test Phase 1.3: Fallback to existing pipeline with spatial boosting."""
        # Store confirmation and extract patterns
        await temp_db.store_confirmation_record(sample_confirmation_record)
        await temp_db.extract_patterns_from_confirmations(days_lookback=1)
        
        # Test fallback with spatial boost (name that doesn't match spatial patterns directly)
        prediction = await temp_db.enhanced_ethnicity_prediction_with_confirmations(
            name="Johan Smith",  # English name - won't match spatial patterns
            city="Johannesburg",
            province="Gauteng",
            suburb="Sandton"
        )
        
        # Should get prediction from fallback pipeline
        assert prediction is not None
        assert prediction.context is not None
        assert prediction.context['spatial_enhanced'] is True
        assert prediction.context['prediction_source'] == 'fallback_with_spatial_boost'
        assert 'original_confidence' in prediction.context
        assert 'spatial_boost_applied' in prediction.context
        assert prediction.processing_time_ms is not None
        assert prediction.processing_time_ms < 100  # Performance requirement
    
    @pytest.mark.asyncio
    async def test_spatial_confidence_boosting_algorithm(self, temp_db, sample_confirmation_record):
        """Test spatial confidence boosting algorithm."""
        from src.leadscout.classification.models import Classification, ClassificationMethod, EthnicityType
        
        # Store confirmation and extract patterns
        await temp_db.store_confirmation_record(sample_confirmation_record)
        await temp_db.extract_patterns_from_confirmations(days_lookback=1)
        
        # Create base prediction for testing
        base_prediction = Classification(
            name="Test Name",
            ethnicity=EthnicityType.AFRICAN,
            confidence=0.7,
            method=ClassificationMethod.RULE_BASED,
            processing_time_ms=10.0
        )
        
        # Apply spatial confidence boosting
        enhanced_prediction = await temp_db._apply_spatial_confidence_boosting(
            base_prediction, "Thabo Mthembu", "Johannesburg", "Gauteng", "Sandton"
        )
        
        # Should enhance confidence if spatial patterns support the prediction
        assert enhanced_prediction is not None
        assert enhanced_prediction.ethnicity == EthnicityType.AFRICAN
        # Confidence should be same or higher (boosted by spatial patterns)
        assert enhanced_prediction.confidence >= base_prediction.confidence
    
    @pytest.mark.asyncio
    async def test_enhanced_prediction_performance_requirements(self, temp_db, sample_confirmation_record):
        """Test that enhanced prediction meets performance requirements."""
        import time
        
        # Store multiple confirmations for realistic performance test
        for i in range(5):
            confirmation = ConfirmationRecord(
                confirmation_id=f"perf_test_enhanced_{i}",
                source_file_identifier=f"perf_file_{i}",
                source_row_number=i + 1,
                source_job_id="job_perf_test",
                original_entity_name=f"Performance Test {i}",
                original_director_name=f"Test Name {i}",
                original_registered_address="123 Test Street",
                original_registered_city="Johannesburg",
                original_registered_province="Gauteng",
                canonical_suburb="Sandton",
                canonical_city="Johannesburg",
                canonical_province="Gauteng",
                spatial_context_hash=temp_db.generate_spatial_context_hash(
                    f"Test Name {i}", "Sandton", "Johannesburg", "Gauteng"
                ),
                ai_predicted_ethnicity="african",
                ai_confidence_score=0.8,
                ai_classification_method="llm",
                confirmed_ethnicity="african",
                confirmed_by=f"sales_rep_{i}",
                confirmed_at=datetime.now(),
                confirmation_notes="Performance test",
                confirmation_source="phone_call",
                created_at=datetime.now()
            )
            await temp_db.store_confirmation_record(confirmation)
        
        await temp_db.extract_patterns_from_confirmations(days_lookback=1)
        
        # Test performance requirement (<100ms)
        start_time = time.time()
        prediction = await temp_db.enhanced_ethnicity_prediction_with_confirmations(
            name="Test Name 2",
            city="Johannesburg",
            province="Gauteng",
            suburb="Sandton"
        )
        processing_time = (time.time() - start_time) * 1000
        
        # Verify performance requirement
        assert processing_time < 100  # <100ms requirement
        assert prediction is not None
        assert prediction.processing_time_ms < 100
    
    @pytest.mark.asyncio
    async def test_enhanced_prediction_graceful_fallback_on_errors(self, temp_db):
        """Test graceful fallback when spatial patterns fail."""
        # Test with empty database (no patterns)
        prediction = await temp_db.enhanced_ethnicity_prediction_with_confirmations(
            name="Test Name",
            city="Johannesburg",
            province="Gauteng",
            suburb="Sandton"
        )
        
        # Should still get prediction via fallback pipeline
        assert prediction is not None
        assert prediction.context is not None
        assert prediction.context['spatial_enhanced'] is True
        assert prediction.context['prediction_source'] == 'fallback_with_spatial_boost'
    
    @pytest.mark.asyncio
    async def test_enhanced_prediction_context_enrichment(self, temp_db, sample_confirmation_record):
        """Test that enhanced prediction properly enriches context with spatial information."""
        # Store confirmation and extract patterns
        await temp_db.store_confirmation_record(sample_confirmation_record)
        await temp_db.extract_patterns_from_confirmations(days_lookback=1)
        
        prediction = await temp_db.enhanced_ethnicity_prediction_with_confirmations(
            name="Thabo Mthembu",
            city="Johannesburg", 
            province="Gauteng",
            suburb="Sandton"
        )
        
        # Verify context enrichment
        assert prediction is not None
        assert prediction.context is not None
        
        # Check required context fields
        required_fields = [
            'spatial_enhanced',
            'spatial_suburb', 
            'spatial_city',
            'spatial_province',
            'prediction_source'
        ]
        
        for field in required_fields:
            assert field in prediction.context, f"Missing context field: {field}"
        
        # Verify spatial context values
        assert prediction.context['spatial_suburb'] == "Sandton"
        assert prediction.context['spatial_city'] == "Johannesburg"
        assert prediction.context['spatial_province'] == "Gauteng"
        assert prediction.context['spatial_enhanced'] is True


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])