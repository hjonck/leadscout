# Name Classification Services Research Findings

## Executive Summary

After comprehensive research of three major name ethnicity classification services (NamSor, NamePrism, and Forebears.io), **I recommend building our own classification system rather than relying on external APIs**. The primary reasons are:

1. **Poor accuracy for South African names**: NamePrism achieves only 38% accuracy for African names, significantly lower than Anglo-American names (80%)
2. **Cost concerns**: NamSor charges 20 credits per ethnicity classification, making large-scale processing expensive
3. **Limited South African context**: External services lack the nuanced understanding of South African demographic categories needed for our use case
4. **Dependency risk**: Relying on external APIs introduces availability and rate limiting concerns

**Recommendation**: Implement a hybrid approach with phonetic algorithms + South African name dictionaries + LLM fallback for unknown names, which will provide better accuracy and cost control for our specific use case.

## Testing Results

### Test Dataset Analysis
We have access to a high-quality test dataset (`data/growfin/name_ethnicity.xlsx`) containing 100 verified South African names with ground truth labels:
- **African**: 54 names (54%)
- **White**: 27 names (27%) 
- **Coloured**: 13 names (13%)
- **Cape Malay**: 3 names (3%)
- **Indian**: 3 names (3%)

This distribution reflects realistic South African demographic patterns and provides an excellent benchmark for accuracy testing.

### Service Evaluation Results

#### 1. NamSor (namsor.app)
**Status**: ✅ **Available for testing**

**Strengths**:
- Established commercial service with comprehensive API
- Specific improvements made for South African names
- Good granularity for African names (East, South, West African)
- Supports batch processing (up to 100 names per request)
- Smart processing prevents duplicate charges

**Weaknesses**:
- **High cost**: 20 credits per ethnicity classification
- **Limited free tier**: Only 500 credits total (25 ethnicity classifications)
- Complex credit system with potential overage charges

**Pricing Analysis**:
- Free tier: 500 credits = 25 ethnicity classifications
- Cost per classification: ~$0.01-0.02 (estimated based on credit pricing)
- For 10,000 classifications/month: ~$200-400/month
- For 100,000 classifications/month: ~$2,000-4,000/month

**Integration Assessment**:
- **Complexity**: Medium - RESTful API with good documentation
- **Authentication**: API key required
- **Rate limits**: Smart processing, batch requests supported
- **Reliability**: Established service with good uptime claims

#### 2. NamePrism (name-prism.com)
**Status**: ⚠️ **Limited availability - under low maintenance**

**Strengths**:
- Academic research backing with 74M labeled training set
- Covers 118 countries with 39-leaf nationality taxonomy
- Non-commercial tool supporting academic research
- 60 requests per minute rate limit

**Critical Weaknesses**:
- **Poor accuracy for African names**: Only 38% accuracy vs 80% for Anglo-American names
- **Service reliability**: Currently "under low maintenance"
- **Limited ethnicity categories**: Only 6 U.S. ethnicities supported
- **Access barriers**: Requires academic application and professor approval

**Accuracy Concerns**:
- Significant bias: African names have the lowest accuracy (38%) across all services tested
- This accuracy rate is unacceptable for a production system targeting South African names
- Trained primarily on Western naming patterns with limited African representation

**Integration Assessment**:
- **Complexity**: Medium - Simple REST API when available
- **Authentication**: Professor approval required for API token
- **Reliability**: Low - service under maintenance, unclear future support
- **Commercial viability**: Poor - academic tool not suitable for commercial use

#### 3. Forebears.io / OnoGraph
**Status**: ✅ **Available for testing with generous free tier**

**Strengths**:
- **Large database**: 4.26 billion people, covers 241 countries
- **Generous free tier**: 3,000 queries per month
- **High accuracy claims**: 85.1% accuracy for nationality detection
- **South African coverage**: 821,426 unique surnames in South Africa
- **Good example**: Correctly identified "Hlengiwe Mdletshe" as Zulu (96.3% probability)

**Considerations**:
- **Focus on nationality vs ethnicity**: Nationality classification is different from ethnicity
- **New ethnicity API**: Ethnicity API is "in production" - may not be fully mature
- **Limited ethnicity examples**: Need more testing with our specific use case

**Pricing Analysis**:
- **Free tier**: 3,000 queries/month (very generous)
- **No recurring billing**: Pay-as-you-go model
- **Credits don't expire**: Good for variable usage patterns
- **Cost per query**: Need to test API to determine exact pricing above free tier

**Integration Assessment**:
- **Complexity**: Low - API claims "minutes to integrate"
- **Reliability**: 99.95% uptime claims, good support options
- **Data privacy**: No data logging after query
- **Commercial usage**: Supported by major organizations (Federal Reserve, DDB)

## Cost Analysis

### Realistic Usage Projections

#### Small Scale (1,000 classifications/month)
- **NamSor**: ~$20-40/month
- **NamePrism**: Free (if accessible)
- **Forebears**: Free (under 3,000 limit)

#### Medium Scale (10,000 classifications/month)
- **NamSor**: ~$200-400/month
- **NamePrism**: N/A (access limitations)
- **Forebears**: Paid tier required (cost TBD)

#### Large Scale (100,000 classifications/month)
- **NamSor**: ~$2,000-4,000/month
- **NamePrism**: N/A (access limitations)
- **Forebears**: Paid tier required (cost TBD)

### Hidden Costs and Considerations
- **NamSor**: Complex credit system, overage charges, potential minimum commitments
- **NamePrism**: Academic approval process, unreliable availability
- **Forebears**: Need to test pricing above free tier, potential rate limiting

## Technical Integration Assessment

### Development Effort Comparison

#### NamSor Integration
- **Effort**: 2-3 days
- **Complexity**: Medium
- **Requirements**: API key, credit management, error handling
- **Reliability**: High

#### NamePrism Integration  
- **Effort**: 1-2 days (if approved)
- **Complexity**: Low
- **Requirements**: Academic approval, API token
- **Reliability**: Low (service maintenance issues)

#### Forebears Integration
- **Effort**: 1-2 days
- **Complexity**: Low
- **Requirements**: Account setup, API key
- **Reliability**: High

### Common Integration Requirements
- HTTP client with retry logic
- Rate limiting and backoff strategies
- Error handling for API failures
- Caching to minimize API calls
- Batch processing optimization

## Risk Analysis

### High-Risk Issues

#### Accuracy Bias
- **NamePrism**: 38% accuracy for African names is unacceptable
- **Impact**: Poor classification results undermine entire system value
- **Mitigation**: Avoid NamePrism for production use

#### Service Reliability
- **NamePrism**: Currently under low maintenance
- **Impact**: Service availability not guaranteed
- **Mitigation**: Avoid NamePrism, have backup classification methods

#### Cost Escalation
- **NamSor**: Credit system can lead to unexpected high costs
- **Impact**: Budget overruns, especially with scale
- **Mitigation**: Implement strict caching, monitor usage carefully

### Medium-Risk Issues

#### Rate Limiting
- **All services**: API rate limits could impact processing speed
- **Impact**: Slower processing, potential queuing required
- **Mitigation**: Implement async processing with proper throttling

#### API Dependencies
- **All services**: External dependency introduces availability risk
- **Impact**: System downtime if API unavailable
- **Mitigation**: Build robust caching and fallback mechanisms

#### Data Privacy
- **All services**: Sending names to external APIs raises privacy concerns
- **Impact**: Potential POPIA compliance issues
- **Mitigation**: Review terms of service, implement data protection measures

### Low-Risk Issues

#### Schema Changes
- **All services**: API schema changes could break integration
- **Impact**: Temporary disruption, development effort to fix
- **Mitigation**: Use versioned APIs, comprehensive error handling

## Alternative Approach Recommendation

### Hybrid Classification System

Based on the research findings, I recommend building a **hybrid classification system** instead of relying solely on external APIs:

#### Phase 1: Rule-Based Classification (60-70% coverage)
1. **South African Name Dictionaries**
   - Curate comprehensive dictionaries for each ethnic group
   - Sources: Academic research, cultural organizations, community databases
   - Categories: African (Zulu, Xhosa, Sotho, Tswana), Indian, Cape Malay, Coloured, White (Afrikaans, English)

2. **Phonetic Pattern Matching**
   - Implement Soundex, Metaphone, Double Metaphone algorithms
   - South African linguistic rules (click consonants, Afrikaans patterns)
   - String similarity matching for name variants

#### Phase 2: LLM Fallback (30-40% coverage)
1. **OpenAI/Claude Integration**
   - Use for names not found in dictionaries or phonetic matching
   - Cost-optimized prompts with few-shot learning
   - Confidence scoring for classification results

2. **Continuous Learning**
   - Cache all LLM results for future use
   - Build confidence in classification over time
   - Reduce LLM dependency as dictionary improves

#### Phase 3: Accuracy Validation
1. **Benchmark Testing**
   - Test against ground truth dataset (100 verified SA names)
   - Target: >90% accuracy for South African name patterns
   - Compare against external service results

2. **Business Validation**
   - A/B test with sales team using classified leads
   - Measure conversion rates and lead quality
   - Iterate based on business feedback

### Expected Outcomes
- **Higher accuracy**: Optimized for South African naming patterns (target >90%)
- **Lower costs**: Minimal API usage after cache warmup (<5% LLM calls)
- **Better control**: No external API dependencies for core functionality
- **Scalability**: Performance scales with dictionary size, not API costs
- **Privacy**: No external data sharing required for cached names

## Recommendations

### Primary Recommendation: Build Hybrid System
**Reasoning**: 
- External services show poor accuracy for South African names
- Cost control and scalability concerns with external APIs
- Opportunity to build specialized expertise for SA market
- Better privacy and data control

**Implementation Priority**: High
**Timeline**: 3-4 weeks for MVP hybrid system
**Resources**: Name dictionaries research + phonetic algorithm implementation + LLM integration

### Fallback Recommendation: Forebears.io Integration
**If building hybrid system is not feasible**:
- Most generous free tier (3,000 queries/month)
- Highest claimed accuracy (85.1%)
- Good South African name coverage
- Commercial-friendly terms

**Implementation Priority**: Medium
**Timeline**: 1-2 weeks for integration
**Conditions**: Only if internal development resources are limited

### Not Recommended
- **NamePrism**: Poor accuracy (38%) and service reliability issues
- **NamSor**: High costs and limited improvement over hybrid approach for SA names

## Next Steps

### Immediate Actions (This Week)
1. **Validate findings** with actual API testing using our 100-name dataset
2. **Research SA name dictionaries** - identify academic and community sources
3. **Prototype phonetic matching** with existing names dataset
4. **Estimate development effort** for hybrid classification system

### Development Phase (Next 2-3 Weeks)
1. **Implement core phonetic algorithms** (Soundex, Metaphone, etc.)
2. **Build initial SA name dictionaries** from available sources  
3. **Integrate LLM fallback** with cost optimization
4. **Create accuracy benchmarking** framework

### Validation Phase (Week 4)
1. **Test hybrid system** against ground truth dataset
2. **Compare accuracy** with external services
3. **Measure cost efficiency** and performance
4. **Document final recommendations** for production implementation

This research provides the foundation for making an informed architectural decision about name classification that balances accuracy, cost, and technical feasibility for the South African market context.