"""Unit tests for CIPC models.

This module tests all CIPC-related Pydantic models including
validation, business logic, and integration with the cache system.

Developer A - CIPC Integration & Caching Specialist
"""

import pytest
from datetime import date, datetime
from typing import List

from leadscout.cipc.models import (
    CIPCCompany,
    PersonalName,
    CompanySearchRequest,
    CompanySearchResponse,
    CompanyMatch,
    SearchFilters,
    CIPCDownloadBatch,
    CIPCProcessingStats,
    CompanyType,
    CompanyStatus
)
from leadscout.cipc.exceptions import CIPCValidationError


class TestCIPCCompany:
    """Test CIPCCompany model validation and methods."""
    
    def test_valid_company_creation(self):
        """Test creating a valid CIPC company record."""
        company = CIPCCompany(
            registration_number="2021/123456/07",
            company_name="ABC Trading CC",
            company_type=CompanyType.CLOSE_CORPORATION,
            company_status=CompanyStatus.ACTIVE,
            download_batch=date(2025, 1, 1),
            file_source="A",
            name_slug="abc trading cc"
        )
        
        assert company.registration_number == "2021/123456/07"
        assert company.company_name == "ABC Trading CC"
        assert company.company_type == CompanyType.CLOSE_CORPORATION
        assert company.company_status == CompanyStatus.ACTIVE
        assert company.is_active()
        assert isinstance(company.created_at, datetime)
    
    def test_registration_number_validation(self):
        """Test SA company registration number validation."""
        # Valid SA format
        company = CIPCCompany(
            registration_number="2021/123456/07",
            company_name="Test Company",
            download_batch=date(2025, 1, 1),
            file_source="A"
        )
        assert company.registration_number == "2021/123456/07"
        
        # Empty registration number should fail
        with pytest.raises(ValueError, match="Registration number is required"):
            CIPCCompany(
                registration_number="",
                company_name="Test Company",
                download_batch=date(2025, 1, 1),
                file_source="A"
            )
        
        # Too short registration number should fail
        with pytest.raises(ValueError, match="Registration number too short"):
            CIPCCompany(
                registration_number="123",
                company_name="Test Company",
                download_batch=date(2025, 1, 1),
                file_source="A"
            )
    
    def test_company_name_validation(self):
        """Test company name validation and cleaning."""
        # Extra whitespace should be cleaned
        company = CIPCCompany(
            registration_number="2021/123456/07",
            company_name="  ABC   Trading   CC  ",
            download_batch=date(2025, 1, 1),
            file_source="A"
        )
        assert company.company_name == "Abc Trading Cc"  # Title case applied
        
        # Empty name should fail
        with pytest.raises(ValueError, match="Company name is required"):
            CIPCCompany(
                registration_number="2021/123456/07",
                company_name="",
                download_batch=date(2025, 1, 1),
                file_source="A"
            )
        
        # Invalid characters should fail
        with pytest.raises(ValueError, match="invalid characters"):
            CIPCCompany(
                registration_number="2021/123456/07",
                company_name="Company\tWith\tTabs",
                download_batch=date(2025, 1, 1),
                file_source="A"
            )
    
    def test_name_slug_generation(self):
        """Test automatic name slug generation."""
        company = CIPCCompany(
            registration_number="2021/123456/07",
            company_name="ABC Trading (Pty) Ltd!",
            download_batch=date(2025, 1, 1),
            file_source="A"
        )
        
        # Should be lowercase, special chars removed, normalized
        expected_slug = "abc trading pty ltd"
        assert company.name_slug == expected_slug
        
        # Manual slug should be preserved
        company_manual_slug = CIPCCompany(
            registration_number="2021/123456/07",
            company_name="ABC Trading CC",
            name_slug="custom slug",
            download_batch=date(2025, 1, 1),
            file_source="A"
        )
        assert company_manual_slug.name_slug == "custom slug"
    
    def test_file_source_validation(self):
        """Test file source validation."""
        # Valid single letter
        company = CIPCCompany(
            registration_number="2021/123456/07",
            company_name="Test Company",
            download_batch=date(2025, 1, 1),
            file_source="A"
        )
        assert company.file_source == "A"
        
        # Valid letter with number
        company_numbered = CIPCCompany(
            registration_number="2021/123456/07",
            company_name="Test Company",
            download_batch=date(2025, 1, 1),
            file_source="A1"
        )
        assert company_numbered.file_source == "A1"
        
        # Invalid format should fail
        with pytest.raises(ValueError, match="Invalid file source format"):
            CIPCCompany(
                registration_number="2021/123456/07",
                company_name="Test Company",
                download_batch=date(2025, 1, 1),
                file_source="invalid"
            )
    
    def test_company_methods(self):
        """Test company utility methods."""
        company = CIPCCompany(
            registration_number="2021/123456/07",
            company_name="ABC Trading CC",
            company_type=CompanyType.CLOSE_CORPORATION,
            company_status=CompanyStatus.ACTIVE,
            download_batch=date(2025, 1, 1),
            file_source="A"
        )
        
        # Test display name
        display_name = company.get_display_name()
        assert "Close Corporation" in display_name
        
        # Test active status
        assert company.is_active()
        
        # Test inactive status
        company.company_status = CompanyStatus.DEREGISTERED
        assert not company.is_active()
        
        # Test search dict conversion
        search_dict = company.to_search_dict()
        assert search_dict["registration_number"] == "2021/123456/07"
        assert search_dict["company_name"] == "ABC Trading CC"
        assert search_dict["is_active"] is False  # After status change


class TestPersonalName:
    """Test PersonalName model validation."""
    
    def test_valid_personal_name(self):
        """Test creating a valid personal name extraction."""
        name = PersonalName(
            name="John Smith",
            phonetic_key="JN SMT",
            position=0,
            extraction_method="regex_pattern",
            confidence=0.95,
            context="John Smith Trading CC",
            company_registration="2021/123456/07"
        )
        
        assert name.name == "John Smith"
        assert name.phonetic_key == "JN SMT"
        assert name.confidence == 0.95
        assert name.is_high_confidence()
    
    def test_name_validation_and_cleaning(self):
        """Test personal name validation and cleaning."""
        # Title case should be applied
        name = PersonalName(
            name="john smith",
            phonetic_key="JN SMT",
            position=0,
            extraction_method="regex_pattern",
            confidence=0.8,
            context="context",
            company_registration="2021/123456/07"
        )
        assert name.name == "John Smith"
        
        # Invalid characters should fail
        with pytest.raises(ValueError, match="invalid characters"):
            PersonalName(
                name="John123 Smith",
                phonetic_key="JN SMT",
                position=0,
                extraction_method="regex_pattern",
                confidence=0.8,
                context="context",
                company_registration="2021/123456/07"
            )
    
    def test_extraction_method_validation(self):
        """Test extraction method validation."""
        valid_methods = [
            "regex_pattern", "tokenization", "capitalization",
            "known_surnames", "name_dictionary", "manual"
        ]
        
        for method in valid_methods:
            name = PersonalName(
                name="John Smith",
                phonetic_key="JN SMT",
                position=0,
                extraction_method=method,
                confidence=0.8,
                context="context",
                company_registration="2021/123456/07"
            )
            assert name.extraction_method == method
        
        # Invalid method should fail
        with pytest.raises(ValueError, match="Invalid extraction method"):
            PersonalName(
                name="John Smith",
                phonetic_key="JN SMT",
                position=0,
                extraction_method="invalid_method",
                confidence=0.8,
                context="context",
                company_registration="2021/123456/07"
            )
    
    def test_confidence_methods(self):
        """Test confidence-related methods."""
        # High confidence name
        high_conf_name = PersonalName(
            name="John Smith",
            phonetic_key="JN SMT",
            position=0,
            extraction_method="regex_pattern",
            confidence=0.9,
            context="context",
            company_registration="2021/123456/07"
        )
        assert high_conf_name.is_high_confidence()
        assert high_conf_name.is_high_confidence(threshold=0.85)
        
        # Low confidence name
        low_conf_name = PersonalName(
            name="Uncertain Name",
            phonetic_key="UNC NM",
            position=0,
            extraction_method="tokenization",
            confidence=0.6,
            context="context",
            company_registration="2021/123456/07"
        )
        assert not low_conf_name.is_high_confidence()
        assert low_conf_name.is_high_confidence(threshold=0.5)


class TestSearchFilters:
    """Test SearchFilters model."""
    
    def test_default_filters(self):
        """Test default filter values."""
        filters = SearchFilters()
        
        assert filters.province is None
        assert filters.company_type is None
        assert filters.company_status is None
        assert filters.active_only is True  # Default should be True
        assert filters.min_confidence == 0.0
        assert filters.has_personal_names is None
    
    def test_custom_filters(self):
        """Test custom filter configuration."""
        filters = SearchFilters(
            province="Gauteng",
            company_type=CompanyType.PRIVATE_COMPANY,
            company_status=CompanyStatus.ACTIVE,
            active_only=False,
            min_confidence=0.8,
            has_personal_names=True,
            download_batch_from=date(2024, 1, 1),
            download_batch_to=date(2024, 12, 31)
        )
        
        assert filters.province == "Gauteng"
        assert filters.company_type == CompanyType.PRIVATE_COMPANY
        assert filters.company_status == CompanyStatus.ACTIVE
        assert filters.active_only is False
        assert filters.min_confidence == 0.8
        assert filters.has_personal_names is True


class TestCompanySearchRequest:
    """Test CompanySearchRequest model."""
    
    def test_valid_search_request(self):
        """Test creating a valid search request."""
        request = CompanySearchRequest(
            query="ABC Trading",
            exact_match=False,
            fuzzy_threshold=0.8,
            max_results=20
        )
        
        assert request.query == "ABC Trading"
        assert request.exact_match is False
        assert request.fuzzy_threshold == 0.8
        assert request.max_results == 20
        assert isinstance(request.filters, SearchFilters)
    
    def test_query_validation_and_cleaning(self):
        """Test query validation and cleaning."""
        # Whitespace should be cleaned
        request = CompanySearchRequest(query="  ABC   Trading  ")
        assert request.query == "ABC Trading"
        
        # Problematic characters should be removed
        request_cleaned = CompanySearchRequest(query='ABC "Trading" |Company|')
        assert '"' not in request_cleaned.query
        assert '|' not in request_cleaned.query
        
        # Empty query should fail
        with pytest.raises(ValueError, match="Search query is required"):
            CompanySearchRequest(query="")
        
        # Too short query should fail
        with pytest.raises(ValueError, match="at least 2"):
            CompanySearchRequest(query="A")
    
    def test_sort_by_validation(self):
        """Test sort criteria validation."""
        valid_sorts = ['relevance', 'name', 'registration_date', 'status']
        
        for sort_criteria in valid_sorts:
            request = CompanySearchRequest(
                query="Test Company",
                sort_by=sort_criteria
            )
            assert request.sort_by == sort_criteria
        
        # Invalid sort should fail
        with pytest.raises(ValueError, match="Invalid sort criteria"):
            CompanySearchRequest(
                query="Test Company",
                sort_by="invalid_sort"
            )


class TestCompanyMatch:
    """Test CompanyMatch model."""
    
    def test_company_match_creation(self):
        """Test creating a company match result."""
        company = CIPCCompany(
            registration_number="2021/123456/07",
            company_name="ABC Trading CC",
            download_batch=date(2025, 1, 1),
            file_source="A"
        )
        
        match = CompanyMatch(
            company=company,
            similarity_score=0.95,
            match_type="fuzzy",
            match_fields=["company_name", "name_slug"],
            rank=1
        )
        
        assert match.company == company
        assert match.similarity_score == 0.95
        assert match.match_type == "fuzzy"
        assert match.rank == 1
        assert match.is_high_quality_match()
    
    def test_match_type_validation(self):
        """Test match type validation."""
        valid_types = ['exact', 'fuzzy', 'partial', 'phonetic', 'substring']
        
        company = CIPCCompany(
            registration_number="2021/123456/07",
            company_name="Test Company",
            download_batch=date(2025, 1, 1),
            file_source="A"
        )
        
        for match_type in valid_types:
            match = CompanyMatch(
                company=company,
                similarity_score=0.8,
                match_type=match_type,
                match_fields=["company_name"],
                rank=1
            )
            assert match.match_type == match_type
        
        # Invalid match type should fail
        with pytest.raises(ValueError, match="Invalid match type"):
            CompanyMatch(
                company=company,
                similarity_score=0.8,
                match_type="invalid_type",
                match_fields=["company_name"],
                rank=1
            )
    
    def test_high_quality_match_criteria(self):
        """Test high quality match determination."""
        active_company = CIPCCompany(
            registration_number="2021/123456/07",
            company_name="ABC Trading CC",
            company_status=CompanyStatus.ACTIVE,
            download_batch=date(2025, 1, 1),
            file_source="A"
        )
        
        # High quality: high similarity, active company, good match type
        high_quality = CompanyMatch(
            company=active_company,
            similarity_score=0.9,
            match_type="exact",
            match_fields=["company_name"],
            rank=1
        )
        assert high_quality.is_high_quality_match()
        
        # Low quality: low similarity
        low_similarity = CompanyMatch(
            company=active_company,
            similarity_score=0.5,
            match_type="exact",
            match_fields=["company_name"],
            rank=1
        )
        assert not low_similarity.is_high_quality_match()
        
        # Low quality: inactive company
        inactive_company = CIPCCompany(
            registration_number="2021/123456/07",
            company_name="ABC Trading CC",
            company_status=CompanyStatus.DEREGISTERED,
            download_batch=date(2025, 1, 1),
            file_source="A"
        )
        
        inactive_match = CompanyMatch(
            company=inactive_company,
            similarity_score=0.9,
            match_type="exact",
            match_fields=["company_name"],
            rank=1
        )
        assert not inactive_match.is_high_quality_match()


class TestCompanySearchResponse:
    """Test CompanySearchResponse model."""
    
    def test_search_response_creation(self):
        """Test creating a search response."""
        company = CIPCCompany(
            registration_number="2021/123456/07",
            company_name="ABC Trading CC",
            download_batch=date(2025, 1, 1),
            file_source="A"
        )
        
        match = CompanyMatch(
            company=company,
            similarity_score=0.9,
            match_type="fuzzy",
            match_fields=["company_name"],
            rank=1
        )
        
        response = CompanySearchResponse(
            query="ABC Trading",
            matches=[match],
            total_results=1,
            search_time_ms=150,
            filters_applied=SearchFilters()
        )
        
        assert response.query == "ABC Trading"
        assert len(response.matches) == 1
        assert response.total_results == 1
        assert response.returned_results == 1  # Auto-calculated
        assert response.search_time_ms == 150
    
    def test_returned_results_calculation(self):
        """Test automatic returned results calculation."""
        response = CompanySearchResponse(
            query="Test",
            matches=[],  # No matches
            total_results=0,
            search_time_ms=100,
            filters_applied=SearchFilters()
        )
        
        assert response.returned_results == 0
        
        # Add matches and verify auto-calculation
        company = CIPCCompany(
            registration_number="2021/123456/07",
            company_name="Test Company",
            download_batch=date(2025, 1, 1),
            file_source="A"
        )
        
        matches = [
            CompanyMatch(
                company=company,
                similarity_score=0.9,
                match_type="exact",
                match_fields=["company_name"],
                rank=i+1
            ) for i in range(3)
        ]
        
        response_with_matches = CompanySearchResponse(
            query="Test",
            matches=matches,
            total_results=3,
            search_time_ms=200,
            filters_applied=SearchFilters()
        )
        
        assert response_with_matches.returned_results == 3


class TestCIPCDownloadBatch:
    """Test CIPCDownloadBatch model."""
    
    def test_download_batch_creation(self):
        """Test creating a download batch record."""
        batch = CIPCDownloadBatch(
            year=2025,
            month=1,
            files_downloaded=26,
            total_companies=150000,
            total_names_extracted=75000,
            processing_time_minutes=45,
            status="completed"
        )
        
        assert batch.year == 2025
        assert batch.month == 1
        assert batch.files_downloaded == 26
        assert batch.status == "completed"
        assert isinstance(batch.download_date, datetime)
    
    def test_status_validation(self):
        """Test batch status validation."""
        valid_statuses = ['pending', 'downloading', 'processing', 'completed', 'failed']
        
        for status in valid_statuses:
            batch = CIPCDownloadBatch(year=2025, month=1, status=status)
            assert batch.status == status
        
        # Invalid status should fail
        with pytest.raises(ValueError, match="Invalid status"):
            CIPCDownloadBatch(year=2025, month=1, status="invalid_status")
    
    def test_batch_identifier(self):
        """Test batch identifier generation."""
        batch = CIPCDownloadBatch(year=2025, month=1)
        identifier = batch.get_batch_identifier()
        assert identifier == "2025-01"
        
        batch_dec = CIPCDownloadBatch(year=2024, month=12)
        identifier_dec = batch_dec.get_batch_identifier()
        assert identifier_dec == "2024-12"
    
    def test_error_management(self):
        """Test error tracking functionality."""
        batch = CIPCDownloadBatch(year=2025, month=1)
        
        assert batch.error_count == 0
        assert len(batch.error_details) == 0
        
        # Add errors
        batch.add_error("Failed to download file A.csv")
        batch.add_error("Parse error in file B.csv")
        
        assert batch.error_count == 2
        assert len(batch.error_details) == 2
        assert "Failed to download file A.csv" in batch.error_details


class TestCIPCProcessingStats:
    """Test CIPCProcessingStats model."""
    
    def test_processing_stats_creation(self):
        """Test creating processing statistics."""
        stats = CIPCProcessingStats(
            total_companies_processed=100000,
            total_names_extracted=50000,
            successful_downloads=26,
            failed_downloads=0,
            average_processing_time_ms=15.5,
            extraction_accuracy_rate=0.94,
            cache_hit_rate=0.82
        )
        
        assert stats.total_companies_processed == 100000
        assert stats.total_names_extracted == 50000
        assert stats.extraction_accuracy_rate == 0.94
    
    def test_download_success_rate(self):
        """Test download success rate calculation."""
        stats = CIPCProcessingStats(
            successful_downloads=24,
            failed_downloads=2
        )
        
        success_rate = stats.get_download_success_rate()
        assert success_rate == 92.31  # 24/26 * 100, rounded to 2 decimals
        
        # No downloads should return 0
        no_downloads_stats = CIPCProcessingStats()
        assert no_downloads_stats.get_download_success_rate() == 0.0
    
    def test_names_per_company_ratio(self):
        """Test names per company ratio calculation."""
        stats = CIPCProcessingStats(
            total_companies_processed=1000,
            total_names_extracted=500
        )
        
        ratio = stats.get_names_per_company_ratio()
        assert ratio == 0.5
        
        # No companies should return 0
        no_companies_stats = CIPCProcessingStats()
        assert no_companies_stats.get_names_per_company_ratio() == 0.0