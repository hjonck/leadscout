# Developer A: Validation & Integration Testing Assignment

## CRITICAL: Session Initialization Checklist

### 1. Read Core Project Files (MANDATORY)
Execute these commands in order:
```bash
# Navigate to project
cd /Users/hjonck/Development/gitprojects/AgileWorksZA/leadscout

# Read core project context
Read CLAUDE.md                                    # Complete project overview
Read CLAUDE_RULES.md                             # Development rules and standards  
Read PROJECT_PLAN.md                             # Current status and priorities
```

### 2. Environment Setup (MANDATORY)
```bash
# MANDATORY: Use local virtual environment
source .venv/bin/activate                        # Required for all Python commands
poetry --version                                # Verify Poetry is available
python --version                               # Should be Python 3.11+
```

### 3. Review Development Standards
**Architecture Standards to Follow:**
- **MANDATORY**: All Python code must use `source .venv/bin/activate &&` prefix
- **MANDATORY**: Complete type hints on every function
- **MANDATORY**: Comprehensive docstrings following Google style
- **MANDATORY**: 80%+ test coverage with pytest
- **FORBIDDEN**: Time estimates for tasks (focus on completion criteria)

## Objective
Validate your caching and database infrastructure meets all quality gates and integration requirements. Provide comprehensive testing report for Technical Project Lead validation.

## Context
Developer B has completed rule-based and phonetic classification systems. Your caching infrastructure is now being used in production. We need to validate quality gates before declaring Phase 2 complete.

## Required Deliverables

### 1. Test Coverage Validation
```bash
# Ensure you're in the right environment
cd /Users/hjonck/Development/gitprojects/AgileWorksZA/leadscout
source .venv/bin/activate

# Run comprehensive test coverage
pytest --cov=leadscout.cache --cov=leadscout.cipc --cov-report=term-missing --cov-report=html
pytest --cov=leadscout.cache --cov=leadscout.cipc --cov-fail-under=80

# Save coverage report
pytest --cov=leadscout.cache --cov=leadscout.cipc --cov-report=html:coverage_report_dev_a
```

**Required**: Achieve 80%+ test coverage for your modules (cache, cipc)

### 2. Performance Benchmark Validation
```bash
# Test cache performance targets
python -m pytest tests/ -k "performance" -v
# OR create performance test if needed

# Document actual performance metrics:
# - Cache lookup time: <10ms target
# - Database query time: <50ms target  
# - Cache hit rate: >80% target
```

**Required**: Provide actual performance measurements vs targets

### 3. Integration Testing with Developer B
```bash
# Test your cache APIs with classification system
python -c "
import asyncio
from src.leadscout.classification import NameClassifier
from src.leadscout.cache import CacheManager

async def test_integration():
    classifier = NameClassifier()
    cache = CacheManager()
    
    # Test classification with cache
    result = await classifier.classify('Thabo Mthembu')
    print(f'Classification: {result}')
    
    # Verify cache storage and retrieval
    cached = await cache.get_classification('Thabo Mthembu')
    print(f'Cached result: {cached}')

asyncio.run(test_integration())
"
```

**Required**: Verify seamless integration between your cache and Developer B's classification

### 4. Code Quality Validation
```bash
# Type checking
mypy src/leadscout/cache/ src/leadscout/cipc/

# Code formatting
black --check src/leadscout/cache/ src/leadscout/cipc/
isort --check-only src/leadscout/cache/ src/leadscout/cipc/

# Linting
flake8 src/leadscout/cache/ src/leadscout/cipc/
```

**Required**: All quality checks must pass clean

## Report Template

Create `dev-tasks/developer-a-validation-report.md` with:

```markdown
# Developer A Validation Report

## Test Coverage Results
- **Coverage Percentage**: X%
- **Lines Covered**: X/X
- **Missing Coverage**: [List any gaps]
- **Status**: ✅ PASS / ❌ FAIL (80% target)

## Performance Benchmark Results
- **Cache Lookup Average**: Xms (target: <10ms)
- **Database Query Average**: Xms (target: <50ms)
- **Cache Hit Rate**: X% (target: >80%)
- **Status**: ✅ PASS / ❌ FAIL

## Integration Test Results
- **Classification + Cache**: ✅ PASS / ❌ FAIL
- **Data Model Compatibility**: ✅ PASS / ❌ FAIL
- **API Contract Compliance**: ✅ PASS / ❌ FAIL
- **Error Handling**: ✅ PASS / ❌ FAIL

## Code Quality Results
- **mypy**: ✅ PASS / ❌ FAIL
- **black**: ✅ PASS / ❌ FAIL
- **isort**: ✅ PASS / ❌ FAIL
- **flake8**: ✅ PASS / ❌ FAIL

## Issues Identified
[List any problems found and how you fixed them]

## API Performance Documentation
[Provide actual performance measurements for your APIs]

## Integration Status
✅ Ready for Production / ❌ Needs Additional Work

## Next Steps Recommended
[Your recommendations for next development priorities]
```

## Success Criteria
- [ ] 80%+ test coverage achieved
- [ ] All performance targets met or exceeded  
- [ ] Integration with Developer B's systems working flawlessly
- [ ] All code quality checks passing
- [ ] Comprehensive validation report provided

## Timeline
Complete validation and provide report within one focused development session.

## Integration Requirements
Your cache APIs must work seamlessly with:
- `NameClassifier.classify()` method from Developer B
- Classification result storage and retrieval
- Performance targets for classification pipeline

## Quality Gates (Non-Negotiable)
1. **Test Coverage**: 80%+ for your modules
2. **Performance**: Meet all SLA targets (<10ms cache, >80% hit rate)
3. **Integration**: Classification system uses your cache successfully
4. **Code Quality**: Pass all linting, typing, formatting checks
5. **Documentation**: Provide clear validation report

---

**Project**: LeadScout AI-Powered Lead Enrichment System  
**Your Role**: Developer A - CIPC Integration & Caching Specialist  
**Assignment**: Validation & Integration Testing  
**Deliverable**: Comprehensive validation report in dev-tasks/developer-a-validation-report.md