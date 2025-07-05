# LeadScout Updated System Design

## Overview

LeadScout is an AI-powered lead enrichment system optimized for South African business contexts. Based on extensive research into SA naming patterns and CIPC data integration, the system uses a multi-layered approach combining rule-based classification, phonetic matching, and LLM fallbacks.

## Key Architecture Insights

### From Research Document Analysis
1. **SA Name Classification is Highly Feasible**: Distinct naming patterns across ethnic groups achieve 80-90% accuracy
2. **CIPC Data is Readily Available**: Monthly CSV downloads provide comprehensive company registry
3. **Multi-Layered Approach Optimal**: Rule engine → Phonetic matching → LLM fallback minimizes costs
4. **Augmented Retrieval Critical**: Few-shot examples improve accuracy by 40%+ and reduce token costs

## System Components

### 1. CIPC Integration Layer (Developer A Responsibility)

#### Data Sources
- **Primary**: Monthly CIPC CSV files (26 files, one per letter)
- **URL Pattern**: `https://www.cipc.co.za/wp-content/uploads/<YYYY>/<MM>/List-<N>.csv`
- **Data Fields**: Company Name, Registration Number, Type, Status
- **Update Frequency**: Monthly (automated cron job)

#### ETL Pipeline
```
CIPC CSVs → Download → Extract Names → Deduplicate → Cache → Index
```

**Key Processing Steps:**
1. **Download Orchestrator**: Fetch all 26 CSV files monthly
2. **Name Extraction**: Parse company names for personal name tokens
   - Split on delimiters (`&`, `,`, `/`)
   - Keep segments with ≥2 capitalized words
   - Filter by vowel presence and name patterns
3. **Deduplication**: Phonetic key (Metaphone) + Levenshtein distance
4. **Storage**: PostgreSQL master table with indexing

#### Company Search Engine
- **Fuzzy Matching**: Company name explosion to minimal slugs
- **Multi-Step Validation**: Provincial footprint, industry keywords
- **Homonym Disambiguation**: Country code and TLD filtering
- **API Endpoint**: `/company/search?name=...&province=...`

### 2. Name Classification System (Developer B Responsibility)

#### Multi-Layered Classification Pipeline
```
Input Name → Exact Cache → Rule Engine → Phonetic Match → LLM Fallback → Cache Result
```

#### Layer 1: Rule-Based Classification (95% coverage target)
**Curated Dictionaries:**
- **African**: Nguni, Sotho, Tswana, Venda patterns
- **Indian**: Tamil, Telugu, Hindi, Gujarati surnames
- **Cape Malay**: Historical naming patterns
- **Coloured**: Month-surnames (April, September, October)
- **European/Afrikaans**: Dutch, German, English origins

**Priority Logic:** Classify by least European element in multi-word names

#### Layer 2: Phonetic Matching
**Algorithms (in priority order):**
1. **Soundex**: Basic phonetic similarity
2. **Metaphone**: Improved English phonetics
3. **Double Metaphone**: Multi-language support
4. **NYSIIS**: Name-optimized algorithm
5. **Jaro-Winkler**: String similarity for variants

**Confidence Scoring:**
- Multiple algorithm agreement: 90-95%
- Single algorithm + high similarity: 80-90%
- Fuzzy matches: 70-80%

#### Layer 3: LLM Integration
**Provider Strategy:**
- **Primary**: OpenAI GPT-4 with function calling
- **Fallback**: Claude for high-confidence validation
- **Batch Processing**: 20-30 names per request

**Augmented Retrieval:**
- Embed incoming name using text-embedding-3-small
- Retrieve 10 nearest neighbors from cache
- Include as few-shot examples in prompt
- Expected improvement: 40%+ accuracy, 40%+ cost reduction

**Function Schema:**
```json
{
  "name": "classify_sa_name",
  "arguments": {
    "full_name": "string",
    "context_examples": "array"
  },
  "returns": {
    "ethnicity": "african|indian|coloured|white|mixed|unknown",
    "confidence": "float 0-1",
    "reasoning": "string"
  }
}
```

### 3. Enrichment Pipeline (Developer B Responsibility)

#### Website Discovery
- **Domain Pattern Matching**: Company name → likely domains
- **Validation**: SSL checks, response analysis, content relevance
- **Quality Scoring**: Website presence, professional appearance, business relevance

#### LinkedIn Research
- **Profile Search**: Director names → LinkedIn profiles
- **Company Pages**: Business presence validation
- **Professional Networks**: Industry connections and credibility
- **Compliance**: Terms of service adherence

#### Contact Validation
- **Email**: Format validation, deliverability checks
- **Phone**: SA number format validation, reachability testing
- **Quality Metrics**: Contact completeness and reliability scores

### 4. Caching & Storage Architecture (Developer A Responsibility)

#### Multi-Tier Caching Strategy
```
Redis (Hot Cache) ↔ PostgreSQL (Persistent) ↔ FAISS (Similarity Search)
```

**Redis Layer:**
- Recent LLM classifications (1 hour TTL)
- Active company searches (30 minutes TTL)
- Session-based enrichment results

**PostgreSQL Schema:**
```sql
-- Master name classification table
CREATE TABLE name_classifications (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    phonetic_key TEXT NOT NULL,
    ethnicity VARCHAR(20) NOT NULL,
    confidence REAL NOT NULL,
    method VARCHAR(20) NOT NULL,
    sources TEXT[], -- JSON array of source systems
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- CIPC company data
CREATE TABLE cipc_companies (
    id SERIAL PRIMARY KEY,
    registration_number VARCHAR(20) UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    company_type VARCHAR(50),
    status VARCHAR(20),
    extracted_names TEXT[], -- JSON array of personal names
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Enrichment cache
CREATE TABLE lead_enrichments (
    id SERIAL PRIMARY KEY,
    lead_hash VARCHAR(64) UNIQUE NOT NULL,
    original_data JSONB NOT NULL,
    enrichment_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);
```

**FAISS Integration:**
- Vector embeddings for name similarity search
- K-nearest neighbor retrieval for few-shot examples
- Periodic reindexing for optimal performance

#### Performance Targets
- **Name Classification**: <100ms average (with cache)
- **Company Search**: <200ms average
- **Batch Processing**: 100+ leads per minute
- **Cache Hit Rate**: >80% for name classifications
- **LLM Usage**: <5% of total classifications

## Component Interaction Flow

### 1. Lead Enrichment Workflow
```
Excel Input → Lead Validation → Parallel Enrichment → Scoring → Excel Output
                                       ↓
                    ┌─────────────────────────────────┐
                    │ Company CIPC Search            │
                    │ Name Classification            │
                    │ Website Discovery              │
                    │ LinkedIn Research              │
                    │ Contact Validation             │
                    └─────────────────────────────────┘
                                       ↓
                              Cache Results → Score Calculation
```

### 2. Name Classification Flow
```
Name Input → Cache Check → Rule Engine → Phonetic Match → LLM Call → Cache Store
     ↓            ↓              ↓              ↓            ↓           ↓
   Instant    Instant       Fast(<10ms)   Medium(~50ms)  Slow(~2s)  Store
```

### 3. CIPC Integration Flow
```
Monthly Cron → Download CSVs → ETL Processing → Update Database → Index Refresh
     ↓               ↓              ↓               ↓              ↓
 Scheduled      26 Files     Extract Names    PostgreSQL      Search Ready
```

## Inter-Module APIs

### 1. Name Classification API
```python
@dataclass
class ClassificationRequest:
    name: str
    context_examples: Optional[List[str]] = None

@dataclass  
class ClassificationResponse:
    name: str
    ethnicity: EthnicityType
    confidence: float
    method: str
    processing_time_ms: int
```

### 2. CIPC Search API
```python
@dataclass
class CompanySearchRequest:
    company_name: str
    province: Optional[str] = None
    exact_match: bool = False

@dataclass
class CompanySearchResponse:
    matches: List[CompanyMatch]
    total_results: int
    search_time_ms: int
```

### 3. Cache Interface
```python
class EnrichmentCache:
    async def get_classification(self, name: str) -> Optional[Classification]
    async def store_classification(self, name: str, result: Classification) -> None
    async def get_company_data(self, name: str) -> Optional[CompanyData]
    async def store_enrichment(self, lead_hash: str, data: EnrichmentData) -> None
```

## Development Coordination Points

### Shared Dependencies
1. **Data Models**: Both teams use common Pydantic models
2. **Configuration**: Shared settings for database, cache, API keys
3. **Error Handling**: Common exception hierarchy
4. **Logging**: Structured logging with correlation IDs

### Integration Testing
1. **Mock APIs**: Both teams provide mock implementations
2. **Test Data**: Shared test datasets for consistent validation
3. **Performance Benchmarks**: Agreed SLA targets for each component
4. **End-to-End Tests**: Combined pipeline testing with real data samples

### Deployment Dependencies
1. **Database Schema**: Developer A creates, Developer B uses classification tables
2. **Cache Infrastructure**: Developer A implements, Developer B consumes
3. **API Contracts**: Versioned APIs with backward compatibility
4. **Configuration**: Environment-specific settings for each component

This architecture enables parallel development while maintaining clear interfaces and shared responsibilities.