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

### 3. Verification and Skepticism Requirement
- **CRITICAL RULE**: **NEVER ASSUME ANYTHING WORKS** until tested and verified
- **MANDATORY**: Test all code changes with actual test cases before claiming success
- **FORBIDDEN**: Over-optimistic assumptions about functionality without verification
- **REQUIRED**: Skeptical approach - expect things to fail until proven otherwise
- **REQUIRED**: Verify all fixes with concrete test execution and results
- **FORBIDDEN**: Saying "this should work" or "expected to work" without testing
- **MANDATORY**: Provide actual test results and evidence when reporting functionality

### 4. Testing Requirements
- **MINIMUM**: 80% code coverage for all new code
- **REQUIRED**: Unit tests for all business logic
- **REQUIRED**: Integration tests for API interactions
- **REQUIRED**: Parametrized tests for classification algorithms
- **CRITICAL**: All fixes must be validated with test execution before reporting success

### 5. Background Processing and Logging Requirements
- **MANDATORY**: All long-running scripts must support background execution
- **REQUIRED**: All scripts must output to structured log files, not just stdout
- **REQUIRED**: Progress monitoring capabilities for long-running operations
- **MANDATORY**: Separate debug and production logging levels
- **REQUIRED**: Meaningful production output with minimal noise
- **FORBIDDEN**: Scripts that timeout or block interactive sessions
- **REQUIRED**: Async processing with proper timeout handling for batch operations

### 6. Structured Logging Standards (Based on Review Team Feedback)
- **MANDATORY**: Use `structlog` for all logging (not basic `logging.getLogger`)
- **REQUIRED**: Include structured context in all log messages
- **REQUIRED**: Environment-specific logging configuration (JSON for prod, console for dev)
- **MANDATORY**: Create centralized logging setup in `src/leadscout/core/logging.py`
- **REQUIRED**: Add logging configuration to Settings class
- **FORBIDDEN**: Print statements or unstructured logging in production code
- **REQUIRED**: Log rotation and proper file organization

### 7. Resumable Job Processing Framework (CRITICAL PRODUCTION REQUIREMENT)

#### **7.1 Fundamental Resumable Job Principle**
- **MANDATORY**: ALL long-running operations MUST be resumable from any interruption point
- **CRITICAL RULE**: Jobs processing 500+ leads MUST support conservative resume with zero data loss
- **REQUIRED**: Stream processing with SQLite intermediate storage (never load entire file into memory)
- **FORBIDDEN**: In-memory processing of large datasets without persistent checkpoints

#### **7.2 Job Architecture Requirements**
- **MANDATORY**: Batch processing with configurable batch size (default: 100 leads per batch)
- **REQUIRED**: Conservative resume strategy - always resume from last committed batch
- **MANDATORY**: SQLite-based job metadata and locking system
- **REQUIRED**: Automatic job resumption by default when same input file is processed
- **FORBIDDEN**: Concurrent processing of the same input file (enforced via DB locks)

#### **7.3 SQLite Schema Design**
```sql
-- MANDATORY schema for all resumable jobs
CREATE TABLE job_executions (
    job_id TEXT PRIMARY KEY,
    input_file_path TEXT NOT NULL,
    input_file_modified_time INTEGER NOT NULL,  -- File mtime for change detection
    output_file_path TEXT,
    total_rows INTEGER,
    batch_size INTEGER DEFAULT 100,
    last_committed_batch INTEGER DEFAULT 0,
    processed_leads_count INTEGER DEFAULT 0,
    failed_leads_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running',  -- 'running', 'completed', 'failed', 'paused'
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completion_time TIMESTAMP,
    api_costs_total REAL DEFAULT 0.0,
    processing_time_total_ms REAL DEFAULT 0.0,
    error_summary TEXT,
    created_by TEXT,  -- Process/session identifier
    UNIQUE(input_file_path, status) WHERE status = 'running'  -- Prevent concurrent jobs
);

CREATE TABLE lead_processing_results (
    job_id TEXT,
    row_index INTEGER,
    batch_number INTEGER,
    entity_name TEXT,
    director_name TEXT,
    classification_result JSON,
    processing_status TEXT,  -- 'success', 'failed', 'retry_exhausted'
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    error_type TEXT,  -- 'rate_limit', 'api_error', 'validation_error', 'timeout'
    processing_time_ms REAL,
    api_provider TEXT,  -- 'openai', 'anthropic', 'rule_based', 'phonetic'
    api_cost REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (job_id, row_index),
    FOREIGN KEY (job_id) REFERENCES job_executions(job_id)
);

CREATE TABLE job_locks (
    input_file_path TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    locked_by TEXT,  -- Process identifier
    FOREIGN KEY (job_id) REFERENCES job_executions(job_id)
);
```

#### **7.4 Rate Limit Management**
- **MANDATORY**: Research and implement actual API rate limits for each provider
- **REQUIRED**: OpenAI rate limit compliance (3 RPM for free tier, higher for paid)
- **REQUIRED**: Anthropic rate limit compliance (5 RPM standard, check current limits)
- **MANDATORY**: Exponential backoff with provider-specific parameters
- **REQUIRED**: Automatic provider switching when rate limits exceeded repeatedly
- **FORBIDDEN**: Guessing rate limits - must use documented API limits

#### **7.5 Error Handling and Retry Strategy**
- **MANDATORY**: Classify errors into categories: 'rate_limit', 'api_error', 'validation_error', 'timeout'
- **REQUIRED**: Microbatch processing for failed leads (batch size = 1) with 3 retry attempts
- **REQUIRED**: Provider switching for persistent failures after 3 attempts on same provider
- **MANDATORY**: Conservative batch commit - only commit successful results within batch
- **REQUIRED**: Track retry count and error reasons for all failures
- **FORBIDDEN**: Infinite retry loops - enforce maximum retry limits

#### **7.6 Progress Tracking and Monitoring**
- **MANDATORY**: Log progress with every completed batch using structured logging
- **REQUIRED**: Real-time progress calculation: (processed_leads / total_rows) * 100
- **REQUIRED**: Performance metrics per batch: processing_time_ms, api_costs, success_rate
- **MANDATORY**: Minimal performance metrics storage for future optimization
- **REQUIRED**: Progress log format: "Batch {batch_num}/{total_batches} completed - {processed}/{total} leads - {success_rate}% success"

#### **7.7 Job Resume Logic**
- **MANDATORY**: Auto-detect existing jobs for same input file and resume by default
- **REQUIRED**: Conservative resume: start from (last_committed_batch + 1) * batch_size
- **REQUIRED**: Verify input file hasn't changed using stored modified_time
- **MANDATORY**: Clear messaging when resuming: "Resuming job {job_id} from batch {batch_num}"
- **FORBIDDEN**: Optimistic resume that might cause data inconsistency

#### **7.8 Streaming Data Processing**
- **MANDATORY**: Stream Excel data in batches, never load entire file into memory
- **REQUIRED**: Process leads in chunks of configured batch size
- **REQUIRED**: Immediate SQLite commit after each successful batch
- **FORBIDDEN**: In-memory accumulation of results beyond single batch size
- **REQUIRED**: Memory-efficient iteration through large Excel files

#### **7.9 Output Generation**
- **MANDATORY**: On-demand output generation from SQLite data
- **REQUIRED**: Support multiple output formats: Excel, CSV, JSON
- **REQUIRED**: Include failed leads in separate output section/file
- **MANDATORY**: Output generation independent of job processing status
- **REQUIRED**: Command structure: `generate_output.py --job-id {job_id} --format excel`

#### **7.10 Job Validation and Integrity**
- **MANDATORY**: Post-completion validation of all jobs
- **REQUIRED**: Validate: processed_count + failed_count = total_input_rows
- **REQUIRED**: Verify SQLite data integrity and consistency
- **REQUIRED**: Confirm output files match SQLite stored results
- **MANDATORY**: Report validation results and any discrepancies
- **FORBIDDEN**: Consider job complete without validation pass

#### **7.11 Job Lifecycle Management**
- **REQUIRED**: Job status transitions: 'running' → 'completed'/'failed'
- **MANDATORY**: Automatic lock cleanup on job completion
- **REQUIRED**: Manual job cleanup commands for maintenance
- **REQUIRED**: Job archival strategy for completed jobs
- **FORBIDDEN**: Automatic deletion of job data without explicit user action

#### **7.12 Configuration Management**
- **REQUIRED**: Batch size configuration via parameter file initially
- **FUTURE**: Database-stored optimization parameters for threading
- **REQUIRED**: Provider-specific rate limit configuration
- **REQUIRED**: Retry and backoff parameter configuration
- **MANDATORY**: All job parameters must be stored with job metadata

#### **7.13 Concurrent Job Prevention**
- **MANDATORY**: SQLite-based job locking with metadata
- **REQUIRED**: Check for existing locks before starting new job
- **REQUIRED**: Automatic lock cleanup on graceful job completion
- **REQUIRED**: Stale lock detection and recovery procedures
- **FORBIDDEN**: Multiple jobs processing same input file simultaneously

#### **7.14 Performance Optimization Foundation**
- **REQUIRED**: Store minimal performance metrics for analysis
- **REQUIRED**: Track: avg_processing_time_per_lead, api_calls_per_provider, cost_per_lead
- **REQUIRED**: Batch performance analytics for future threading optimization
- **FUTURE**: Database-driven batch size optimization based on historical performance
- **REQUIRED**: Performance baseline establishment for regression detection

#### **7.15 LLM-Driven Auto-Improvement System (CRITICAL COST OPTIMIZATION)**
- **MANDATORY**: Cache all successful LLM classifications for auto-improvement
- **REQUIRED**: Extract patterns from LLM successes to enhance rule-based classification
- **REQUIRED**: Build phonetic mappings from LLM-classified names automatically
- **MANDATORY**: Create feedback loop: LLM success → Rule enhancement → Reduced LLM dependency
- **REQUIRED**: Automatic rule generation from LLM classification patterns
- **FORBIDDEN**: Discarding LLM results without learning from them

#### **7.16 Auto-Enhancement Schema Extensions**
```sql
-- MANDATORY additions to lead_processing_results table for auto-learning
ALTER TABLE lead_processing_results ADD COLUMN phonetic_codes JSON;  -- Store phonetic variants
ALTER TABLE lead_processing_results ADD COLUMN learned_patterns JSON;  -- Extracted patterns
ALTER TABLE lead_processing_results ADD COLUMN confidence_factors JSON;  -- Why LLM was confident

-- Auto-generated rule storage
CREATE TABLE IF NOT EXISTS auto_generated_rules (
    rule_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,  -- Name that generated this rule
    source_job_id TEXT,  -- Job where pattern was learned
    rule_type TEXT,  -- 'prefix', 'suffix', 'phonetic', 'substring', 'pattern'
    rule_pattern TEXT,  -- The actual pattern/rule
    target_ethnicity TEXT,  -- What this rule classifies to
    confidence_score REAL,  -- Confidence in this auto-generated rule
    usage_count INTEGER DEFAULT 0,  -- How many times rule has been applied
    success_rate REAL DEFAULT 0.0,  -- Success rate when applied
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    FOREIGN KEY (source_job_id) REFERENCES job_executions(job_id)
);

-- Pattern learning analytics
CREATE TABLE IF NOT EXISTS pattern_learning_analytics (
    pattern_id TEXT PRIMARY KEY,
    pattern_type TEXT,  -- 'name_prefix', 'name_suffix', 'phonetic_group', 'linguistic_pattern'
    pattern_value TEXT,
    ethnicity TEXT,
    confidence_score REAL,
    sample_names JSON,  -- Names that support this pattern
    validation_names JSON,  -- Names used to validate pattern
    created_from_job_id TEXT,
    accuracy_rate REAL DEFAULT 0.0,
    total_applications INTEGER DEFAULT 0,
    FOREIGN KEY (created_from_job_id) REFERENCES job_executions(job_id)
);
```

#### **7.17 Auto-Learning Implementation Requirements**
- **MANDATORY**: After each LLM classification, extract learnable patterns
- **REQUIRED**: Generate phonetic codes for all LLM-classified names
- **REQUIRED**: Identify name components (prefixes, suffixes, roots) from LLM successes
- **MANDATORY**: Auto-create rules with confidence thresholds for future use
- **REQUIRED**: Validate auto-generated rules against existing successful classifications
- **FORBIDDEN**: Using auto-generated rules without confidence validation

#### **7.18 Cost Optimization Through Learning**
- **TARGET**: Achieve <5% LLM usage through intelligent rule learning
- **REQUIRED**: Track LLM cost reduction over time as rules improve
- **MANDATORY**: Measure rule effectiveness: (auto_classifications / total_classifications)
- **REQUIRED**: Regular purging of low-performing auto-generated rules
- **TARGET**: 80%+ cost reduction through accumulated learning

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
- **MANDATORY**: Start with skeptical mindset - assume existing code may have issues
- **REQUIRED**: Plan test cases before writing implementation code
- **FORBIDDEN**: Assuming anything works without verification

### 2. Project Estimation Policy
- **FORBIDDEN**: Time estimates for development tasks
- **REASON**: Time estimates are unreliable and create false expectations
- **INSTEAD**: Focus on priority order and completion criteria
- **ALLOWED**: Complexity assessment (simple/moderate/complex)

### 3. Virtual Environment Management
- **MANDATORY**: Always use local project virtual environment `.venv`
- **ACTIVATION**: All Python commands must use `source .venv/bin/activate &&` prefix
- **INSTALLATION**: Use Poetry within the activated virtual environment
- **FORBIDDEN**: Global package installations or system Python usage
- **ISOLATION**: Each project must have its own isolated environment

### 4. Project Tracking System
- **MANDATORY**: Use `PROJECT_PLAN.md` for all project planning and tracking
- **LOCATION**: Root directory of project
- **FORMAT**: Structured markdown with phases, tasks, and completion status
- **UPDATES**: Must be updated with every significant development session
- **NEVER**: Use external project management tools for core planning

### 5. File Documentation Standards
- **MANDATORY**: Every source file must begin with comprehensive module docstring
- **FORMAT**: Multi-line docstring explaining purpose, architecture, and key components
- **CONTENT REQUIREMENTS**:
  - What the module does and why it exists
  - Key classes, functions, and their relationships
  - Integration points with other modules
  - Usage examples for complex functionality
  - Architecture decisions and design patterns used
- **SESSION EFFICIENCY**: Docstrings must enable Claude sessions to understand module purpose instantly
- **DEVELOPER HANDOFF**: Docstrings must enable seamless work distribution between Claude developers

### 6. Multi-Claude Development Framework
- **PROJECT MANAGER ROLE**: One Claude session acts as Project Manager/Technical Lead
- **DEVELOPER ROLES**: Two specialist Claude developers handle specific modules
- **TASK DISTRIBUTION**: Use `dev-tasks/` directory for developer assignments
- **COMMUNICATION**: All coordination via structured markdown files
- **VERIFICATION**: Project Manager validates all developer work before integration
- **SPECIALIZATION**: 
  - Developer A: CIPC Integration & Caching System
  - Developer B: Name Classification & Enrichment Pipeline

### 7. Verification and Testing Workflow (MANDATORY)
- **CRITICAL**: Every fix, feature, or change MUST be verified with test execution
- **FORBIDDEN**: Claiming something is "fixed" or "working" without running tests
- **REQUIRED**: Provide concrete test results and evidence when reporting progress
- **MANDATORY**: Run diagnostic/validation scripts after making changes
- **REQUIRED**: Test edge cases and failure scenarios, not just happy path
- **FORBIDDEN**: Over-optimistic language without verification ("should work", "expected to work")
- **MANDATORY**: Document actual test execution results and outputs

### 8. Adding New Features
1. Create/update data models in `models/`
2. Implement core logic in appropriate module
3. Add CLI interface in `cli/`
4. Write comprehensive tests
5. **VERIFY**: Execute tests and provide results
6. Update documentation

## API Integration Rules

### 1. API Integrations
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
- **DATA SOURCES**: CIPC Registry, Name Classification, Website Discovery, LinkedIn, Contact Validation
- **CIPC INTEGRATION**: Priority data source using monthly CSV downloads (26 files by letter)
- **CIPC URL PATTERN**: `https://www.cipc.co.za/wp-content/uploads/<YYYY>/<MM>/List-<N>.csv`
- **PROCESSING**: Async batch processing with configurable concurrency
- **ERROR HANDLING**: Graceful degradation, partial results on failures
- **CACHING**: 30-day TTL for external APIs, persistent cache for CIPC data

### 3. Scoring System
- **ARCHITECTURE**: Pluggable scoring modules with weight configuration
- **DEFAULT WEIGHTS**: CIPC Match(25%), Name Classification(25%), Website(25%), LinkedIn(15%), Contact Quality(10%)
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
5. **MANDATORY**: Approach with skepticism - verify current state before proceeding

### 2. Session Handover
- **REQUIRED**: Clear documentation of work in progress
- **REQUIRED**: Updated TODO items in project tracking
- **REQUIRED**: Clear next steps and blockers
- **REQUIRED**: Concrete test results and verification evidence
- **FORBIDDEN**: Leaving sessions with broken tests or partial implementations
- **FORBIDDEN**: Handover with unverified claims or assumptions

## Communication and Reporting Standards

### 1. Progress Reporting Requirements
- **MANDATORY**: All progress reports must include actual test execution results
- **REQUIRED**: Specific error messages, outputs, and evidence when reporting issues
- **FORBIDDEN**: Vague statements like "it should work" or "expected to work"
- **REQUIRED**: Screenshots, logs, or command outputs as evidence
- **MANDATORY**: Clear distinction between "implemented" vs "implemented and verified"

### 2. Problem Reporting Standards
- **REQUIRED**: Exact error messages and stack traces
- **REQUIRED**: Steps to reproduce the problem
- **REQUIRED**: Environment details and configuration state
- **FORBIDDEN**: Assumptions about root causes without investigation
- **MANDATORY**: Multiple test cases to isolate the issue

### 3. Solution Verification Standards
- **CRITICAL**: Never report a solution as complete without test execution
- **REQUIRED**: Before/after test results showing the improvement
- **REQUIRED**: Edge case testing to ensure robustness
- **FORBIDDEN**: Theoretical solutions without practical verification
- **MANDATORY**: Regression testing to ensure no new issues introduced

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