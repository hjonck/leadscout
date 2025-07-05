# LeadScout Claude Rules

## Project Identity & Mission

**Project**: LeadScout - AI-Powered Lead Enrichment System  
**Purpose**: Research and score business leads using AI for South African businesses  
**Architecture**: Modular Python CLI with pluggable components  
**Quality Standard**: Professional, enterprise-grade MVP

## Mandatory Reading Before Any Development

1. **CLAUDE.md** - Complete project context and technical specifications
2. **docs/coding-standards.md** - Non-negotiable coding standards
3. **docs/architecture/system-design.md** - System architecture and design patterns
4. **README.md** - User-facing documentation and project overview

## Core Development Principles

### 1. Architecture Consistency
- **NEVER** deviate from the established modular architecture
- **ALWAYS** follow the package structure defined in `src/leadscout/`
- **REQUIRED** patterns: dependency injection, async processing, pluggable scoring
- **FORBIDDEN** patterns: monolithic code, synchronous blocking operations, hardcoded values

### 2. Code Quality Standards
- **MANDATORY**: Type hints on all functions and class attributes
- **MANDATORY**: Google-style docstrings for all public functions/classes
- **MANDATORY**: Error handling with custom exception hierarchy
- **MANDATORY**: Structured logging with context
- **FORBIDDEN**: Wildcard imports, hardcoded credentials, print statements

### 3. Testing Requirements
- **MINIMUM**: 80% code coverage for all new code
- **REQUIRED**: Unit tests for all business logic
- **REQUIRED**: Integration tests for API interactions
- **REQUIRED**: Parametrized tests for classification algorithms

## File and Folder Conventions

### Project Structure (IMMUTABLE)
```
leadscout/
├── src/leadscout/           # Main package - NEVER change this structure
│   ├── cli/                 # Command line interface
│   ├── core/                # Core business logic
│   ├── enrichment/          # Data enrichment modules
│   ├── scoring/             # Scoring engine
│   ├── classification/      # Name classification system
│   ├── cache/               # Caching layer
│   └── models/              # Data models
├── tests/                   # Test suite
├── docs/                    # Documentation
├── data/                    # Sample data and templates
├── cache/                   # SQLite cache files
├── config/                  # Configuration files
└── scripts/                 # Utility scripts
```

### Naming Conventions
- **Files**: snake_case (e.g., `name_classifier.py`)
- **Classes**: PascalCase (e.g., `NameClassifier`)
- **Functions/Variables**: snake_case (e.g., `classify_name`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_CONFIDENCE_THRESHOLD`)
- **Modules**: Short, descriptive names (e.g., `cipc.py`, `linkedin.py`)

### Import Organization (STRICT)
```python
# 1. Standard library imports
import os
import sys
from pathlib import Path

# 2. Third-party imports
import click
import pandas as pd
from pydantic import BaseModel

# 3. Local imports
from leadscout.core import config
from leadscout.models.lead import Lead
```

## Development Workflow Rules

### 1. Before Writing Any Code
- **ALWAYS** check if similar functionality exists
- **ALWAYS** review existing patterns before implementing new ones
- **ALWAYS** consider the pluggable architecture
- **ALWAYS** think about caching and performance

### 2. Adding New Features
1. Create/update data models in `models/`
2. Implement core logic in appropriate module
3. Add CLI interface in `cli/`
4. Write comprehensive tests
5. Update documentation

### 3. API Integrations
- **REQUIRED**: Use httpx async client
- **REQUIRED**: Implement retry logic with exponential backoff
- **REQUIRED**: Rate limiting for all external APIs
- **REQUIRED**: Comprehensive error handling
- **FORBIDDEN**: Synchronous requests, unhandled timeouts

## Critical Business Logic Rules

### 1. Name Classification System
- **IMMUTABLE ARCHITECTURE**: Exact match → Phonetic match → LLM fallback
- **REQUIRED ALGORITHMS**: Soundex, Metaphone, Double Metaphone, NYSIIS, Jaro-Winkler
- **CACHE STRATEGY**: SQLite with confidence scores and TTL
- **PERFORMANCE TARGET**: <5% LLM calls after cache warmup

### 2. Lead Enrichment Pipeline
- **DATA SOURCES**: CIPC/CIPRO, Website Discovery, LinkedIn, Contact Validation
- **PROCESSING**: Async batch processing with configurable concurrency
- **ERROR HANDLING**: Graceful degradation, partial results on failures
- **CACHING**: 30-day TTL for all external API results

### 3. Scoring System
- **ARCHITECTURE**: Pluggable scoring modules with weight configuration
- **DEFAULT WEIGHTS**: CIPC(30%), Website(25%), LinkedIn(25%), Contact Quality(20%)
- **OUTPUT**: Normalized scores 0-100 with confidence levels
- **EXTENSIBILITY**: Easy addition of new scoring criteria

## Security & Privacy Rules

### 1. Data Protection (NON-NEGOTIABLE)
- **FORBIDDEN**: Hardcoded API keys, credentials in code
- **REQUIRED**: Environment variable configuration
- **REQUIRED**: Encryption for sensitive cached data
- **REQUIRED**: POPIA compliance for South African data

### 2. API Security
- **REQUIRED**: Secure credential storage using pydantic SecretStr
- **REQUIRED**: Input validation for all user data
- **REQUIRED**: Rate limiting and respectful API usage
- **FORBIDDEN**: Logging sensitive information

### 3. Privacy Compliance
- **REQUIRED**: Configurable data retention policies
- **REQUIRED**: Audit trail for all data processing
- **ALLOWED**: Full compliance with lead usage permissions
- **FORBIDDEN**: Unnecessary data collection or retention

## Configuration Management Rules

### 1. Settings Architecture
- **BASE CLASS**: Use pydantic BaseSettings
- **ENVIRONMENT**: Support .env files and environment variables
- **VALIDATION**: Schema validation for all configuration
- **SECURITY**: SecretStr for sensitive values

### 2. Configuration Files
```python
# REQUIRED pattern for all configuration
class Settings(BaseSettings):
    openai_api_key: SecretStr = Field(..., env="OPENAI_API_KEY")
    cache_dir: Path = Field(default=Path("./cache"), env="CACHE_DIR")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

## CLI Design Rules

### 1. Command Structure (IMMUTABLE)
```bash
leadscout enrich input.xlsx --output output.xlsx --batch-size 100
leadscout cache status
leadscout cache clean
leadscout config set openai_api_key YOUR_KEY
leadscout config test
```

### 2. CLI Conventions
- **REQUIRED**: Click framework for all CLI commands
- **REQUIRED**: Comprehensive help text for all commands
- **REQUIRED**: Progress indicators for long-running operations
- **REQUIRED**: Verbose mode support
- **FORBIDDEN**: Breaking changes to existing command interfaces

## Testing Standards (MANDATORY)

### 1. Test Organization
```
tests/
├── unit/                    # Unit tests for individual components
├── integration/             # API and database integration tests
├── e2e/                     # End-to-end pipeline tests
└── fixtures/                # Test data and mock objects
```

### 2. Test Requirements
- **REQUIRED**: pytest with async support
- **REQUIRED**: Mock external APIs in unit tests
- **REQUIRED**: Real API tests in integration suite (with rate limiting)
- **REQUIRED**: Performance benchmarks for critical paths

### 3. Test Naming
```python
class TestNameClassifier:
    def test_classify_european_name_returns_correct_ethnicity(self):
        """Test that European names are classified correctly."""
        pass
    
    def test_classify_invalid_name_raises_validation_error(self):
        """Test that invalid names raise ValidationError."""
        pass
```

## Performance Requirements (NON-NEGOTIABLE)

### 1. Processing Targets
- **MINIMUM**: 100+ leads per minute
- **MEMORY**: <500MB for 10,000 leads
- **API EFFICIENCY**: <5% LLM calls after cache warmup
- **ACCURACY**: >95% ethnicity classification accuracy

### 2. Optimization Rules
- **REQUIRED**: Async processing for all I/O operations
- **REQUIRED**: Connection pooling for HTTP clients
- **REQUIRED**: Intelligent caching with TTL management
- **REQUIRED**: Batch processing for large datasets

## Documentation Requirements

### 1. Code Documentation
- **REQUIRED**: Docstrings for all public functions and classes
- **REQUIRED**: Type hints for all function signatures
- **REQUIRED**: Usage examples in docstrings
- **REQUIRED**: Architecture decision records for major changes

### 2. User Documentation
- **REQUIRED**: Keep README.md updated with all changes
- **REQUIRED**: CLI help text for all commands
- **REQUIRED**: Configuration examples
- **REQUIRED**: Troubleshooting guides

## Error Handling Standards

### 1. Exception Hierarchy (IMMUTABLE)
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

class ConfigurationError(LeadScoutError):
    """Configuration-related errors."""
    pass
```

### 2. Error Handling Patterns
- **REQUIRED**: Specific exception handling, avoid bare except
- **REQUIRED**: Structured logging for all errors
- **REQUIRED**: User-friendly error messages
- **FORBIDDEN**: Silent failures, generic error messages

## Dependencies Management

### 1. Poetry Configuration (IMMUTABLE)
- **REQUIRED**: Use Poetry for all dependency management
- **REQUIRED**: Pin major versions, allow minor/patch updates
- **REQUIRED**: Separate dev dependencies from runtime
- **FORBIDDEN**: Direct pip installs, unpinned dependencies

### 2. Dependency Categories
```toml
[tool.poetry.dependencies]
python = "^3.11"
# Core framework dependencies
click = "^8.1.7"
pydantic = "^2.5.0"
# AI/ML dependencies
openai = "^1.6.0"
anthropic = "^0.8.0"

[tool.poetry.group.dev.dependencies]
# Testing
pytest = "^7.4.0"
# Code quality
black = "^23.12.0"
```

## Version Control Rules

### 1. Commit Standards
- **REQUIRED**: Conventional commit format
- **REQUIRED**: Clear, descriptive commit messages
- **REQUIRED**: Small, atomic commits
- **FORBIDDEN**: Large commits mixing multiple concerns

### 2. Branch Protection
- **REQUIRED**: Pull request reviews for all changes
- **REQUIRED**: All tests must pass before merge
- **REQUIRED**: Code quality checks must pass
- **FORBIDDEN**: Direct commits to main branch

## Deployment Standards

### 1. Environment Management
- **REQUIRED**: Environment-specific configuration
- **REQUIRED**: Docker containerization
- **REQUIRED**: Health checks and monitoring
- **FORBIDDEN**: Environment-specific code

### 2. Release Process
- **REQUIRED**: Semantic versioning
- **REQUIRED**: Release notes for all versions
- **REQUIRED**: Automated testing in CI/CD
- **REQUIRED**: Performance benchmarks for releases

## Session Continuity Rules

### 1. Starting New Sessions
1. **ALWAYS** read CLAUDE.md first for full context
2. **ALWAYS** review recent commits and current branch
3. **ALWAYS** run tests before making changes
4. **ALWAYS** check existing patterns before implementing

### 2. Session Handover
- **REQUIRED**: Clear documentation of work in progress
- **REQUIRED**: Updated TODO items in project tracking
- **REQUIRED**: Clear next steps and blockers
- **FORBIDDEN**: Leaving sessions with broken tests or partial implementations

## Quality Gates (MANDATORY)

### 1. Before Any Commit
- [ ] All tests pass
- [ ] Code formatting (black, isort)
- [ ] Type checking (mypy)
- [ ] Linting (flake8)
- [ ] Security scan (bandit)

### 2. Before Any Release
- [ ] Full test suite passes
- [ ] Performance benchmarks meet targets
- [ ] Documentation is updated
- [ ] Security review completed
- [ ] Breaking changes documented

## Integration Rules

### 1. External APIs
- **CIPC/CIPRO**: Official South African company registry
- **LinkedIn**: Professional networking data (respect terms of service)
- **OpenAI/Claude**: LLM services for name classification
- **Website Discovery**: Intelligent domain detection and validation

### 2. API Client Requirements
- **REQUIRED**: Async HTTP client (httpx)
- **REQUIRED**: Rate limiting and backoff
- **REQUIRED**: Comprehensive error handling
- **REQUIRED**: Request/response logging (without sensitive data)

## Project Evolution Rules

### 1. Adding New Features
1. **ALWAYS** create design document first
2. **ALWAYS** consider impact on existing architecture
3. **ALWAYS** maintain backward compatibility
4. **ALWAYS** update documentation and tests

### 2. Refactoring
- **REQUIRED**: Comprehensive test coverage before refactoring
- **REQUIRED**: Maintain public API compatibility
- **REQUIRED**: Performance validation after refactoring
- **FORBIDDEN**: Refactoring without clear business value

## Failure Recovery

### 1. If Project Drifts from Standards
1. Stop all development
2. Review CLAUDE.md and coding standards
3. Run full test suite and quality checks
4. Fix all violations before continuing
5. Document lessons learned

### 2. If Architecture Violations Occur
1. Assess impact and scope
2. Create migration plan if needed
3. Update documentation
4. Ensure team alignment
5. Prevent future violations

## Success Metrics

### 1. Code Quality
- Test coverage >80%
- Type coverage >95%
- Zero linting violations
- Zero security vulnerabilities

### 2. Performance
- Lead processing >100/minute
- Memory usage <500MB per 10K leads
- API efficiency <5% LLM calls
- Classification accuracy >95%

### 3. Maintainability
- Clear, consistent architecture
- Comprehensive documentation
- Easy onboarding for new developers
- Minimal technical debt

---

**REMEMBER**: These rules exist to maintain the professional quality and architectural integrity of LeadScout. They are not suggestions—they are requirements for all development work on this project.

**ENFORCEMENT**: Any session that violates these rules should be stopped and corrected before continuing. Quality and consistency are non-negotiable.

**EVOLUTION**: These rules can only be updated through explicit discussion and documented decision. Never ignore or work around these rules without explicit justification and approval.