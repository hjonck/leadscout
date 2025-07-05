# LeadScout Coding Standards

## Overview

This document defines the coding standards and best practices for the LeadScout project. All contributors must follow these guidelines to ensure code quality, maintainability, and consistency across the codebase.

## General Principles

### 1. Code Quality First
- Write code that is readable, maintainable, and testable
- Favor explicit code over clever code
- Follow the principle of least surprise
- Write code as if the person maintaining it is a violent psychopath who knows where you live

### 2. Performance Considerations
- Optimize for readability first, performance second
- Use profiling to identify actual bottlenecks
- Prefer built-in functions and libraries over custom implementations
- Cache expensive operations appropriately

### 3. Security by Design
- Never hardcode credentials or sensitive information
- Validate all input data
- Use parameterized queries for database operations
- Follow the principle of least privilege

## Python Standards

### Version Requirements
- **Minimum Python Version**: 3.11
- **Target Python Version**: 3.11+
- **Compatibility**: Support latest stable Python releases

### Code Formatting

#### Black Configuration
```toml
[tool.black]
line-length = 88
target-version = ['py311']
```

#### Import Organization (isort)
```python
# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import click
import pandas as pd
from pydantic import BaseModel

# Local imports
from leadscout.core import config
from leadscout.models.lead import Lead
```

### Type Hints

#### Required Type Annotations
```python
# All function signatures must include type hints
def enrich_lead(lead: Lead, config: Config) -> EnrichedLead:
    """Enrich a lead with additional data."""
    pass

# Class attributes should be annotated
class LeadProcessor:
    cache: Dict[str, Any]
    timeout: int = 30
    
    def __init__(self, cache_dir: Path) -> None:
        self.cache = {}
```

#### Optional and Union Types
```python
from typing import Optional, Union, List, Dict, Any

# Use Optional for nullable values
def get_company_info(company_id: Optional[str]) -> Optional[CompanyInfo]:
    pass

# Use Union for multiple types
def process_data(data: Union[str, Dict[str, Any]]) -> ProcessedData:
    pass
```

### Error Handling

#### Exception Hierarchy
```python
class LeadScoutError(Exception):
    """Base exception for LeadScout."""
    pass

class APIError(LeadScoutError):
    """API-related errors."""
    pass

class ValidationError(LeadScoutError):
    """Data validation errors."""
    pass
```

#### Error Handling Patterns
```python
# Specific exception handling
try:
    result = api_call()
except APIError as e:
    logger.error(f"API call failed: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise LeadScoutError(f"Unexpected error: {e}") from e

# Resource cleanup
try:
    with open(file_path) as f:
        process_file(f)
except FileNotFoundError:
    logger.warning(f"File not found: {file_path}")
    return None
```

### Documentation Standards

#### Docstring Format (Google Style)
```python
def classify_name(name: str, confidence_threshold: float = 0.8) -> Classification:
    """Classify a name's ethnicity using multiple algorithms.
    
    Args:
        name: The name to classify
        confidence_threshold: Minimum confidence for classification
        
    Returns:
        Classification object containing ethnicity and confidence
        
    Raises:
        ValidationError: If name is empty or invalid
        APIError: If external classification service fails
        
    Example:
        >>> classify_name("John Smith")
        Classification(ethnicity="european", confidence=0.95)
    """
```

#### Class Documentation
```python
class LeadEnricher:
    """Enriches lead data with external information sources.
    
    This class coordinates the enrichment process by calling various
    external APIs and services to gather additional information about
    business leads.
    
    Attributes:
        config: Configuration object
        cache: Cache instance for storing results
        
    Example:
        >>> enricher = LeadEnricher(config)
        >>> enriched = enricher.enrich(lead)
    """
```

### Testing Standards

#### Test Organization
```python
# tests/unit/test_classification.py
import pytest
from unittest.mock import Mock, patch

from leadscout.classification import NameClassifier
from leadscout.models import Classification


class TestNameClassifier:
    """Test suite for NameClassifier."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = NameClassifier()
    
    def test_classify_european_name(self):
        """Test classification of European names."""
        result = self.classifier.classify("John Smith")
        assert result.ethnicity == "european"
        assert result.confidence > 0.8
    
    @pytest.mark.parametrize("name,expected", [
        ("John Smith", "european"),
        ("Thabo Mthembu", "african"),
        ("Priya Patel", "indian"),
    ])
    def test_classify_various_names(self, name, expected):
        """Test classification of various name types."""
        result = self.classifier.classify(name)
        assert result.ethnicity == expected
```

#### Test Categories
```python
# Mark tests by category
@pytest.mark.unit
def test_unit_functionality():
    """Unit test for isolated functionality."""
    pass

@pytest.mark.integration
def test_api_integration():
    """Integration test with external APIs."""
    pass

@pytest.mark.slow
def test_large_dataset():
    """Test with large datasets - marked as slow."""
    pass
```

### Logging Standards

#### Structured Logging
```python
import structlog

logger = structlog.get_logger(__name__)

# Log with context
logger.info(
    "Processing lead",
    lead_id=lead.id,
    company_name=lead.entity_name,
    processing_time=elapsed_time
)

# Log errors with exception info
try:
    result = process_lead(lead)
except Exception as e:
    logger.error(
        "Lead processing failed",
        lead_id=lead.id,
        error=str(e),
        exc_info=True
    )
    raise
```

#### Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about system operation
- **WARNING**: Something unexpected but not necessarily problematic
- **ERROR**: Error conditions that don't stop the program
- **CRITICAL**: Serious errors that may cause the program to stop

### Configuration Management

#### Settings Pattern
```python
from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""
    
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    claude_api_key: str = Field(..., env="CLAUDE_API_KEY")
    cache_dir: Path = Field(default=Path("./cache"), env="CACHE_DIR")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

#### Configuration Loading
```python
# Load configuration once at startup
config = Settings()

# Use dependency injection for configuration
def get_enricher(config: Settings = config) -> LeadEnricher:
    return LeadEnricher(config)
```

## Database Standards

### SQLAlchemy Models
```python
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class LeadCache(Base):
    """Cache table for enriched lead data."""
    
    __tablename__ = "lead_cache"
    
    id = Column(Integer, primary_key=True)
    lead_hash = Column(String(64), unique=True, nullable=False)
    entity_name = Column(String(255), nullable=False)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<LeadCache(id={self.id}, entity_name='{self.entity_name}')>"
```

### Database Operations
```python
# Use context managers for database operations
async def get_cached_lead(lead_hash: str) -> Optional[LeadCache]:
    """Get cached lead data."""
    async with get_db_session() as session:
        result = await session.execute(
            select(LeadCache).where(LeadCache.lead_hash == lead_hash)
        )
        return result.scalar_one_or_none()
```

## API Integration Standards

### HTTP Client Configuration
```python
import httpx
from typing import AsyncGenerator

async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Get configured HTTP client."""
    async with httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
    ) as client:
        yield client
```

### API Error Handling
```python
async def call_external_api(url: str, data: dict) -> dict:
    """Call external API with proper error handling."""
    try:
        async with get_http_client() as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        raise APIError(f"API call failed: {e.response.status_code}")
    except httpx.TimeoutException:
        logger.error("API call timed out")
        raise APIError("API timeout")
    except Exception as e:
        logger.error(f"Unexpected API error: {e}")
        raise APIError(f"Unexpected error: {e}")
```

## CLI Standards

### Click Command Structure
```python
import click
from typing import Optional

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config', '-c', type=click.Path(exists=True), help='Config file path')
@click.pass_context
def cli(ctx: click.Context, verbose: bool, config: Optional[str]) -> None:
    """LeadScout CLI application."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--batch-size', default=100, help='Batch size for processing')
@click.pass_context
def enrich(ctx: click.Context, input_file: str, output: Optional[str], batch_size: int) -> None:
    """Enrich leads from input file."""
    if ctx.obj['verbose']:
        click.echo(f"Processing {input_file} with batch size {batch_size}")
```

## Security Standards

### API Key Management
```python
# Never hardcode API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Use secure configuration loading
from pydantic import BaseSettings, SecretStr

class Settings(BaseSettings):
    openai_api_key: SecretStr
    
    def get_openai_key(self) -> str:
        return self.openai_api_key.get_secret_value()
```

### Input Validation
```python
from pydantic import BaseModel, validator

class LeadInput(BaseModel):
    """Input validation for lead data."""
    
    entity_name: str
    email_address: str
    phone_number: str
    
    @validator('entity_name')
    def validate_entity_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Entity name must be at least 2 characters')
        return v.strip()
    
    @validator('email_address')
    def validate_email(cls, v):
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError('Invalid email address')
        return v.lower()
```

## Performance Standards

### Async Programming
```python
import asyncio
from typing import List

async def process_leads_concurrently(leads: List[Lead]) -> List[EnrichedLead]:
    """Process multiple leads concurrently."""
    semaphore = asyncio.Semaphore(10)  # Limit concurrent operations
    
    async def process_with_semaphore(lead: Lead) -> EnrichedLead:
        async with semaphore:
            return await enrich_lead(lead)
    
    tasks = [process_with_semaphore(lead) for lead in leads]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### Caching Strategy
```python
from functools import lru_cache
from typing import Dict, Optional

class NameClassifier:
    """Name classifier with caching."""
    
    def __init__(self):
        self._cache: Dict[str, Classification] = {}
    
    @lru_cache(maxsize=1000)
    def _phonetic_match(self, name: str) -> Optional[str]:
        """Cached phonetic matching."""
        return compute_phonetic_code(name)
    
    async def classify(self, name: str) -> Classification:
        """Classify name with caching."""
        if name in self._cache:
            return self._cache[name]
        
        result = await self._classify_uncached(name)
        self._cache[name] = result
        return result
```

## File Organization Standards

### Package Structure
```
src/leadscout/
├── __init__.py                 # Package initialization
├── cli/                        # Command line interface
│   ├── __init__.py
│   ├── main.py                # Main CLI entry point
│   └── commands/              # CLI command modules
├── core/                      # Core business logic
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── exceptions.py          # Custom exceptions
│   └── utils.py               # Utility functions
├── models/                    # Data models
│   ├── __init__.py
│   ├── lead.py                # Lead data models
│   └── classification.py      # Classification models
├── enrichment/                # Data enrichment modules
│   ├── __init__.py
│   ├── base.py                # Base enrichment interface
│   ├── cipc.py                # CIPC integration
│   ├── linkedin.py            # LinkedIn integration
│   └── website.py             # Website discovery
├── classification/            # Name classification system
│   ├── __init__.py
│   ├── phonetic.py            # Phonetic algorithms
│   ├── llm.py                 # LLM integration
│   └── cache.py               # Classification cache
├── scoring/                   # Scoring engine
│   ├── __init__.py
│   ├── base.py                # Base scoring interface
│   └── default.py             # Default scoring implementation
└── cache/                     # Caching layer
    ├── __init__.py
    ├── sqlite.py              # SQLite cache implementation
    └── models.py              # Cache data models
```

### Import Standards
```python
# Preferred import patterns
from leadscout.models import Lead, EnrichedLead
from leadscout.core.config import Settings
from leadscout.enrichment.base import BaseEnricher

# Avoid wildcard imports
# from leadscout.models import *  # DON'T DO THIS

# Use relative imports within packages
from .base import BaseEnricher
from ..models import Lead
```

## Version Control Standards

### Commit Messages
```
feat: add ethnicity classification using phonetic matching

- Implement Soundex, Metaphone, and Double Metaphone algorithms
- Add confidence scoring for classification results
- Cache phonetic codes for performance optimization
- Include unit tests for all phonetic algorithms

Resolves #123
```

### Branch Naming
- `feature/ethnicity-classification`
- `bugfix/api-timeout-handling`
- `hotfix/critical-data-leak`
- `refactor/database-abstraction`

### Pull Request Guidelines
1. **Description**: Clear description of changes
2. **Testing**: Evidence of testing (unit tests, manual testing)
3. **Documentation**: Updated documentation if needed
4. **Breaking Changes**: Clearly marked breaking changes
5. **Review**: At least one reviewer approval required

## Code Review Standards

### Review Checklist
- [ ] Code follows style guidelines (Black, isort, flake8)
- [ ] Type hints are present and correct
- [ ] Error handling is appropriate
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] Performance considerations addressed
- [ ] Security implications considered
- [ ] No hardcoded credentials or sensitive data

### Review Comments
```python
# Good review comment
# Consider using asyncio.gather() here for better performance when processing multiple leads concurrently

# Bad review comment
# This is wrong, fix it
```

## Continuous Integration

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
```

### GitHub Actions
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install --with dev
    
    - name: Run tests
      run: |
        poetry run pytest --cov=leadscout
        poetry run black --check .
        poetry run isort --check-only .
        poetry run flake8 .
        poetry run mypy src/
```

## Documentation Standards

### Code Documentation
- All public functions and classes must have docstrings
- Use Google-style docstrings
- Include examples in docstrings where helpful
- Document complex algorithms and business logic

### API Documentation
- Document all CLI commands and options
- Include usage examples
- Document configuration options
- Provide troubleshooting guides

### Architecture Documentation
- Keep architecture documents up to date
- Document major design decisions
- Include diagrams where helpful
- Document API integrations and data flows

## Deployment Standards

### Environment Configuration
```python
# Use environment-specific settings
class Settings(BaseSettings):
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    class Config:
        env_file = f".env.{os.getenv('ENVIRONMENT', 'development')}"
```

### Docker Configuration
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY src/ ./src/
COPY README.md ./

CMD ["poetry", "run", "leadscout"]
```

These standards ensure that the LeadScout codebase remains maintainable, secure, and performant as it grows and evolves.