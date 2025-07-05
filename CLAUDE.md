# LeadScout - AI-Powered Lead Enrichment System

## Project Overview

LeadScout is a next-generation lead enrichment tool designed to research and score business leads using AI-powered analysis. The system takes Excel files containing lead data and enriches them with comprehensive research from multiple sources, focusing on South African business contexts.

## Core Functionality

### Input Processing
- **Input Format**: XLSX files with lead data
- **Required Fields**: EntityName, TradingAsName, Keyword, ContactNumber, CellNumber, EmailAddress, RegisteredAddress, RegisteredAddressCity, RegisteredAddressProvince, DirectorName, DirectorCell
- **Output**: Enhanced Excel file with enrichment flags and prioritization scores

### Data Enrichment Sources
1. **CIPC/CIPRO Registry**: South African company registration data
2. **Website Discovery**: Company website detection and analysis
3. **LinkedIn Research**: Director and company profile research
4. **Ethnicity Classification**: AI-powered name analysis for demographic targeting

### Scoring System
- **Pluggable Architecture**: Modular scoring components
- **Initial Scoring Criteria**: 
  - Data availability flags (CIPRO found, website found, LinkedIn presence)
  - Ethnicity classification scores
  - Contact completeness metrics
- **Business Priority**: Prioritize leads based on data richness and demographic factors

## Technical Architecture

### Core Technologies
- **Language**: Python 3.11+
- **Database**: SQLite for caching and data persistence
- **Package Management**: Poetry for dependency management
- **CLI Framework**: Click for command-line interface
- **Data Processing**: Pandas for Excel manipulation
- **HTTP Client**: httpx for async API calls
- **Validation**: Pydantic for data models

### System Components
1. **Data Pipeline**: Composable tool chain for processing leads
2. **Cache System**: SQLite-based caching for API results and name classifications
3. **Scoring Engine**: Pluggable scoring modules
4. **Research Modules**: Separate modules for each data source
5. **Name Classification**: Multi-layered phonetic + LLM classification system

## Name Classification System

### Multi-Layered Approach
1. **Exact Match Cache**: Previously classified names (100% confidence)
2. **Phonetic Matching**: Soundex, Metaphone, Double Metaphone, NYSIIS, Jaro-Winkler
3. **South African Linguistic Rules**: Afrikaans, Zulu, Xhosa, Sotho patterns
4. **LLM Fallback**: OpenAI/Claude classification for unknown names
5. **Active Learning**: Continuous improvement of classification accuracy

### Confidence Scoring
- **90-95%**: Multiple phonetic algorithms agree
- **80-90%**: Single algorithm + high string similarity
- **70-80%**: Fuzzy match with known variants
- **100%**: LLM classification (ground truth)

## Development Standards

### Code Quality
- **Type Hints**: All functions must include type annotations
- **Documentation**: Comprehensive docstrings using Google style
- **Testing**: Minimum 80% code coverage
- **Linting**: Black formatting, isort imports, flake8 compliance
- **Security**: No hardcoded credentials, secure API key management

### Project Structure
```
leadscout/
├── src/leadscout/           # Main package
│   ├── __init__.py
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

### Configuration Management
- **Environment Variables**: API keys and sensitive config
- **Config Files**: YAML/TOML for non-sensitive settings
- **Default Values**: Sensible defaults for all settings
- **Validation**: Configuration validation on startup

### Error Handling
- **Graceful Degradation**: System continues with partial data
- **Retry Logic**: Exponential backoff for API failures
- **Logging**: Structured logging with correlation IDs
- **Monitoring**: Track success rates and processing times

## API Integration Guidelines

### CIPC/CIPRO Integration
- **Rate Limiting**: Respect API limits and implement backoff
- **Data Validation**: Validate company registration data
- **Caching**: Cache results for 30 days (configurable)
- **Error Handling**: Handle various response formats

### LinkedIn Research
- **Compliance**: Ensure compliance with LinkedIn's terms of service
- **Rate Limiting**: Conservative approach to avoid blocking
- **Data Extraction**: Focus on publicly available information
- **Privacy**: No storage of personal data beyond what's needed

### LLM Integration
- **Provider Support**: OpenAI, Claude, Gemini compatibility
- **Fallback Strategy**: Multiple providers for reliability
- **Cost Optimization**: Batch processing and caching
- **Prompt Engineering**: Optimized prompts for ethnicity classification

## Data Management

### Caching Strategy
- **SQLite Schema**: Normalized tables for efficient querying
- **Cache Expiration**: Configurable TTL for different data types
- **Cache Warming**: Pre-populate cache with common names
- **Cleanup**: Automatic cleanup of expired entries

### Data Privacy
- **Compliance**: Full compliance with lead usage permissions
- **Retention**: Configurable data retention policies
- **Encryption**: Encrypt sensitive data at rest
- **Audit Trail**: Track all data access and modifications

## Testing Strategy

### Test Types
- **Unit Tests**: Individual component testing
- **Integration Tests**: API and database integration
- **End-to-End Tests**: Complete pipeline testing
- **Performance Tests**: Load testing with large datasets

### Test Data
- **Sample Leads**: Anonymized test data
- **Mock APIs**: Mock external services for testing
- **Edge Cases**: Test with malformed and edge case data
- **Ethnicity Validation**: Test classification accuracy

## Deployment and Operations

### Environment Setup
- **Development**: Local development with Docker
- **Testing**: CI/CD pipeline with automated testing
- **Production**: Containerized deployment
- **Monitoring**: Health checks and performance metrics

### Configuration
- **Environment Variables**: 
  - `OPENAI_API_KEY`: OpenAI API key
  - `CLAUDE_API_KEY`: Claude API key
  - `CIPC_API_KEY`: CIPC API key (if available)
  - `CACHE_DIR`: SQLite cache directory
  - `LOG_LEVEL`: Logging level

### Performance Targets
- **Processing Speed**: 100+ leads per minute
- **Memory Usage**: <500MB for 10,000 leads
- **API Efficiency**: <5 LLM calls per 100 names (after cache warmup)
- **Accuracy**: >95% ethnicity classification accuracy

## Contributing Guidelines

### Code Review Process
- **Pull Requests**: All changes via PR
- **Code Review**: Minimum one reviewer
- **Testing**: All tests must pass
- **Documentation**: Update docs with changes

### Commit Standards
- **Conventional Commits**: Use conventional commit format
- **Small Commits**: Atomic changes with clear messages
- **Branch Names**: Feature branches with descriptive names
- **No Direct Commits**: No direct commits to main branch

## Important Notes

### Business Context
- **South African Focus**: Optimized for SA business environment
- **Demographic Targeting**: Ethnicity classification for marketing prioritization
- **Lead Compliance**: Full compliance with lead usage permissions
- **Data Accuracy**: Prioritize data quality over processing speed

### Technical Decisions
- **Python Choice**: Balance of AI libraries and business logic
- **SQLite**: Lightweight, file-based database for caching
- **Async Processing**: Concurrent API calls for performance
- **Modular Design**: Pluggable components for extensibility

### Future Enhancements
- **CRM Integration**: Future integration with CRM systems
- **Real-time Processing**: API endpoint for real-time enrichment
- **Advanced Scoring**: Machine learning-based scoring models
- **Multi-language Support**: Support for additional languages

## Getting Started

### Prerequisites
- Python 3.11+
- Poetry for dependency management
- API keys for external services

### Installation
```bash
cd leadscout
poetry install
poetry run leadscout --help
```

### Basic Usage
```bash
# Process a lead file
poetry run leadscout enrich leads.xlsx --output enriched_leads.xlsx

# Check cache status
poetry run leadscout cache status

# Configure API keys
poetry run leadscout config set openai_api_key YOUR_KEY
```

This document serves as the comprehensive guide for all development activities on the LeadScout project. All code must align with these standards and architecture decisions.

## Claude Development Rules

**CRITICAL**: Read and follow these mandatory rules for all development work:

@CLAUDE_RULES.md
@docs/coding-standards.md

### Session Startup Checklist
1. **ALWAYS** read CLAUDE.md first for full project context
2. **ALWAYS** review CLAUDE_RULES.md for development standards
3. **ALWAYS** check recent commits and current branch status
4. **ALWAYS** run tests before making any changes
5. **NEVER** deviate from established architecture patterns

### Quality Gates (Non-Negotiable)
- All functions must have type hints and docstrings
- Minimum 80% test coverage for new code
- Black/isort/flake8 compliance required
- No hardcoded credentials or sensitive data
- Async patterns for all I/O operations