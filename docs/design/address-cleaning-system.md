# Address Cleaning & Canonicalization System Design

## 🎯 **Executive Summary**

Design for intelligent address cleaning system using multi-layered LLM classification pipeline, mirroring the successful name ethnicity classification approach. The system will canonicalize "dirty" South African addresses into standardized components for improved spatial ethnicity prediction and data quality.

## 📋 **Background & Context**

### **Problem Statement**
South African address data is notoriously inconsistent:
- **Misspellings**: "Sandton" → "Sandtom", "Johannesburg" → "Joburg"/"JHB" 
- **Abbreviations**: "Rd"/"Road", "St"/"Street", "Ave"/"Avenue"
- **Missing Components**: "Sandton" vs "Sandton, Johannesburg, Gauteng"
- **Format Variations**: "123 Main St, Sandton 2196" vs "123 Main Street, Sandton, Johannesburg"
- **Historical Changes**: "Port Elizabeth" → "Gqeberha", regional name updates
- **Language Variants**: "Cape Town"/"Kaapstad", "Durban"/"eThekwini"

### **Business Impact**
- **Poor Ethnicity Prediction**: Inconsistent suburbs reduce spatial correlation accuracy
- **Data Quality Issues**: Inconsistent addresses affect lead scoring and routing
- **Manual Cleanup Costs**: Sales teams waste time correcting addresses
- **Integration Problems**: CRM systems can't match addresses effectively

### **Success Vision**
Transform inconsistent address data into canonical, standardized components that enable:
- **Accurate Suburb-Level Ethnicity Prediction**: Clean suburbs improve demographic analysis
- **Consistent Data Quality**: Standardized addresses across all systems
- **Automated Cleanup**: Zero manual intervention for common address variations
- **Learning Intelligence**: System improves accuracy over time through LLM learning

## 🏗️ **System Architecture**

### **Multi-Layered Address Classification Pipeline**

```
Raw Address Input → Rule-Based → Fuzzy Matching → Gazetteer Lookup → LLM Classification → Learning Database
                     ↓             ↓                ↓                  ↓                    ↓
                   Common          Typo            Canonical          Complex              Pattern
                   Patterns        Correction      Lookup             Analysis             Storage
```

### **Processing Flow**
1. **Input**: `"123 Main St, Sandtom, JHB, GP 2196"`
2. **Rule-Based**: Extract postal code, expand abbreviations → `"123 Main Street, Sandtom, Johannesburg, Gauteng 2196"`
3. **Fuzzy Matching**: Correct typos → `"123 Main Street, Sandton, Johannesburg, Gauteng 2196"`
4. **Gazetteer Lookup**: Validate against canonical places → `"Sandton, Johannesburg, Gauteng"`
5. **LLM Classification**: Handle complex cases and validate final canonicalization
6. **Learning Database**: Store successful patterns for future use

## 📊 **Database Schema Design**

### **Core Address Tables**

```sql
-- Address classification results (equivalent to lead_processing_results)
CREATE TABLE address_classifications (
    classification_id TEXT PRIMARY KEY,
    raw_address TEXT NOT NULL,
    raw_city TEXT,
    raw_province TEXT,
    
    -- Canonical components
    street_number TEXT,
    street_name TEXT,
    suburb TEXT,
    city TEXT,
    province TEXT,
    postal_code TEXT,
    
    -- Classification metadata
    classification_method TEXT, -- rule_based|fuzzy|gazetteer|llm|cache
    confidence_score REAL,
    corrections_made JSON,       -- Array of corrections applied
    
    -- Source tracking
    source_job_id TEXT,
    source_row_number INTEGER,
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Performance tracking
    processing_time_ms REAL,
    api_cost REAL DEFAULT 0.0,
    api_provider TEXT,
    
    FOREIGN KEY (source_job_id) REFERENCES job_executions(job_id)
);

-- Learned address patterns (equivalent to learned_patterns)
CREATE TABLE address_canonicalization_patterns (
    pattern_id TEXT PRIMARY KEY,
    raw_pattern TEXT,             -- Pattern in raw address
    canonical_replacement TEXT,   -- Canonical form
    pattern_type TEXT,            -- abbreviation|misspelling|alternative|format
    component_type TEXT,          -- street|suburb|city|province|postal
    confidence_score REAL,
    usage_count INTEGER DEFAULT 1,
    success_rate REAL DEFAULT 1.0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_from_job_id TEXT,
    is_active BOOLEAN DEFAULT true
);

-- Enhanced places gazetteer
CREATE TABLE places_gazetteer (
    place_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    place_type TEXT NOT NULL,    -- suburb|city|province|postal_area
    parent_place_id TEXT,        -- Hierarchical structure
    
    -- Alternative names and spellings
    alternative_names JSON,      -- Common variations
    historical_names JSON,       -- Previous names (Port Elizabeth → Gqeberha)
    abbreviations JSON,          -- JHB, CT, DBN, etc.
    misspellings JSON,          -- Common typos
    
    -- Geographic context
    postal_codes JSON,          -- Associated postal codes
    coordinates TEXT,           -- Lat,lng for future geospatial features
    
    -- Metadata
    population_estimate INTEGER,
    ethnicity_profile JSON,     -- Demographic data for prediction
    data_source TEXT,           -- Census, PostNet, manual, etc.
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_place_id) REFERENCES places_gazetteer(place_id)
);

-- LLM address classifications cache (equivalent to llm_classifications)
CREATE TABLE llm_address_classifications (
    classification_id TEXT PRIMARY KEY,
    raw_address_hash TEXT NOT NULL, -- Hash for quick lookup
    raw_address TEXT NOT NULL,
    
    -- LLM response
    llm_response JSON,              -- Full LLM structured response
    canonical_components JSON,      -- Extracted address components
    confidence_score REAL,
    corrections_made JSON,
    
    -- LLM metadata
    llm_provider TEXT,              -- openai|anthropic
    llm_model TEXT,                 -- gpt-4|claude-3-haiku
    api_cost REAL,
    processing_time_ms REAL,
    
    -- Learning integration
    patterns_generated INTEGER DEFAULT 0,
    has_been_learned BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Address validation and correction tracking
CREATE TABLE address_validations (
    validation_id TEXT PRIMARY KEY,
    original_address TEXT NOT NULL,
    canonical_address TEXT NOT NULL,
    validation_method TEXT,         -- automated|manual|llm
    validated_by TEXT,             -- User/system identifier
    validation_notes TEXT,
    is_confirmed BOOLEAN DEFAULT false,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_address_classifications_raw ON address_classifications(raw_address);
CREATE INDEX idx_address_patterns_raw ON address_canonicalization_patterns(raw_pattern);
CREATE INDEX idx_places_canonical ON places_gazetteer(canonical_name, place_type);
CREATE INDEX idx_places_alternatives ON places_gazetteer(alternative_names);
CREATE INDEX idx_llm_address_hash ON llm_address_classifications(raw_address_hash);
```

### **Integration with Existing Schema**

```sql
-- Enhance existing lead_processing_results table
ALTER TABLE lead_processing_results ADD COLUMN address_classification_id TEXT;
ALTER TABLE lead_processing_results ADD COLUMN canonical_street_address TEXT;
ALTER TABLE lead_processing_results ADD COLUMN canonical_suburb TEXT;
ALTER TABLE lead_processing_results ADD COLUMN canonical_city TEXT;
ALTER TABLE lead_processing_results ADD COLUMN canonical_province TEXT;
ALTER TABLE lead_processing_results ADD COLUMN canonical_postal_code TEXT;
ALTER TABLE lead_processing_results ADD COLUMN address_confidence_score REAL;

-- Link to address classifications
ALTER TABLE lead_processing_results 
ADD FOREIGN KEY (address_classification_id) REFERENCES address_classifications(classification_id);

-- Enhance ethnicity confirmations with canonical addresses
ALTER TABLE ethnicity_confirmations ADD COLUMN canonical_suburb TEXT;
ALTER TABLE ethnicity_confirmations ADD COLUMN canonical_city TEXT;
ALTER TABLE ethnicity_confirmations ADD COLUMN canonical_province TEXT;
```

## 🧠 **LLM Address Classification System**

### **LLM Prompt Engineering**

```python
def create_address_classification_prompt(raw_address, city=None, province=None):
    """Create structured prompt for LLM address classification."""
    
    context = f"""
You are an expert in South African address standardization. Your task is to parse and canonicalize the given address into standard components.

RULES:
1. Use official place names (e.g., "Johannesburg" not "Joburg" or "JHB")
2. Expand abbreviations (e.g., "St" → "Street", "Rd" → "Road")
3. Correct common misspellings
4. Use current official names (e.g., "Gqeberha" not "Port Elizabeth")
5. Standardize province names to full forms

SOUTH AFRICAN CONTEXT:
- Major cities: Johannesburg, Cape Town, Durban, Pretoria, Port Elizabeth (now Gqeberha)
- Provinces: Gauteng, Western Cape, KwaZulu-Natal, Eastern Cape, Free State, Limpopo, Mpumalanga, Northern Cape, North West
- Common abbreviations: JHB→Johannesburg, CT→Cape Town, DBN→Durban, PTA→Pretoria, GP→Gauteng, WC→Western Cape

ADDRESS TO PARSE: "{raw_address}"
ADDITIONAL CONTEXT: City="{city}", Province="{province}"

Respond with ONLY a JSON object in this exact format:
{{
    "street_number": "123 or null",
    "street_name": "Main Street or null", 
    "suburb": "Sandton or null",
    "city": "Johannesburg or null",
    "province": "Gauteng or null", 
    "postal_code": "2196 or null",
    "confidence": 0.95,
    "corrections_made": ["Sandtom → Sandton", "JHB → Johannesburg"],
    "reasoning": "Brief explanation of parsing decisions"
}}
"""
    
    return context.strip()
```

### **Address Classification Engine**

```python
class AddressClassificationEngine:
    """Multi-layered address classification system."""
    
    def __init__(self):
        self.rule_processor = RuleBasedAddressProcessor()
        self.fuzzy_matcher = FuzzyAddressMatcher()
        self.gazetteer = PlacesGazetteer()
        self.llm_classifier = LLMAddressClassifier()
        self.learning_db = AddressLearningDatabase()
    
    async def classify_address(self, raw_address, city=None, province=None):
        """Classify address through multi-layered pipeline."""
        
        start_time = time.time()
        classification_path = []
        
        # 1. Check cache first
        cached_result = self.learning_db.get_cached_classification(raw_address)
        if cached_result:
            classification_path.append("cache")
            return self._create_result(cached_result, classification_path, start_time)
        
        # 2. Rule-based processing
        rule_result = self.rule_processor.process(raw_address, city, province)
        if rule_result.confidence > 0.9:
            classification_path.append("rule_based")
            self.learning_db.store_classification(raw_address, rule_result)
            return self._create_result(rule_result, classification_path, start_time)
        
        # 3. Fuzzy matching
        fuzzy_result = self.fuzzy_matcher.match(rule_result.processed_address)
        if fuzzy_result.confidence > 0.8:
            classification_path.append("fuzzy_matching")
            self.learning_db.store_classification(raw_address, fuzzy_result)
            return self._create_result(fuzzy_result, classification_path, start_time)
        
        # 4. Gazetteer lookup
        gazetteer_result = self.gazetteer.lookup(fuzzy_result.processed_address)
        if gazetteer_result.confidence > 0.85:
            classification_path.append("gazetteer")
            self.learning_db.store_classification(raw_address, gazetteer_result)
            return self._create_result(gazetteer_result, classification_path, start_time)
        
        # 5. LLM classification (last resort)
        llm_result = await self.llm_classifier.classify(raw_address, city, province)
        classification_path.append("llm")
        
        # Store LLM result and learn patterns
        self.learning_db.store_llm_classification(raw_address, llm_result)
        await self.learning_db.extract_patterns(raw_address, llm_result)
        
        return self._create_result(llm_result, classification_path, start_time)
```

### **Rule-Based Address Processing**

```python
class RuleBasedAddressProcessor:
    """Handle common address patterns and abbreviations."""
    
    def __init__(self):
        self.abbreviation_map = {
            # Street types
            'st': 'Street', 'str': 'Street', 'street': 'Street',
            'rd': 'Road', 'road': 'Road',
            'ave': 'Avenue', 'avenue': 'Avenue', 'av': 'Avenue',
            'dr': 'Drive', 'drive': 'Drive',
            'cres': 'Crescent', 'crescent': 'Crescent',
            'pl': 'Place', 'place': 'Place',
            
            # City abbreviations
            'jhb': 'Johannesburg', 'joburg': 'Johannesburg',
            'ct': 'Cape Town', 'cpt': 'Cape Town',
            'dbn': 'Durban', 'durban': 'Durban',
            'pta': 'Pretoria', 'pretoria': 'Pretoria',
            'pe': 'Gqeberha', 'port elizabeth': 'Gqeberha',
            
            # Province abbreviations
            'gp': 'Gauteng', 'gauteng': 'Gauteng',
            'wc': 'Western Cape', 'western cape': 'Western Cape',
            'kzn': 'KwaZulu-Natal', 'kwazulu-natal': 'KwaZulu-Natal',
            'ec': 'Eastern Cape', 'eastern cape': 'Eastern Cape',
            'fs': 'Free State', 'free state': 'Free State',
            'lp': 'Limpopo', 'limpopo': 'Limpopo',
            'mp': 'Mpumalanga', 'mpumalanga': 'Mpumalanga',
            'nc': 'Northern Cape', 'northern cape': 'Northern Cape',
            'nw': 'North West', 'north west': 'North West',
        }
        
        self.postal_code_pattern = re.compile(r'\b\d{4}\b')
        self.street_number_pattern = re.compile(r'^\d+[a-z]?\s')
    
    def process(self, raw_address, city=None, province=None):
        """Apply rule-based processing to address."""
        
        processed = raw_address.lower().strip()
        corrections = []
        
        # Extract postal code
        postal_match = self.postal_code_pattern.search(processed)
        postal_code = postal_match.group() if postal_match else None
        if postal_code:
            processed = self.postal_code_pattern.sub('', processed).strip()
        
        # Extract street number
        street_number_match = self.street_number_pattern.match(processed)
        street_number = street_number_match.group().strip() if street_number_match else None
        if street_number:
            processed = self.street_number_pattern.sub('', processed).strip()
        
        # Apply abbreviation expansions
        words = processed.split()
        expanded_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in self.abbreviation_map:
                expanded = self.abbreviation_map[clean_word]
                expanded_words.append(expanded)
                corrections.append(f"{word} → {expanded}")
            else:
                expanded_words.append(word)
        
        # Parse components from expanded address
        components = self._parse_components(' '.join(expanded_words), city, province)
        
        return AddressClassificationResult(
            street_number=street_number,
            postal_code=postal_code,
            corrections_made=corrections,
            confidence=0.7,  # Rule-based confidence
            method="rule_based",
            **components
        )
```

### **Fuzzy Address Matching**

```python
class FuzzyAddressMatcher:
    """Handle typos and variations using fuzzy matching."""
    
    def __init__(self):
        self.known_places = self._load_known_places()
        self.similarity_threshold = 0.8
    
    def match(self, processed_address):
        """Apply fuzzy matching to correct typos."""
        
        components = self._split_address_components(processed_address)
        corrections = []
        matched_components = {}
        
        for component_type, value in components.items():
            if not value:
                continue
                
            # Find best fuzzy match
            candidates = self.known_places.get(component_type, [])
            best_match = self._find_best_match(value, candidates)
            
            if best_match and best_match['similarity'] > self.similarity_threshold:
                matched_components[component_type] = best_match['canonical']
                if best_match['canonical'] != value:
                    corrections.append(f"{value} → {best_match['canonical']}")
            else:
                matched_components[component_type] = value
        
        confidence = self._calculate_fuzzy_confidence(components, matched_components)
        
        return AddressClassificationResult(
            corrections_made=corrections,
            confidence=confidence,
            method="fuzzy_matching",
            **matched_components
        )
    
    def _find_best_match(self, input_value, candidates):
        """Find best fuzzy match using multiple algorithms."""
        from difflib import SequenceMatcher
        from fuzzywuzzy import fuzz
        
        best_match = None
        best_similarity = 0
        
        for candidate in candidates:
            # Use multiple similarity measures
            seq_similarity = SequenceMatcher(None, input_value, candidate['name']).ratio()
            fuzzy_similarity = fuzz.ratio(input_value, candidate['name']) / 100
            
            # Weighted average
            combined_similarity = (seq_similarity * 0.6) + (fuzzy_similarity * 0.4)
            
            if combined_similarity > best_similarity:
                best_similarity = combined_similarity
                best_match = {
                    'canonical': candidate['canonical_name'],
                    'similarity': combined_similarity
                }
        
        return best_match
```

## 🗺️ **Places Gazetteer System**

### **Gazetteer Population Strategy**

```python
class PlacesGazetteerBuilder:
    """Build comprehensive SA places database."""
    
    def __init__(self):
        self.data_sources = [
            StatsSAData(),      # Official census data
            PostNetData(),      # Postal service data
            MunicipalData(),    # Municipal boundaries
            CommercialData(),   # Business directories
        ]
    
    async def build_gazetteer(self):
        """Build comprehensive places database."""
        
        # 1. Load official data sources
        for source in self.data_sources:
            places_data = await source.extract_places()
            await self._import_places(places_data, source.name)
        
        # 2. Generate alternative names and misspellings
        await self._generate_alternatives()
        
        # 3. Build hierarchical relationships
        await self._build_hierarchy()
        
        # 4. Validate and clean data
        await self._validate_gazetteer()
    
    async def _generate_alternatives(self):
        """Generate common alternatives and misspellings."""
        
        # Language variants
        language_variants = {
            'Cape Town': ['Kaapstad'],
            'Durban': ['eThekwini'],
            'Johannesburg': ['Joburg', 'JHB', 'Egoli'],
            'Pretoria': ['Tshwane', 'PTA'],
        }
        
        # Common misspellings (can be learned from LLM corrections)
        common_misspellings = {
            'Sandton': ['Sandtom', 'Sandown', 'Sandon'],
            'Rosebank': ['Rosebank', 'Rose Bank'],
            'Randburg': ['Randburt', 'Randberg'],
        }
        
        # Update gazetteer with alternatives
        for canonical, alternatives in {**language_variants, **common_misspellings}.items():
            await self._add_alternatives(canonical, alternatives)
```

## 📝 **Integration with Ethnicity System**

### **Enhanced Spatial Ethnicity Prediction**

```python
def enhanced_ethnicity_prediction(name, canonical_address_components):
    """Improved ethnicity prediction using clean address data."""
    
    suburb = canonical_address_components.get('suburb')
    city = canonical_address_components.get('city')
    province = canonical_address_components.get('province')
    
    # Multi-level spatial lookup with clean data
    prediction_layers = [
        lookup_suburb_ethnicity_patterns(name, suburb),
        lookup_city_ethnicity_patterns(name, city),
        lookup_province_ethnicity_patterns(name, province),
        lookup_postal_area_patterns(name, canonical_address_components.get('postal_code'))
    ]
    
    # Weighted prediction combining all layers
    return calculate_weighted_ethnicity_prediction(prediction_layers)

def update_spatial_patterns_with_clean_addresses(confirmation):
    """Update spatial patterns using canonical address components."""
    
    # Update with clean suburb data
    update_suburb_ethnicity_pattern(
        name=confirmation.full_name,
        canonical_suburb=confirmation.canonical_suburb,
        canonical_city=confirmation.canonical_city,
        ethnicity=confirmation.confirmed_ethnicity
    )
    
    # Learn address → ethnicity correlations
    store_address_ethnicity_pattern(
        address_components=confirmation.canonical_address_components,
        ethnicity=confirmation.confirmed_ethnicity,
        confidence=1.0  # Human confirmed
    )
```

## 🎯 **Implementation Plan & Backlog**

### **Phase 1: Foundation (2-3 weeks)**
- [ ] **Database Schema**: Implement address classification tables
- [ ] **Rule-Based Processor**: Common abbreviations and patterns
- [ ] **Basic Gazetteer**: Load major cities and suburbs
- [ ] **CLI Integration**: `leadscout address clean` command
- [ ] **Export Enhancement**: Include canonical address columns

### **Phase 2: Intelligence (3-4 weeks)**
- [ ] **LLM Classification**: Implement address classification LLM pipeline
- [ ] **Fuzzy Matching**: Advanced typo correction system
- [ ] **Learning Database**: Pattern extraction and storage
- [ ] **Cache System**: Fast lookup for previously classified addresses
- [ ] **Performance Optimization**: Sub-100ms processing targets

### **Phase 3: Advanced Features (4-6 weeks)**
- [ ] **Comprehensive Gazetteer**: Full SA places database with alternatives
- [ ] **Spatial Intelligence**: Advanced ethnicity prediction with clean addresses
- [ ] **Validation System**: Manual confirmation and correction workflow
- [ ] **Analytics Dashboard**: Address quality metrics and improvement tracking
- [ ] **API Integration**: Real-time address validation services

### **Phase 4: Production Excellence (2-3 weeks)**
- [ ] **Performance Tuning**: Achieve <100ms average processing
- [ ] **Cost Optimization**: Reduce LLM usage to <5% through learning
- [ ] **Quality Assurance**: Comprehensive testing and validation
- [ ] **Documentation**: User guides and API documentation
- [ ] **Monitoring**: Address quality metrics and alerting

## ✅ **Success Criteria**

### **Technical Success Metrics**

1. **Accuracy Targets**
   - [ ] 95%+ correct suburb extraction from raw addresses
   - [ ] 98%+ correct city identification  
   - [ ] 90%+ correct street name standardization
   - [ ] 85%+ correct postal code association

2. **Performance Targets**
   - [ ] <100ms average address processing time
   - [ ] <5% LLM usage after 1000 address learning phase
   - [ ] 95%+ cache hit rate for common addresses
   - [ ] <$0.001 average cost per address classification

3. **Quality Metrics**
   - [ ] 90%+ reduction in address variations
   - [ ] 15%+ improvement in ethnicity prediction accuracy
   - [ ] 80%+ automated correction of common typos
   - [ ] Zero data loss during address processing

### **Business Success Criteria**

1. **Data Quality Improvement**
   - [ ] Consistent suburb naming across all lead records
   - [ ] Standardized city/province formats for CRM integration
   - [ ] Accurate postal code assignment for 80%+ of addresses
   - [ ] Elimination of manual address cleanup tasks

2. **Ethnicity Prediction Enhancement**
   - [ ] 20%+ improvement in suburb-based ethnicity accuracy
   - [ ] Better spatial correlation analysis capabilities
   - [ ] Reduced false positives in demographic targeting
   - [ ] More confident ethnicity classifications

3. **Operational Efficiency**
   - [ ] Zero manual intervention for 90%+ of address cleaning
   - [ ] Seamless integration with existing job processing workflow
   - [ ] Real-time address validation for new leads
   - [ ] Automated learning from manual corrections

### **User Experience Goals**

1. **Dialler Team Benefits**
   - [ ] Consistent address formats in lead sheets
   - [ ] Accurate geographic context for call routing
   - [ ] Reliable suburb information for targeting
   - [ ] Reduced confusion from address variations

2. **System Administrator Benefits**
   - [ ] Clear address quality metrics and reporting
   - [ ] Easy manual correction and override capabilities
   - [ ] Comprehensive audit trail of address changes
   - [ ] Performance monitoring and optimization tools

## 📚 **Required Background Reading**

### **Pre-Development Reading List**

1. **Project Foundation**
   - [ ] `CLAUDE.md` - Complete project context and architecture
   - [ ] `CLAUDE_RULES.md` - Mandatory development standards and rules
   - [ ] `docs/coding-standards.md` - Code quality and style requirements

2. **Technical Architecture**
   - [ ] `docs/architecture/system-design.md` - Overall system architecture
   - [ ] `docs/architecture/database-schema.md` - Database design patterns
   - [ ] `src/leadscout/classification/` - Existing classification pipeline code

3. **LeadScout Specifics**
   - [ ] `src/leadscout/core/resumable_job_runner.py` - Job processing framework
   - [ ] `src/leadscout/classification/learning_database.py` - Learning system patterns
   - [ ] `src/leadscout/cli/` - CLI command patterns and conventions

4. **South African Context**
   - [ ] SA Municipal boundaries and naming conventions
   - [ ] Historical place name changes (Port Elizabeth → Gqeberha)
   - [ ] Common address formats and postal code systems
   - [ ] Provincial and language variations in place names

### **Development Prerequisites**

1. **Technical Requirements**
   - [ ] Python 3.11+ development environment
   - [ ] Poetry package management understanding
   - [ ] SQLite database design experience
   - [ ] Async/await programming patterns
   - [ ] LLM integration experience (OpenAI/Anthropic APIs)

2. **Testing Requirements**
   - [ ] pytest framework proficiency
   - [ ] Mock and fixture creation for LLM testing
   - [ ] Database testing patterns
   - [ ] Performance testing and benchmarking

3. **Quality Assurance**
   - [ ] Type hint annotation requirements
   - [ ] Structured logging implementation
   - [ ] Error handling and exception management
   - [ ] Code review and validation processes

## 🧪 **Test Case Framework**

### **Unit Test Categories**

1. **Rule-Based Processing Tests**
   ```python
   def test_abbreviation_expansion():
       assert expand_abbreviation("Main St") == "Main Street"
       assert expand_abbreviation("JHB") == "Johannesburg"
   
   def test_postal_code_extraction():
       assert extract_postal_code("123 Main St, Sandton 2196") == "2196"
   ```

2. **Fuzzy Matching Tests**
   ```python
   def test_typo_correction():
       assert fuzzy_match("Sandtom") == "Sandton"
       assert fuzzy_match("Rosbank") == "Rosebank"
   ```

3. **LLM Classification Tests**
   ```python
   @pytest.mark.asyncio
   async def test_llm_address_classification():
       result = await classify_address("123 Main St, Sandtom, JHB")
       assert result.suburb == "Sandton"
       assert result.city == "Johannesburg"
   ```

### **Integration Test Scenarios**

1. **End-to-End Address Pipeline**
   - [ ] Raw address → canonical components
   - [ ] Performance under load testing
   - [ ] Learning system integration
   - [ ] Cache effectiveness validation

2. **Database Integration**
   - [ ] Pattern storage and retrieval
   - [ ] Gazetteer lookup performance
   - [ ] Cache hit rate optimization
   - [ ] Data consistency validation

### **Performance Test Benchmarks**

1. **Speed Benchmarks**
   - [ ] <100ms processing for 95% of addresses
   - [ ] <50ms for cached addresses
   - [ ] <200ms for complex LLM classifications
   - [ ] Bulk processing: 1000+ addresses/minute

2. **Accuracy Benchmarks**
   - [ ] Test dataset: 1000 manually verified SA addresses
   - [ ] Accuracy target: 95%+ correct canonicalization
   - [ ] Learning effectiveness: Improving accuracy over time
   - [ ] Error categorization and analysis

## 🔗 **Integration Points**

### **Existing System Integration**

1. **Job Processing Pipeline**
   - Integrate address cleaning into `ResumableJobRunner`
   - Store canonical addresses in `lead_processing_results`
   - Update export commands to include clean addresses

2. **Ethnicity Classification**
   - Use canonical suburbs for improved spatial prediction
   - Update confirmation system to include address validation
   - Enhance learning database with clean address correlations

3. **CLI Commands**
   - Extend `jobs export` with address cleaning options
   - Add `address` command group for standalone processing
   - Include address quality metrics in `jobs analyze`

### **Future Integration Opportunities**

1. **CRM System Integration**
   - Real-time address validation API endpoints
   - Batch address cleaning for existing CRM data
   - Address quality scoring for lead prioritization

2. **Geocoding Services**
   - Coordinate lookup for spatial analysis
   - Delivery route optimization
   - Geographic clustering analysis

3. **Business Intelligence**
   - Address quality dashboards
   - Geographic lead distribution analysis
   - Market penetration mapping

---

**Document Status**: Design Phase Complete  
**Next Step**: Review and approve design before implementation  
**Estimated Implementation**: 8-12 weeks (4 phases)  
**Success Measurement**: Technical metrics + Business value + User experience goals
