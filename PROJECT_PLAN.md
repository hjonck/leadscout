# LeadScout MVP Development Plan

## Project Status: Foundation Phase
**Current Focus**: Setting up core architecture and data models  
**Last Updated**: 2025-01-05

## Release Scope Decisions

### ✅ **Included in First Release**
- Name ethnicity classification (core feature)
- Website discovery and validation
- LinkedIn profile research
- Contact validation and scoring
- Excel I/O with enhanced data
- SQLite caching system
- Async processing pipeline

### 🚫 **Excluded from First Release**
- **CIPC/CIPRO Integration**: Deferred to future release
  - Reason: Complex integration, not essential for MVP validation
  - Alternative: Focus on available data sources first

## Development Phases

### **Phase 1: Foundation** ✅ *Completed*
**Status**: Core architecture established

#### Data Models (Complexity: Simple) ✅
- [x] Create `Lead` model for input data validation
- [x] Create `EnrichedLead` model for output structure  
- [x] Create `Classification` model for ethnicity data
- [x] Create `ContactInfo` model for validation results
- [x] Add Pydantic validation and type hints

#### CLI Framework (Complexity: Simple) ✅
- [x] Set up Click-based command structure
- [x] Implement `enrich` command interface
- [x] Implement `cache` management commands
- [x] Implement `config` management commands
- [x] Add help text and documentation

#### Configuration System (Complexity: Moderate) ✅
- [x] Pydantic Settings with environment variables
- [x] API key validation and secure storage
- [x] Cache directory management
- [x] Logging configuration
- [x] Error handling setup

#### Excel I/O Operations (Complexity: Simple)
- [ ] Read XLSX with column validation
- [ ] Write enhanced XLSX with new columns
- [ ] Error handling for malformed files
- [ ] Progress tracking for large files

### **Phase 2: Core Systems** ⏳ *Next Priority*
**Dependencies**: Phase 1 completion

**Current Focus**: Excel I/O operations and SQLite cache layer

#### SQLite Cache Layer (Complexity: Moderate)
- [ ] Database schema design
- [ ] Cache models and operations
- [ ] TTL management and cleanup
- [ ] Query optimization
- [ ] Migration system

#### Name Classification System (Complexity: Complex)
- [ ] Phonetic algorithms implementation
  - [ ] Soundex algorithm
  - [ ] Metaphone algorithm  
  - [ ] Double Metaphone algorithm
  - [ ] NYSIIS algorithm
  - [ ] Jaro-Winkler algorithm
- [ ] LLM integration for classification
- [ ] Confidence scoring system
- [ ] Classification cache integration
- [ ] South African context optimization

### **Phase 3: Research & Enrichment** 📋 *Planned* 
**Dependencies**: Phase 2 completion

#### Website Discovery (Complexity: Moderate)
- [ ] Domain detection algorithms
- [ ] Website validation and scoring
- [ ] SSL/security checks
- [ ] Content analysis for business relevance

#### LinkedIn Research (Complexity: Complex)
- [ ] Profile search functionality
- [ ] Data extraction (compliance-first)
- [ ] Professional information scoring
- [ ] Rate limiting and error handling

#### Contact Validation (Complexity: Simple)
- [ ] Email format validation
- [ ] Phone number format validation
- [ ] Contact completeness scoring
- [ ] Data quality assessment

#### Scoring Engine (Complexity: Moderate)
- [ ] Pluggable scoring interface
- [ ] Default scoring implementation
- [ ] Weight configuration system
- [ ] Priority calculation algorithm

### **Phase 4: Integration & Testing** 📋 *Planned*
**Dependencies**: Phase 3 completion

#### End-to-End Pipeline (Complexity: Complex)
- [ ] Async processing coordination
- [ ] Batch processing optimization
- [ ] Error recovery mechanisms
- [ ] Progress tracking and reporting
- [ ] Performance optimization

#### Testing Suite (Complexity: Moderate)
- [ ] Unit tests for all components
- [ ] Integration tests with mock APIs
- [ ] Performance benchmarks
- [ ] End-to-end pipeline tests
- [ ] Edge case validation

#### Documentation & Polish (Complexity: Simple)
- [ ] Complete CLI help text
- [ ] Usage examples and tutorials
- [ ] Error message improvements
- [ ] Performance optimization
- [ ] Security review

## Current Sprint: Foundation Setup

### Immediate Action Items (Priority Order)

#### 🔥 **A) Environment Setup** - *Next Task*
- [ ] Poetry environment validation
- [ ] Basic project structure verification
- [ ] Test runner setup (pytest)
- [ ] Code quality tools configuration

#### 🔥 **B) Data Models Creation**
- [ ] Lead input model with field validation
- [ ] EnrichedLead output model design
- [ ] Classification result model
- [ ] Database table models

#### 🔥 **C) CLI Framework Foundation**
- [ ] Main CLI entry point
- [ ] Command structure implementation
- [ ] Basic help and error handling

#### 🔥 **D) Configuration System**
- [ ] Environment variable setup
- [ ] API key management
- [ ] Settings validation

## Quality Metrics & Gates

### Code Quality Requirements
- [ ] Type hints on all functions
- [ ] Google-style docstrings
- [ ] 80%+ test coverage
- [ ] Black/isort/flake8 compliance
- [ ] No hardcoded credentials

### Performance Targets
- Process 100+ leads per minute
- Memory usage <500MB for 10K leads
- <5% LLM calls after cache warmup
- >95% classification accuracy

### Security Requirements
- [ ] No hardcoded API keys
- [ ] Input validation on all data
- [ ] Secure credential storage
- [ ] Rate limiting on APIs
- [ ] Audit logging

## Risk Management

### Technical Risks
- **LinkedIn API Compliance**: Research terms of service thoroughly
- **LLM Cost Management**: Implement proper caching and rate limiting  
- **Performance with Large Files**: Design for scalability from start
- **API Rate Limits**: Build robust retry and backoff mechanisms

### Mitigation Strategies
- Start with mock APIs for development
- Implement comprehensive caching early
- Design pluggable architecture for easy changes
- Focus on data quality over processing speed

## Success Criteria

### MVP Success Metrics
- [ ] Process sample Excel file successfully
- [ ] Classify names with >90% accuracy on test set
- [ ] Enrich leads with website and LinkedIn data
- [ ] Generate prioritized lead scores
- [ ] Complete processing without manual intervention
- [ ] Maintain data quality and error reporting

### User Validation
- [ ] Sales team can use tool effectively
- [ ] Processing time is acceptable for workflow
- [ ] Results improve lead prioritization
- [ ] Error messages are clear and actionable

## Decision Log

### 2025-01-05: Scope Decisions
- **CIPC/CIPRO Integration**: Deferred to post-MVP
- **Reasoning**: Complex integration, focus on proven data sources first
- **Impact**: Adjusted scoring weights to prioritize name classification

### 2025-01-05: Time Estimation Policy
- **Decision**: No time estimates for development tasks
- **Reasoning**: Estimates create false expectations and pressure
- **Alternative**: Focus on priority order and completion criteria

### 2025-01-05: Project Tracking
- **Tool**: PROJECT_PLAN.md (this document)
- **Update Frequency**: Every significant development session
- **Format**: Structured markdown with completion tracking

---

**Next Session Action**: Start with Environment Setup validation and move to Data Models creation.