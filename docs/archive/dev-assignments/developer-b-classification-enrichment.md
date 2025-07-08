# Developer B: Name Classification & Enrichment Pipeline

## Developer Assignment
**Role**: AI Classification & Enrichment Specialist  
**Primary Responsibility**: Build the intelligent name classification system and comprehensive lead enrichment pipeline using multi-layered AI approaches.

## CRITICAL: Read These Files First
1. **CLAUDE.md** - Complete project context and standards
2. **CLAUDE_RULES.md** - Development rules and architecture decisions  
3. **docs/architecture/updated-system-design.md** - Your specific architecture requirements
4. **docs/architecture/ethnicity classification and cpiro data.md** - Research foundation and classification approach

## Your Specialization Scope

### Core Responsibilities
1. **Multi-Layered Name Classification**: Rule-based → Phonetic → LLM pipeline optimized for SA names
2. **Curated Dictionary System**: Build comprehensive ethnic name databases for South African context
3. **LLM Integration**: OpenAI/Claude integration with few-shot learning and cost optimization
4. **Enrichment Pipeline**: Website discovery, LinkedIn research, contact validation
5. **Scoring Engine**: Lead prioritization algorithm with configurable weights

### Integration Points with Developer A
- **Consumes**: Name caching APIs and company search functionality
- **Provides**: Classification results for caching and enrichment data
- **Shared**: Database tables for storing classification results

## Technical Requirements

### MANDATORY: Follow All Project Standards
- **Virtual Environment**: Always use `source .venv/bin/activate &&` for all commands
- **Type Hints**: Every function must have complete type annotations
- **Docstrings**: Comprehensive module and function documentation
- **Error Handling**: Use custom exception hierarchy from `core.exceptions`
- **Async Patterns**: All I/O operations must be async
- **Testing**: Minimum 80% code coverage with pytest

### Architecture Implementation

#### 1. Name Classification Module (`src/leadscout/classification/`)

**Required Files Structure:**
```
src/leadscout/classification/
├── __init__.py          # Module exports and main classifier
├── rules.py             # Rule-based classification engine
├── phonetic.py          # Phonetic matching algorithms
├── llm.py               # LLM integration with few-shot learning
├── dictionaries.py      # SA ethnic name databases
├── augmented.py         # Vector similarity and retrieval
├── models.py            # Classification data models
└── exceptions.py        # Classification-specific exceptions
```

**Key Components to Implement:**

**A. Rule-Based Classification Engine (`rules.py`)**
```python
"""Rule-based name classification using curated South African dictionaries.

This module implements the first layer of the classification pipeline using
carefully curated dictionaries of names categorized by ethnic groups common
in South Africa. Achieves 95% coverage target with high confidence.

Key Features:
- Curated dictionaries for African, Indian, Cape Malay, Coloured, White ethnic groups
- Priority logic for multi-word names (classify by least European element)
- Special heuristics for month-surnames (April, September, October → Coloured)
- Confidence scoring based on dictionary match strength
- Fast lookup with O(1) performance using hash tables

Architecture Decision: Uses rule-based approach for maximum speed and
transparency, avoiding ML complexity for the majority of classification cases.
Research shows this achieves 80-90% accuracy with proper dictionaries.

Integration: First layer in classification pipeline, feeds to phonetic matching
for unknown names.
"""

class RuleBasedClassifier:
    def load_dictionaries(self) -> Dict[EthnicityType, Set[str]]
    def classify_name(self, name: str) -> Optional[Classification]
    def classify_multi_word_name(self, name_parts: List[str]) -> Classification
    def apply_special_heuristics(self, name: str) -> Optional[EthnicityType]
    def calculate_rule_confidence(self, name: str, matches: List[str]) -> float
```

**B. Phonetic Matching System (`phonetic.py`)**
```python
"""Advanced phonetic matching for name classification.

This module implements multiple phonetic algorithms to match unknown names
against classified names in the cache. Uses the confidence scoring approach
from the research document with algorithm agreement weighting.

Key Features:
- Multiple algorithms: Soundex, Metaphone, Double Metaphone, NYSIIS, Jaro-Winkler
- Algorithm confidence weighting and agreement scoring
- South African linguistic pattern optimization
- Variant spelling detection and normalization
- Performance optimization with precomputed phonetic codes

Architecture Decision: Combines multiple algorithms with weighted confidence
scoring to handle the linguistic diversity of South African names effectively.
Academic research shows this approach achieves 85%+ accuracy.

Integration: Second layer in classification pipeline, uses Developer A's
cache to find phonetically similar names.
"""

class PhoneticClassifier:
    def generate_phonetic_codes(self, name: str) -> Dict[str, str]
    def find_phonetic_matches(self, name: str, threshold: float = 0.8) -> List[ClassificationMatch]
    def calculate_phonetic_confidence(self, matches: List[ClassificationMatch]) -> float
    def optimize_for_sa_linguistics(self, name: str) -> str
    async def classify_with_phonetics(self, name: str) -> Optional[Classification]
```

**C. LLM Integration with Few-Shot Learning (`llm.py`)**
```python
"""LLM-based classification with augmented retrieval and cost optimization.

This module implements the final layer of classification using Large Language
Models with sophisticated prompt engineering and few-shot learning. Includes
the augmented retrieval approach from research for 40%+ cost reduction.

Key Features:
- Multi-provider support (OpenAI GPT-4, Claude)
- Few-shot learning with nearest neighbor examples
- Batch processing for cost optimization (20-30 names per request)
- Vector similarity search for example selection
- Prompt engineering optimized for South African name patterns
- Fallback and retry logic with exponential backoff

Architecture Decision: Uses function calling with structured outputs for
reliable classification results. Implements augmented retrieval to improve
accuracy while reducing token costs significantly.

Integration: Final layer in classification pipeline, only called for names
that cannot be classified by rules or phonetic matching (~5% of cases).
"""

class LLMClassifier:
    async def classify_with_few_shot(self, name: str, examples: List[Classification]) -> Classification
    async def batch_classify(self, names: List[str]) -> List[Classification]
    def select_few_shot_examples(self, name: str, count: int = 10) -> List[Classification]
    def build_classification_prompt(self, name: str, examples: List[Classification]) -> str
    async def call_openai_function(self, prompt: str) -> Classification
    async def call_claude_function(self, prompt: str) -> Classification
```

**D. Curated Dictionary System (`dictionaries.py`)**
```python
"""Comprehensive South African name dictionaries for rule-based classification.

This module manages the curated dictionaries that form the foundation of the
rule-based classification system. Based on academic research and real-world
SA naming patterns for maximum accuracy.

Key Features:
- Comprehensive African name databases (Nguni, Sotho, Tswana, Venda)
- Indian subcontinental names (Tamil, Telugu, Hindi, Gujarati)
- Cape Malay historical naming patterns
- Coloured community names including month-surnames
- European/Afrikaans name patterns
- Dynamic dictionary updates and management
- Statistical analysis and coverage reporting

Architecture Decision: Stores dictionaries as structured data with metadata
including confidence weights, regional patterns, and historical context
for nuanced classification decisions.

Integration: Core data source for rules.py, updated through administrative
interface and community feedback.
"""

class NameDictionaries:
    def load_african_names(self) -> Dict[str, NameEntry]
    def load_indian_names(self) -> Dict[str, NameEntry]  
    def load_cape_malay_names(self) -> Dict[str, NameEntry]
    def load_coloured_names(self) -> Dict[str, NameEntry]
    def load_european_names(self) -> Dict[str, NameEntry]
    def get_name_metadata(self, name: str) -> Optional[NameMetadata]
    def update_dictionary(self, ethnicity: EthnicityType, names: List[NameEntry]) -> None
```

#### 2. Enrichment Pipeline (`src/leadscout/enrichment/`)

**Required Files Structure:**
```
src/leadscout/enrichment/
├── __init__.py          # Enrichment pipeline orchestrator
├── website.py           # Website discovery and validation
├── linkedin.py          # LinkedIn profile research
├── contact.py           # Contact validation and quality
├── base.py              # Base enrichment interface
├── models.py            # Enrichment data models
└── exceptions.py        # Enrichment-specific exceptions
```

**Key Components to Implement:**

**A. Website Discovery Engine (`website.py`)**
```python
"""Intelligent website discovery and validation for business leads.

This module discovers and validates company websites using multiple strategies
including domain pattern matching, search engine queries, and content analysis.
Implements quality scoring for business relevance and professional appearance.

Key Features:
- Domain pattern generation from company names
- Multiple discovery strategies (direct, search, social)
- SSL certificate validation and security scoring
- Content analysis for business relevance
- Professional appearance scoring
- Performance and accessibility metrics

Architecture Decision: Uses a multi-strategy approach with fallbacks to
maximize discovery rate while maintaining quality standards. Implements
async processing for high throughput.

Integration: Part of the enrichment pipeline, results cached by Developer A's
caching system for efficiency.
"""

class WebsiteDiscovery:
    async def discover_website(self, company_name: str, province: str) -> Optional[WebsiteInfo]
    async def validate_website(self, url: str) -> WebsiteValidation
    def generate_domain_patterns(self, company_name: str) -> List[str]
    async def search_engine_discovery(self, company_name: str) -> List[str]
    def score_website_quality(self, website_info: WebsiteInfo) -> float
```

**B. LinkedIn Research System (`linkedin.py`)**
```python
"""LinkedIn profile and company research with compliance focus.

This module researches directors and companies on LinkedIn while maintaining
strict compliance with LinkedIn's terms of service. Focuses on publicly
available information for business validation and network analysis.

Key Features:
- Director profile discovery using public search
- Company page validation and analysis
- Professional network and connection analysis
- Industry credibility assessment
- Strict compliance with LinkedIn ToS
- Rate limiting and respectful scraping

Architecture Decision: Uses conservative approach with rate limiting and
public API where possible to ensure long-term sustainability and compliance.
Implements quality scoring based on profile completeness and professional indicators.

Integration: Enrichment pipeline component, works with name classification
to target director research efforts effectively.
"""

class LinkedInResearch:
    async def research_director(self, director_name: str, company_name: str) -> Optional[LinkedInProfile]
    async def research_company(self, company_name: str) -> Optional[LinkedInCompany]
    def validate_profile_authenticity(self, profile: LinkedInProfile) -> bool
    def score_professional_credibility(self, profile: LinkedInProfile) -> float
    async def respect_rate_limits(self) -> None
```

**C. Contact Validation System (`contact.py`)**
```python
"""Comprehensive contact information validation and quality assessment.

This module validates email addresses, phone numbers, and other contact
information while providing quality scores for lead prioritization.
Implements both format validation and deliverability checking.

Key Features:
- Email format validation and deliverability checking
- South African phone number validation and reachability
- Contact completeness scoring
- Quality metrics for lead prioritization
- Batch validation for efficiency
- Privacy-compliant validation methods

Architecture Decision: Combines format validation with selective deliverability
testing to balance accuracy with cost and privacy concerns. Implements
configurable validation levels based on use case requirements.

Integration: Final stage of enrichment pipeline, contributes to overall
lead quality scoring for prioritization.
"""

class ContactValidator:
    async def validate_email(self, email: str, check_deliverable: bool = False) -> EmailValidation
    async def validate_phone(self, phone: str, check_reachable: bool = False) -> PhoneValidation
    def calculate_contact_quality_score(self, contacts: ContactInfo) -> float
    async def batch_validate_contacts(self, contacts: List[ContactInfo]) -> List[ContactValidation]
```

#### 3. Scoring Engine (`src/leadscout/scoring/`)

**Required Files Structure:**
```
src/leadscout/scoring/
├── __init__.py          # Scoring engine and factory
├── base.py              # Base scoring interface
├── default.py           # Default scoring implementation
├── configurable.py     # Weight-based configurable scorer
├── models.py            # Scoring data models
└── exceptions.py        # Scoring-specific exceptions
```

**Key Components to Implement:**

**A. Pluggable Scoring Engine (`base.py` & `configurable.py`)**
```python
"""Configurable lead scoring system with pluggable components.

This module implements the pluggable scoring architecture that allows
for different scoring strategies and weight configurations. Supports
the business requirement for prioritizing leads based on data richness
and demographic factors.

Key Features:
- Pluggable scoring component architecture
- Configurable weights for different data sources
- Composite scoring with normalization
- A/B testing support for scoring strategies
- Performance tracking and optimization
- Business rule integration

Architecture Decision: Uses strategy pattern with dependency injection
to allow runtime configuration of scoring algorithms while maintaining
clean interfaces and testability.

Integration: Consumes all enrichment data to produce final lead scores
for business prioritization.
"""

class ConfigurableScorer:
    def calculate_composite_score(self, enrichment_data: EnrichedLead) -> LeadScore
    def apply_business_rules(self, lead: Lead, score: LeadScore) -> LeadScore
    def normalize_scores(self, scores: List[float]) -> List[float]
    def configure_weights(self, weights: ScoringWeights) -> None
    def track_scoring_performance(self, lead_id: str, score: LeadScore) -> None
```

## APIs You Must Consume (from Developer A)

### 1. Name Classification Cache
```python
# Check cache for existing classification
cached_result = await cache_client.get_classification(name)

# Store classification result
await cache_client.store_classification(name, classification)

# Find similar names for few-shot examples
similar_names = await cache_client.find_similar_names(name, limit=10)
```

### 2. Company Search Integration
```python
# Search for company in CIPC data
company_matches = await company_search.search_companies(
    company_name=lead.entity_name,
    province=lead.registered_address_province
)
```

## Implementation Priority Order

### Phase 1: Classification Foundation (Week 1)
1. **Dictionary System**: Load and organize SA ethnic name dictionaries
2. **Rule-Based Engine**: Fast dictionary-based classification
3. **Basic Models**: Classification and ethnicity data models
4. **Cache Integration**: Basic integration with Developer A's cache

### Phase 2: Advanced Classification (Week 2)
1. **Phonetic Matching**: All 5 phonetic algorithms with confidence scoring
2. **LLM Integration**: OpenAI function calling with basic prompts
3. **Few-Shot Learning**: Vector similarity and example selection
4. **Pipeline Coordination**: Multi-layer classification workflow

### Phase 3: Enrichment Pipeline (Week 3)
1. **Website Discovery**: Domain pattern matching and validation
2. **LinkedIn Research**: Profile discovery with compliance
3. **Contact Validation**: Email/phone validation and quality scoring
4. **Pipeline Integration**: Complete enrichment workflow

### Phase 4: Scoring & Optimization (Week 4)
1. **Scoring Engine**: Pluggable scoring with configurable weights
2. **Performance Optimization**: Batch processing and caching strategies
3. **Quality Metrics**: Accuracy tracking and validation
4. **Production Readiness**: Error handling and monitoring

## Quality Requirements

### Performance Targets
- **Name Classification**: <100ms average (including cache check)
- **Rule-Based Classification**: <10ms for dictionary matches
- **Phonetic Matching**: <50ms for similar name search
- **LLM Classification**: <2s including few-shot retrieval
- **Full Enrichment Pipeline**: <30s per lead average

### Accuracy Targets
- **Overall Classification Accuracy**: >95% on validation dataset
- **Rule-Based Coverage**: >90% of common SA names
- **Phonetic Match Accuracy**: >85% for variant spellings
- **LLM Accuracy**: >95% with few-shot examples
- **Cache Hit Rate**: >80% for repeated names

### Testing Requirements
- **Classification Validation**: Test with known SA name datasets
- **Integration Tests**: End-to-end pipeline with real lead data
- **Performance Tests**: Load testing with batch processing
- **Accuracy Metrics**: Continuous validation against ground truth
- **Error Scenarios**: Malformed names, API failures, network issues

## Integration with Developer A

### Coordination Points
1. **Cache Interface**: Use Developer A's caching APIs for all classification storage
2. **Database Schema**: Contribute to shared name_classifications table design
3. **Company Data**: Integrate CIPC company search into enrichment pipeline
4. **Performance**: Meet SLA requirements for cache interaction

### Data Flow Dependencies
1. **Classification Results → Cache**: All classifications stored via Developer A's APIs
2. **Company Search → Enrichment**: Use CIPC data for company validation
3. **Batch Processing → Cache**: Efficient bulk operations for large datasets
4. **Monitoring → Analytics**: Performance data shared for system optimization

## Completion Criteria

### Definition of Done
- [ ] Multi-layer name classification system operational (Rule → Phonetic → LLM)
- [ ] SA ethnic dictionaries comprehensive and accurate
- [ ] LLM integration with few-shot learning optimized
- [ ] Complete enrichment pipeline (website, LinkedIn, contacts)
- [ ] Pluggable scoring engine with configurable weights
- [ ] Integration with Developer A's caching system
- [ ] Performance targets met for all components
- [ ] Accuracy validation with real SA datasets
- [ ] Error handling and monitoring comprehensive
- [ ] Documentation and examples complete

### Deliverables
1. **Classification System**: Production-ready multi-layer classifier
2. **Enrichment Pipeline**: Complete lead enrichment workflow
3. **Scoring Engine**: Configurable lead prioritization system
4. **Integration Tests**: Full pipeline testing with realistic data
5. **Performance Report**: Benchmarks showing accuracy and speed targets
6. **User Guide**: Documentation for configuration and customization

**IMPORTANT**: You are building the intelligent core of the system that directly impacts business outcomes. Focus on accuracy, performance, and business value. The classification quality determines lead prioritization effectiveness.

## Getting Started

1. **Set up your development environment**:
   ```bash
   source .venv/bin/activate
   poetry install
   ```

2. **Create your module structure**:
   ```bash
   mkdir -p src/leadscout/classification src/leadscout/enrichment src/leadscout/scoring
   ```

3. **Start with the dictionaries** - this is the foundation for rule-based classification

4. **Implement rule-based classification** - get 90%+ coverage before moving to complex systems

5. **Build phonetic matching** - bridge the gap between rules and LLM

6. **Add LLM integration** - for the remaining 5-10% of difficult cases

Remember: Follow all rules in CLAUDE_RULES.md and maintain the highest code quality standards. The Project Manager will verify your work before integration.

## Research Resources

### Academic Papers
- [The Importance of Being Ernest, Ekundayo, or Eswari](https://hdsr.mitpress.mit.edu/pub/wgss79vu) - Name-ethnicity classification research
- [Name-ethnicity classification from open sources](https://dl.acm.org/doi/10.1145/1557019.1557032) - Academic classification techniques

### South African Context
- [Know our heritage: Meet Mr September](https://www.iol.co.za/news/south-africa/western-cape/know-our-heritage-meet-mr-september-2070357) - Month-surname patterns
- [The so-called Coloured people of South Africa](https://onomajournal.org/wp-content/uploads/2021/08/Onoma-55-1.12-Neethling-final-web-August.pdf) - Naming patterns research

### External APIs (for reference)
- [NamSor](https://www.namsor.com/) - Name classification service for comparison
- [Forebears.io](https://forebears.io/surnames) - Global surname frequency and origin data

Use these resources to validate your classification approach and ensure cultural sensitivity in your implementation.