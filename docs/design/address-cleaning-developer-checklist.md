# Address Cleaning System - Developer Onboarding Checklist

## 🎯 **Quick Start Guide**

This checklist ensures developers have the essential background knowledge before implementing the address cleaning system.

## ✅ **Pre-Development Checklist**

### **1. Essential Project Knowledge**
- [ ] **Read `CLAUDE.md`** - Complete project context, architecture, and business goals
- [ ] **Read `CLAUDE_RULES.md`** - Mandatory development standards (NON-NEGOTIABLE)
- [ ] **Read `docs/coding-standards.md`** - Code quality requirements and patterns
- [ ] **Review `README.md`** - Current CLI functionality and user experience

### **2. Technical Architecture Understanding**
- [ ] **Study existing classification pipeline** - `src/leadscout/classification/`
  - How name ethnicity classification works (our proven model)
  - Multi-layered approach: Rule → Phonetic → LLM → Learning
  - Learning database patterns and caching strategies
- [ ] **Understand job processing framework** - `src/leadscout/core/resumable_job_runner.py`
  - How jobs are structured and processed
  - Database integration patterns
  - Error handling and resumable operations
- [ ] **Review CLI command patterns** - `src/leadscout/cli/`
  - How commands are structured and organized
  - User experience patterns and help text
  - Integration with core business logic

### **3. Database Design Patterns**
- [ ] **Study existing schema** - `cache/jobs.db` and `cache/llm_learning.db`
  - How classifications are stored and retrieved
  - Learning pattern storage and effectiveness tracking
  - Performance optimization through indexes
- [ ] **Understand data relationships**
  - Job → Processing Results → Classifications
  - Learning database patterns and pattern generation
  - Cache strategy and TTL management

### **4. LLM Integration Patterns**
- [ ] **Review existing LLM usage** - `src/leadscout/classification/llm.py`
  - Prompt engineering for structured responses
  - Error handling and retry logic
  - Cost tracking and optimization
  - Provider switching (OpenAI/Anthropic)
- [ ] **Understand learning system** - `src/leadscout/classification/learning_database.py`
  - How patterns are extracted from LLM responses
  - Cache hit optimization
  - Cost reduction through learning

### **5. South African Context Knowledge**
- [ ] **Study SA address formats and conventions**
  - Common abbreviations: JHB, CT, PTA, GP, WC
  - Province names and variations
  - Suburb naming patterns and hierarchies
  - Postal code systems and formats
- [ ] **Historical place name changes**
  - Port Elizabeth → Gqeberha
  - Pretoria → City of Tshwane (administrative)
  - Other municipal boundary changes
- [ ] **Language and cultural variations**
  - Afrikaans place names (Kaapstad, Bloemfontein)
  - African language variations
  - Common misspellings and phonetic variations

## 🧪 **Technical Prerequisites**

### **Development Environment**
- [ ] **Python 3.11+ environment set up**
- [ ] **Poetry package management** - `poetry install` successful
- [ ] **Virtual environment activated** - `source .venv/bin/activate`
- [ ] **CLI working** - `poetry run leadscout --help` displays commands
- [ ] **Database access** - Can query `cache/jobs.db` with SQLite tools

### **API Access**
- [ ] **OpenAI API key configured** - For LLM address classification
- [ ] **Anthropic API key configured** - For provider redundancy
- [ ] **Test LLM integration** - Verify both providers work with existing system
- [ ] **Understand rate limits** - Know current API quotas and limitations

### **Testing Capabilities**
- [ ] **pytest framework** - Can run existing tests successfully
- [ ] **Mock/fixture experience** - Understand how to mock LLM calls for testing
- [ ] **Database testing** - Can create and test with temporary databases
- [ ] **Performance testing** - Understand benchmarking and load testing approaches

## 📚 **Code Study Requirements**

### **Critical Files to Understand**

1. **`src/leadscout/classification/name_classifier.py`** (if exists)
   - Multi-layered classification approach
   - Confidence scoring and fallback logic
   - Pattern matching and caching

2. **`src/leadscout/classification/learning_database.py`**
   - How learning patterns are stored and retrieved
   - Pattern effectiveness tracking
   - Cache optimization strategies

3. **`src/leadscout/core/resumable_job_runner.py`**
   - Job lifecycle management
   - Database integration patterns
   - Error handling and recovery

4. **`src/leadscout/cli/jobs.py`**
   - Command structure and user experience
   - Database querying patterns
   - Export functionality

5. **`src/leadscout/models/`** - Data models and validation patterns

### **Architecture Patterns to Understand**

- [ ] **Dependency Injection** - How services are injected and configured
- [ ] **Async Processing** - Async/await patterns for LLM calls
- [ ] **Error Handling** - Custom exception hierarchy and handling
- [ ] **Logging Patterns** - Structured logging with context
- [ ] **Configuration Management** - Settings and environment handling

## 🎯 **Implementation Strategy Understanding**

### **Design Philosophy**
- [ ] **Understand "uberthink" approach** - Think comprehensively, implement incrementally
- [ ] **Learn from name classification success** - Apply proven patterns to addresses
- [ ] **Pragmatic first, extensible second** - Deliver immediate value, build for future
- [ ] **Learning-driven optimization** - Start with LLM, reduce cost through learning

### **Business Integration Points**
- [ ] **Dialler team workflow** - How clean addresses improve sales process
- [ ] **Ethnicity prediction enhancement** - How clean suburbs improve demographic analysis
- [ ] **Data quality improvement** - How standardization helps CRM integration
- [ ] **Spatial intelligence** - How geography correlates with demographics in SA

## ✅ **Ready-to-Code Validation**

### **Knowledge Verification**
Complete these checks before starting implementation:

- [ ] **Can explain the multi-layered classification approach** in your own words
- [ ] **Can describe how learning reduces LLM costs** and provide specific examples
- [ ] **Can identify 3 specific SA address challenges** and how to solve them
- [ ] **Can explain the database schema design** for address classifications
- [ ] **Can describe the integration points** with existing ethnicity system

### **Technical Validation**
- [ ] **Successfully run existing CLI commands** and understand output
- [ ] **Query the learning database** and understand pattern storage
- [ ] **Review a job export file** and understand current data structure
- [ ] **Run the test suite** and understand testing patterns
- [ ] **Trace through a complete job processing cycle** from input to output

### **Code Reading Verification**
- [ ] **Read and understand 3 core files** from the critical files list
- [ ] **Trace through the name classification pipeline** and understand each step
- [ ] **Understand the CLI command structure** and can add a simple new command
- [ ] **Understand the database integration patterns** and can query/insert data

## 🚨 **Critical Success Factors**

### **Non-Negotiables from CLAUDE_RULES.md**
- [ ] **Type hints on ALL functions** - No exceptions
- [ ] **Google-style docstrings** for all public functions/classes
- [ ] **Structured logging with context** - Never use print statements
- [ ] **Async patterns for all I/O** - LLM calls, database operations
- [ ] **Comprehensive error handling** - Custom exception hierarchy
- [ ] **Test-driven development** - Tests first, implementation second

### **Architecture Compliance**
- [ ] **Follow existing patterns** - Don't invent new approaches without justification
- [ ] **Maintain backward compatibility** - Don't break existing CLI or exports
- [ ] **Performance first** - Design for <100ms processing from start
- [ ] **Cost optimization** - Minimize LLM usage through intelligent caching

## 📅 **Recommended Study Timeline**

### **Day 1-2: Foundation**
- Read all essential project documentation
- Set up development environment
- Run and understand existing CLI commands

### **Day 3-4: Architecture Deep Dive**
- Study existing classification pipeline code
- Understand database schema and patterns
- Trace through complete job processing workflow

### **Day 5: Validation & Planning**
- Complete all verification checks
- Review address cleaning design document
- Plan Phase 1 implementation approach

## ❓ **Questions to Ask Before Starting**

If you can't answer these questions, spend more time on background reading:

1. **How does the existing name classification pipeline work?**
2. **What are the 4 layers in the multi-layered approach?**
3. **How does the learning database reduce LLM costs?**
4. **What are 5 common SA address format challenges?**
5. **How will clean addresses improve ethnicity predictions?**
6. **What are the performance and cost targets for address cleaning?**
7. **How does the resumable job framework prevent data loss?**
8. **What CLI commands will need to be modified or added?**

## ✅ **Final Go/No-Go Checklist**

Before writing the first line of address cleaning code:

- [ ] ✅ **All documentation read and understood**
- [ ] ✅ **Development environment fully functional**
- [ ] ✅ **Existing codebase patterns understood**
- [ ] ✅ **SA address challenges clearly identified**
- [ ] ✅ **Design document reviewed and questions answered**
- [ ] ✅ **Test strategy planned and understood**
- [ ] ✅ **Performance and cost targets committed to memory**
- [ ] ✅ **Integration points with ethnicity system understood**

**Only proceed to implementation when ALL items are checked ✅**

---

**Remember**: This is a complex system that builds on proven patterns. Understanding the existing successful name classification system is crucial for replicating that success with addresses. Take the time to study thoroughly - it will save weeks of development time and prevent architectural mistakes.

**Estimated Study Time**: 3-5 days for thorough preparation  
**Payoff**: 50%+ faster development and higher code quality  
**Success Pattern**: Follow the same multi-layered approach that made name classification successful