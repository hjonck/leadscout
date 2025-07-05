"""CIPC-specific exception classes.

This module defines the exception hierarchy for CIPC integration components,
providing specific error types for different failure scenarios in company
registry data processing.

Exception Hierarchy:
    CIPCError (base)
    ├── CIPCDownloadError (CSV download failures)
    ├── CIPCParsingError (data parsing issues)
    ├── CIPCSearchError (search operation failures)
    └── CIPCValidationError (data validation failures)

Usage:
    from leadscout.cipc.exceptions import CIPCDownloadError
    
    try:
        await downloader.download_csv(url)
    except CIPCDownloadError as e:
        logger.error(f"Download failed: {e}")
        # Handle download failure gracefully
"""

from leadscout.core.exceptions import LeadScoutError


class CIPCError(LeadScoutError):
    """Base exception for all CIPC-related errors.
    
    This is the parent class for all CIPC module exceptions, allowing
    consumers to catch all CIPC-related errors with a single exception type.
    """
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}


class CIPCDownloadError(CIPCError):
    """Raised when CSV download operations fail.
    
    This exception is raised for various download-related failures including
    network errors, HTTP errors, file system errors, and invalid responses
    from the CIPC website.
    
    Attributes:
        url: The URL that failed to download
        status_code: HTTP status code (if applicable)
        retry_count: Number of retries attempted
    """
    
    def __init__(
        self, 
        message: str, 
        url: str = None, 
        status_code: int = None,
        retry_count: int = 0,
        details: dict = None
    ):
        super().__init__(message, details)
        self.url = url
        self.status_code = status_code
        self.retry_count = retry_count


class CIPCParsingError(CIPCError):
    """Raised when CSV parsing or data extraction fails.
    
    This exception is raised when CSV files cannot be parsed correctly,
    when expected columns are missing, or when data extraction algorithms
    encounter malformed company name data.
    
    Attributes:
        file_path: Path to the file that failed to parse
        line_number: Line number where parsing failed (if applicable)
        column_name: Column that caused the parsing error
    """
    
    def __init__(
        self,
        message: str,
        file_path: str = None,
        line_number: int = None,
        column_name: str = None,
        details: dict = None
    ):
        super().__init__(message, details)
        self.file_path = file_path
        self.line_number = line_number
        self.column_name = column_name


class CIPCSearchError(CIPCError):
    """Raised when company search operations fail.
    
    This exception is raised when search queries fail due to database
    connectivity issues, malformed queries, or search algorithm failures.
    
    Attributes:
        query: The search query that failed
        search_type: Type of search operation (fuzzy, exact, etc.)
        index_name: Database index involved in the search
    """
    
    def __init__(
        self,
        message: str,
        query: str = None,
        search_type: str = None,
        index_name: str = None,
        details: dict = None
    ):
        super().__init__(message, details)
        self.query = query
        self.search_type = search_type
        self.index_name = index_name


class CIPCValidationError(CIPCError):
    """Raised when company data validation fails.
    
    This exception is raised when company registration numbers, company names,
    or other CIPC data fails validation checks or doesn't conform to expected
    South African business registration formats.
    
    Attributes:
        field_name: Name of the field that failed validation
        field_value: Value that failed validation
        validation_rule: Description of the validation rule that failed
    """
    
    def __init__(
        self,
        message: str,
        field_name: str = None,
        field_value: str = None,
        validation_rule: str = None,
        details: dict = None
    ):
        super().__init__(message, details)
        self.field_name = field_name
        self.field_value = field_value
        self.validation_rule = validation_rule