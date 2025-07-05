# LeadScout System Architecture

## Overview

LeadScout is designed as a modular, scalable system for processing and enriching business lead data. The architecture emphasizes performance, reliability, and extensibility while maintaining clean separation of concerns.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Input Layer   │───▶│ Processing Core │───▶│  Output Layer   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Data Sources  │    │   Cache Layer   │    │   Reporting     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## System Components

### 1. Input Layer
- **Excel Reader**: Pandas-based XLSX file processing
- **Data Validation**: Pydantic models for input validation
- **Batch Processing**: Configurable batch sizes for large files
- **Error Handling**: Graceful handling of malformed input

### 2. Processing Core
- **Pipeline Engine**: Orchestrates the enrichment workflow
- **Async Task Manager**: Manages concurrent API calls
- **State Management**: Tracks processing progress and failures
- **Configuration Manager**: Handles settings and API keys

### 3. Enrichment Modules
- **CIPC Lookup**: South African company registry integration
- **Website Discovery**: Intelligent website detection
- **LinkedIn Research**: Professional profile investigation
- **Contact Validation**: Phone/email verification

### 4. Classification System
- **Name Classifier**: Multi-layered ethnicity classification
- **Phonetic Engine**: Soundex, Metaphone, and custom algorithms
- **LLM Interface**: OpenAI/Claude integration for unknown names
- **Cache Integration**: Intelligent result caching

### 5. Scoring Engine
- **Pluggable Scorers**: Modular scoring components
- **Weight Configuration**: Configurable scoring weights
- **Composite Scoring**: Combines multiple score types
- **Ranking System**: Final priority calculation

### 6. Cache Layer
- **SQLite Database**: Persistent result caching
- **TTL Management**: Configurable cache expiration
- **Query Optimization**: Efficient data retrieval
- **Cleanup Automation**: Automatic cache maintenance

### 7. Output Layer
- **Excel Writer**: Enhanced XLSX generation
- **Report Generation**: Processing summaries and statistics
- **Progress Tracking**: Real-time processing updates
- **Error Reporting**: Detailed failure analysis

## Data Flow

### 1. Input Processing
```
Excel File → Data Validation → Batch Creation → Queue Management
```

### 2. Enrichment Pipeline
```
Lead Data → Cache Check → API Calls → Data Consolidation → Scoring
```

### 3. Classification Flow
```
Name → Exact Match → Phonetic Match → LLM Classification → Cache Update
```

### 4. Output Generation
```
Enriched Data → Score Calculation → Ranking → Excel Export
```

## Key Design Patterns

### 1. Plugin Architecture
- **Modular Enrichment**: Each data source as a separate module
- **Pluggable Scoring**: Custom scoring algorithms
- **Extensible Classification**: New classification methods
- **Configurable Pipeline**: Dynamic workflow composition

### 2. Async Processing
- **Concurrent API Calls**: Multiple requests in parallel
- **Non-blocking Operations**: Maintains UI responsiveness
- **Resource Management**: Configurable concurrency limits
- **Error Isolation**: Failures don't block other operations

### 3. Caching Strategy
- **Multi-level Caching**: In-memory and persistent caches
- **Smart Invalidation**: TTL-based cache expiration
- **Preemptive Loading**: Cache warming for common queries
- **Efficient Storage**: Normalized data structures

### 4. Configuration Management
- **Environment Variables**: Secure API key storage
- **Configuration Files**: Non-sensitive settings
- **Runtime Configuration**: Dynamic setting updates
- **Validation**: Configuration schema validation

## Performance Considerations

### 1. Scalability
- **Horizontal Scaling**: Multiple processing instances
- **Vertical Scaling**: Efficient resource utilization
- **Load Balancing**: Distributes processing load
- **Memory Management**: Optimized data structures

### 2. Optimization
- **Batch Processing**: Reduces API overhead
- **Connection Pooling**: Efficient HTTP connections
- **Data Streaming**: Handles large files efficiently
- **Query Optimization**: Efficient database queries

### 3. Reliability
- **Retry Logic**: Exponential backoff for failures
- **Circuit Breakers**: Prevents cascade failures
- **Graceful Degradation**: Partial results on failures
- **State Persistence**: Resumable processing

## Security Architecture

### 1. API Security
- **Key Management**: Secure credential storage
- **Rate Limiting**: Prevents API abuse
- **Error Handling**: Secure error messages
- **Audit Logging**: Complete access tracking

### 2. Data Protection
- **Encryption**: Sensitive data encryption
- **Access Control**: Role-based permissions
- **Data Minimization**: Only necessary data storage
- **Retention Policies**: Configurable data cleanup

### 3. Privacy Compliance
- **POPIA Compliance**: South African privacy laws
- **Data Anonymization**: Optional PII removal
- **Consent Management**: Respects user preferences
- **Audit Trail**: Complete processing history

## Database Schema

### 1. Cache Tables
```sql
-- Main cache table
CREATE TABLE lead_cache (
    id INTEGER PRIMARY KEY,
    lead_hash TEXT UNIQUE,
    entity_name TEXT,
    data_json TEXT,
    created_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- Name classification cache
CREATE TABLE name_classifications (
    id INTEGER PRIMARY KEY,
    name_hash TEXT UNIQUE,
    original_name TEXT,
    ethnicity TEXT,
    confidence REAL,
    method TEXT,
    created_at TIMESTAMP
);

-- Phonetic variants
CREATE TABLE phonetic_variants (
    id INTEGER PRIMARY KEY,
    name_id INTEGER,
    algorithm TEXT,
    phonetic_code TEXT,
    FOREIGN KEY (name_id) REFERENCES name_classifications(id)
);
```

### 2. Processing State
```sql
-- Processing jobs
CREATE TABLE processing_jobs (
    id INTEGER PRIMARY KEY,
    file_name TEXT,
    total_leads INTEGER,
    processed_leads INTEGER,
    status TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Processing errors
CREATE TABLE processing_errors (
    id INTEGER PRIMARY KEY,
    job_id INTEGER,
    lead_index INTEGER,
    error_type TEXT,
    error_message TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES processing_jobs(id)
);
```

## API Integration Architecture

### 1. HTTP Client Layer
- **httpx**: Async HTTP client with connection pooling
- **Retry Logic**: Exponential backoff for transient failures
- **Timeout Management**: Configurable request timeouts
- **Error Handling**: Comprehensive error classification

### 2. Rate Limiting
- **Token Bucket**: Configurable rate limiting per service
- **Backoff Strategies**: Adaptive rate limiting
- **Priority Queues**: Prioritize important requests
- **Monitoring**: Rate limit usage tracking

### 3. Data Transformation
- **Response Parsers**: Service-specific data extraction
- **Data Normalizers**: Consistent data formatting
- **Validation**: Response data validation
- **Enrichment**: Data enhancement and cleanup

## Testing Strategy

### 1. Unit Testing
- **Component Tests**: Individual module testing
- **Mock Services**: External API mocking
- **Edge Cases**: Boundary condition testing
- **Performance Tests**: Component performance validation

### 2. Integration Testing
- **API Integration**: Real service integration tests
- **Database Tests**: SQLite integration testing
- **Pipeline Tests**: End-to-end workflow testing
- **Error Scenarios**: Failure mode testing

### 3. Load Testing
- **Stress Tests**: High-volume processing tests
- **Concurrency Tests**: Parallel processing validation
- **Memory Tests**: Memory usage optimization
- **API Limits**: Service limit testing

## Monitoring and Observability

### 1. Metrics Collection
- **Processing Metrics**: Throughput, latency, errors
- **Cache Metrics**: Hit rates, storage usage
- **API Metrics**: Request rates, response times
- **System Metrics**: CPU, memory, disk usage

### 2. Logging
- **Structured Logging**: JSON-formatted logs
- **Correlation IDs**: Request tracking
- **Error Tracking**: Detailed error information
- **Audit Logs**: Security and compliance tracking

### 3. Health Checks
- **Service Health**: API availability monitoring
- **Database Health**: Cache system monitoring
- **Resource Health**: System resource monitoring
- **Alert System**: Proactive issue notification

## Deployment Architecture

### 1. Environment Management
- **Development**: Local development environment
- **Testing**: CI/CD testing environment
- **Production**: Containerized deployment
- **Configuration**: Environment-specific settings

### 2. Containerization
- **Docker**: Container-based deployment
- **Multi-stage Builds**: Optimized image sizes
- **Health Checks**: Container health monitoring
- **Resource Limits**: CPU and memory constraints

### 3. Orchestration
- **Docker Compose**: Local development orchestration
- **Kubernetes**: Production orchestration (future)
- **Service Discovery**: Dynamic service location
- **Load Balancing**: Traffic distribution

This architecture provides a solid foundation for the LeadScout system, emphasizing modularity, performance, and reliability while maintaining the flexibility to evolve as requirements change.