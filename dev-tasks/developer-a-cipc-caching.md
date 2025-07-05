# Developer A: CIPC Integration & Caching System

## Developer Assignment
**Role**: CIPC Integration & Caching Specialist  
**Primary Responsibility**: Build the core data infrastructure for South African company registry integration and high-performance caching system.

## CRITICAL: Read These Files First
1. **CLAUDE.md** - Complete project context and standards
2. **CLAUDE_RULES.md** - Development rules and architecture decisions  
3. **docs/architecture/updated-system-design.md** - Your specific architecture requirements
4. **docs/architecture/ethnicity classification and cpiro data.md** - Research foundation

## Your Specialization Scope

### Core Responsibilities
1. **CIPC Data Integration**: Automated monthly CSV download and processing system
2. **ETL Pipeline**: Extract, transform, and load CIPC data with company name parsing
3. **Caching Architecture**: Multi-tier caching with Redis and PostgreSQL
4. **Company Search Engine**: Fuzzy matching and disambiguation for business lookup
5. **Data Storage**: Database schema design and optimization for name classification

### Integration Points with Developer B
- **Provides**: Cached name classifications and company data via APIs
- **Consumes**: Name classification requests and results for caching
- **Shared**: Database schema for name classifications table

## Technical Requirements

### MANDATORY: Follow All Project Standards
- **Virtual Environment**: Always use `source .venv/bin/activate &&` for all commands
- **Type Hints**: Every function must have complete type annotations
- **Docstrings**: Comprehensive module and function documentation
- **Error Handling**: Use custom exception hierarchy from `core.exceptions`
- **Async Patterns**: All I/O operations must be async
- **Testing**: Minimum 80% code coverage with pytest

### Architecture Implementation

#### 1. CIPC Integration Module (`src/leadscout/cipc/`)

**Required Files Structure:**
```
src/leadscout/cipc/
├── __init__.py          # Module exports
├── downloader.py        # CSV download orchestrator  
├── parser.py            # Company name extraction
├── models.py            # CIPC data models
├── search.py            # Company search engine
└── exceptions.py        # CIPC-specific exceptions
```

**Key Components to Implement:**

**A. CSV Download System (`downloader.py`)**
```python
"""CIPC CSV download and management system.

This module handles the automated download of all 26 CIPC CSV files
(one per alphabet letter) on a monthly schedule. It implements robust
error handling, retry logic, and validation to ensure data integrity.

Key Features:
- Parallel download of all 26 CSV files
- Automatic URL construction for current month
- Retry logic with exponential backoff
- File validation and integrity checking
- Download progress tracking and logging

Architecture Decision: Uses httpx for async downloads with connection pooling
to efficiently handle the 26 concurrent file downloads while respecting
CIPC server limits.

Integration: Works with parser.py to trigger ETL pipeline after successful downloads.
"""

class CIPCDownloader:
    async def download_monthly_batch(self, year: int, month: int) -> List[Path]
    async def download_single_file(self, letter_code: int) -> Path
    async def validate_csv_file(self, file_path: Path) -> bool
    async def get_latest_available_month(self) -> Tuple[int, int]
```

**B. Name Extraction Parser (`parser.py`)**
```python
"""Company name parsing and personal name extraction.

This module processes CIPC CSV data to extract personal names from company names,
implementing the research-based approach for identifying natural person names
within business entity names.

Key Features:
- Company name tokenization and splitting
- Personal name pattern recognition
- Deduplication using phonetic keys
- Multi-language name handling for SA context
- Extraction confidence scoring

Architecture Decision: Uses rule-based approach with regex patterns optimized
for South African business naming conventions, avoiding heavy ML dependencies
for this preprocessing step.

Integration: Feeds extracted names to Developer B's classification system.
"""

class NameExtractor:
    def extract_personal_names(self, company_name: str) -> List[PersonalName]
    def is_personal_name_pattern(self, token: str) -> bool
    def generate_phonetic_key(self, name: str) -> str
    def calculate_extraction_confidence(self, name: str, context: str) -> float
```

**C. Company Search Engine (`search.py`)**
```python
"""Advanced company search and matching system.

This module provides fuzzy search capabilities for matching lead company names
against the CIPC registry, implementing the multi-step validation approach
from the research document.

Key Features:
- Fuzzy string matching with multiple algorithms
- Company name normalization and slug generation
- Provincial and industry-based filtering
- Homonym disambiguation
- Search result ranking and confidence scoring

Architecture Decision: Combines PostgreSQL full-text search with Python-based
fuzzy matching (rapidfuzz) for optimal performance and accuracy balance.

Integration: Used by lead enrichment pipeline to validate company existence.
"""

class CompanySearchEngine:
    async def search_companies(self, query: str, filters: SearchFilters) -> SearchResults
    async def fuzzy_match_company(self, name: str, threshold: float = 0.8) -> List[CompanyMatch]
    def normalize_company_name(self, name: str) -> str
    def disambiguate_matches(self, matches: List[CompanyMatch]) -> CompanyMatch
```

#### 2. Caching System (`src/leadscout/cache/`)

**Required Files Structure:**
```
src/leadscout/cache/
├── __init__.py          # Cache exports and factory
├── redis_cache.py       # Hot cache implementation
├── postgres_cache.py    # Persistent cache
├── cache_manager.py     # Multi-tier coordination
├── models.py            # Cache data models
└── exceptions.py        # Cache-specific exceptions
```

**Key Components to Implement:**

**A. Redis Hot Cache (`redis_cache.py`)**
```python
"""High-performance Redis cache for frequently accessed data.

This module implements the hot cache layer using Redis for ultra-fast
access to recently used name classifications and company search results.
Designed for sub-millisecond response times on cache hits.

Key Features:
- TTL-based automatic expiration
- Atomic operations for thread safety
- Pipeline operations for batch caching
- Memory usage monitoring and optimization
- Connection pooling for high concurrency

Architecture Decision: Uses Redis with JSON serialization for complex
objects while maintaining backward compatibility with simple string caching.

Integration: First layer checked by cache_manager.py before hitting PostgreSQL.
"""

class RedisCache:
    async def get_classification(self, name_hash: str) -> Optional[Classification]
    async def set_classification(self, name_hash: str, classification: Classification, ttl: int) -> None
    async def get_company_data(self, company_hash: str) -> Optional[CompanyData]
    async def batch_get(self, keys: List[str]) -> Dict[str, Any]
    async def invalidate_pattern(self, pattern: str) -> int
```

**B. PostgreSQL Persistent Cache (`postgres_cache.py`)**
```python
"""Persistent cache and master data storage using PostgreSQL.

This module manages the persistent storage layer for all cached data,
implementing the database schema from the updated system design.
Handles long-term storage, complex queries, and data analytics.

Key Features:
- Full database schema implementation
- Complex query optimization
- Data migration and versioning
- Batch operations for bulk data
- Analytics queries for performance monitoring

Architecture Decision: Uses SQLAlchemy async for ORM with raw SQL for
performance-critical queries, following the hybrid approach for optimal
development speed and runtime performance.

Integration: Backing store for all cached data, primary integration point
with Developer B's classification results.
"""

class PostgresCache:
    async def store_classification(self, classification: Classification) -> None
    async def get_classification_by_name(self, name: str) -> Optional[Classification]
    async def store_cipc_company(self, company: CIPCCompany) -> None
    async def search_companies(self, query: str) -> List[CompanyData]
    async def get_cache_statistics(self) -> CacheStats
```

#### 3. Database Schema Implementation

**Required Schema (implement in migration files):**
```sql
-- Name classifications (shared with Developer B)
CREATE TABLE name_classifications (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    phonetic_key TEXT NOT NULL,
    ethnicity VARCHAR(20) NOT NULL,
    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    method VARCHAR(20) NOT NULL,
    sources TEXT[], -- JSON array of source systems
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name, ethnicity) -- Allow multiple ethnicities per name with different confidences
);

-- CIPC company registry data
CREATE TABLE cipc_companies (
    id SERIAL PRIMARY KEY,
    registration_number VARCHAR(20) UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    company_type VARCHAR(50),
    status VARCHAR(20),
    extracted_names TEXT[], -- JSON array of personal names found
    download_batch DATE NOT NULL, -- Which monthly batch this came from
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Lead enrichment cache
CREATE TABLE lead_enrichments (
    id SERIAL PRIMARY KEY,
    lead_hash VARCHAR(64) UNIQUE NOT NULL,
    original_data JSONB NOT NULL,
    enrichment_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    processing_time_ms INTEGER
);

-- Performance indexes
CREATE INDEX idx_name_classifications_name ON name_classifications(name);
CREATE INDEX idx_name_classifications_phonetic ON name_classifications(phonetic_key);
CREATE INDEX idx_cipc_companies_name ON cipc_companies USING GIN(to_tsvector('english', company_name));
CREATE INDEX idx_lead_enrichments_hash ON lead_enrichments(lead_hash);
CREATE INDEX idx_lead_enrichments_expires ON lead_enrichments(expires_at);
```

## APIs You Must Provide (for Developer B)

### 1. Name Classification Cache API
```python
@dataclass
class CacheRequest:
    name: str
    search_similar: bool = False
    similarity_threshold: float = 0.8

@dataclass
class CacheResponse:
    name: str
    classification: Optional[Classification]
    similar_matches: List[Classification]
    cache_hit: bool
    response_time_ms: int
```

### 2. Company Search API  
```python
@dataclass
class CompanySearchRequest:
    company_name: str
    province: Optional[str] = None
    exact_match: bool = False
    include_inactive: bool = False

@dataclass
class CompanySearchResponse:
    query: str
    matches: List[CompanyMatch]
    total_results: int
    search_confidence: float
    processing_time_ms: int
```

## Implementation Priority Order

### Phase 1: Foundation (Week 1)
1. **Database Schema**: Create all tables and indexes
2. **CIPC Models**: Data models for company and name data
3. **Basic Cache**: Simple Redis and PostgreSQL cache implementations
4. **Download System**: Single CSV file download with validation

### Phase 2: Core Systems (Week 2)  
1. **Batch Downloader**: All 26 CSV files with parallel processing
2. **Name Extraction**: Company name parsing and personal name identification
3. **Cache Manager**: Multi-tier cache coordination
4. **Basic Search**: Simple company name matching

### Phase 3: Advanced Features (Week 3)
1. **Fuzzy Search**: Advanced company matching with multiple algorithms
2. **Performance Optimization**: Query optimization and caching strategies
3. **Monitoring**: Cache hit rates, performance metrics, error tracking
4. **Integration APIs**: Final API contracts for Developer B

### Phase 4: Production Ready (Week 4)
1. **Error Recovery**: Robust error handling and retry mechanisms
2. **Monitoring Dashboard**: Cache statistics and system health
3. **Documentation**: API documentation and usage examples
4. **Performance Testing**: Load testing and optimization

## Quality Requirements

### Performance Targets
- **Name Cache Lookup**: <10ms average response time
- **Company Search**: <200ms for fuzzy matching  
- **Batch CSV Processing**: Process all 26 files within 30 minutes
- **Cache Hit Rate**: >80% for name classifications
- **Database Storage**: Efficient storage for 2M+ company records

### Testing Requirements
- **Unit Tests**: 80%+ coverage for all modules
- **Integration Tests**: Database operations and API contracts
- **Performance Tests**: Load testing with realistic data volumes
- **Error Scenarios**: Network failures, malformed data, cache misses

### Monitoring & Observability
- **Structured Logging**: All operations with correlation IDs
- **Metrics Collection**: Cache hit rates, response times, error rates
- **Health Checks**: Database connectivity, Redis availability, disk space
- **Alert Thresholds**: Performance degradation and error rate spikes

## Integration with Developer B

### Coordination Points
1. **Shared Models**: Use common Pydantic models for data exchange
2. **API Contracts**: Maintain backward compatibility for all endpoints
3. **Test Data**: Provide realistic test datasets for classification testing
4. **Performance SLAs**: Meet agreed response time targets for cache operations

### Communication Protocol
1. **Update `PROJECT_PLAN.md`** when you complete each task
2. **Mark tasks as completed** with detailed commit messages
3. **Document any API changes** in the integration documentation
4. **Notify Project Manager** when your phase is complete for verification

## Completion Criteria

### Definition of Done
- [ ] All database tables created with proper indexes
- [ ] CIPC CSV download system fully automated
- [ ] Name extraction working with SA business naming patterns
- [ ] Multi-tier caching system operational
- [ ] Company search engine with fuzzy matching
- [ ] APIs documented and tested
- [ ] Performance targets met
- [ ] Error handling comprehensive
- [ ] Monitoring and logging implemented
- [ ] Integration tests passing

### Deliverables
1. **Working Code**: All modules implemented according to architecture
2. **Database Schema**: Complete PostgreSQL schema with migrations
3. **API Documentation**: Clear documentation for all Developer B integrations
4. **Test Suite**: Comprehensive test coverage with realistic scenarios
5. **Performance Report**: Benchmarks showing target achievement
6. **Integration Guide**: Instructions for Developer B integration

**IMPORTANT**: You are building the foundational data infrastructure that Developer B's classification system depends on. Focus on performance, reliability, and clean APIs. The entire system's success depends on your caching and data layer performance.

## Getting Started

1. **Set up your development environment**:
   ```bash
   source .venv/bin/activate
   poetry install
   ```

2. **Create your module structure**:
   ```bash
   mkdir -p src/leadscout/cipc src/leadscout/cache
   ```

3. **Start with the database schema** - this is critical for Developer B integration

4. **Implement basic caching** - Developer B needs this immediately for testing

5. **Build the CIPC downloader** - start with single file, then expand to batch

Remember: Follow all rules in CLAUDE_RULES.md and maintain the highest code quality standards. The Project Manager will verify your work before integration.