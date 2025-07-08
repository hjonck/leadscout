# LeadScout Claude Rules - Condensed Developer Onboarding

**Purpose**: Essential rules for new Claude developers. Read this FIRST, then reference complete CLAUDE_RULES.md as needed.

## 🎯 **Project Identity**

**Project**: LeadScout - AI-Powered Lead Enrichment System  
**Architecture**: Modular Python CLI with multi-layered classification  
**Quality Standard**: Professional, enterprise-grade production system  
**Current Status**: Production-ready with 68.6% cost efficiency through learning

## ⚠️ **CRITICAL RULES (NON-NEGOTIABLE)**

### **1. Verification Requirement**
- **NEVER ASSUME ANYTHING WORKS** until tested and verified
- **MANDATORY**: Test all code changes with actual execution before claiming success
- **FORBIDDEN**: Over-optimistic language ("should work", "expected to work") without testing
- **REQUIRED**: Provide actual test results and evidence when reporting functionality
- **CRITICAL**: **NEVER use `importlib.reload()`** - breaks Pydantic enum validation

### **2. Architecture Consistency**
- **NEVER** deviate from established modular architecture in `src/leadscout/`
- **IMMUTABLE**: Multi-layered classification (Rule-based → Phonetic → LLM → Learning)
- **REQUIRED**: Dependency injection, async processing, pluggable scoring patterns
- **FORBIDDEN**: Monolithic code, synchronous blocking operations, hardcoded values

### **3. Code Quality Standards**
- **MANDATORY**: Type hints on ALL functions and class attributes
- **MANDATORY**: Google-style docstrings for ALL public functions/classes
- **MANDATORY**: Error handling with custom exception hierarchy
- **FORBIDDEN**: Wildcard imports, hardcoded credentials, print statements
- **REQUIRED**: 80%+ test coverage for all new code

### **4. Resumable Job Framework (CRITICAL)**
- **MANDATORY**: ALL long-running operations MUST be resumable from interruption
- **REQUIRED**: SQLite-based job persistence with conservative resume strategy
- **REQUIRED**: Stream processing with configurable batch sizes (never load entire files)
- **FORBIDDEN**: In-memory processing without persistent checkpoints
- **PATTERN**: Process leads in batches, commit after each successful batch

### **5. Learning System Optimization**
- **MANDATORY**: Cache ALL successful classifications for auto-improvement
- **REQUIRED**: Extract patterns from successes to enhance rule-based classification
- **TARGET**: <5% LLM usage through intelligent pattern learning
- **PATTERN**: LLM success → Pattern extraction → Rule enhancement → Cost reduction

## 📁 **Architecture Overview**

### **Project Structure (IMMUTABLE)**
```
src/leadscout/
├── cli/                 # Command line interface
├── core/                # Core business logic & job processing
├── enrichment/          # Data enrichment modules
├── scoring/             # Scoring engine
├── classification/      # Multi-layered name classification
├── cache/               # Caching layer
└── models/              # Data models
```

### **Key Components**
- **Job Processing**: `core/job_database.py` - Resumable job framework
- **Classification**: `classification/` - Multi-layered ethnicity classification
- **Learning**: `classification/learning_database.py` - Cost optimization patterns
- **CLI**: `cli/` - Click-based command interface with Poetry integration

## 🔄 **Development Workflow**

### **Before Writing Code**
1. **Read** this document + complete CLAUDE_RULES.md + relevant design docs
2. **Check** existing patterns before implementing new ones
3. **Plan** test cases before writing implementation
4. **Verify** understanding of existing codebase patterns

### **During Development**
1. **Follow** existing patterns exactly (dependency injection, async, error handling)
2. **Test** each component as you build it
3. **Document** with comprehensive docstrings
4. **Integrate** with existing job processing and CLI patterns

### **Before Committing**
1. **Execute** comprehensive tests and provide results
2. **Validate** integration with existing functionality
3. **Check** performance impact and optimization
4. **Document** changes and integration points

## 🧪 **Testing Requirements**

### **Mandatory Testing**
- Unit tests for all business logic
- Integration tests for API interactions
- Performance validation for batch operations
- Error handling and edge case validation

### **Evidence Required**
- Actual test execution results
- Performance metrics comparison
- Error handling demonstration
- Integration validation proof

## 🎯 **Success Patterns**

### **Proven Architecture**
- **Multi-layered Classification**: 68.6% cost efficiency achieved
- **Learning Database**: Real-time pattern extraction and application
- **Resumable Jobs**: Bulletproof processing with SQLite persistence
- **CLI Integration**: Clean Poetry-based command interface

### **Performance Targets**
- **Processing Speed**: 100+ leads per minute
- **Memory Usage**: <500MB for 10K leads
- **API Efficiency**: <5% LLM calls after cache warmup
- **Accuracy**: >95% ethnicity classification

### **Integration Patterns**
- **Database**: SQLite with proper indexing and foreign keys
- **CLI**: Click framework with comprehensive help and progress indicators
- **Error Handling**: Custom exception hierarchy with structured logging
- **Configuration**: Pydantic BaseSettings with environment variable support

## 🚨 **Common Pitfalls to Avoid**

1. **Assuming functionality works** without testing
2. **Breaking existing job processing** patterns
3. **Using synchronous operations** for I/O
4. **Hardcoding values** instead of configuration
5. **Skipping error handling** for edge cases
6. **Not following established patterns** for database, CLI, or learning

## 📚 **Essential Reference Documents**

### **Must Read Before Starting**
1. **`CLAUDE.md`** - Complete project context and current status
2. **`CLAUDE_RULES.md`** - Complete development standards (this is condensed version)
3. **`docs/coding-standards.md`** - Code quality requirements
4. **Relevant design documents** for your specific assignment

### **Architecture References**
5. **`docs/architecture/system-design.md`** - System architecture decisions
6. **`README.md`** - User-facing documentation and CLI usage
7. **Existing source code patterns** in your assigned modules

## 🎯 **Developer Specialization Areas**

### **Developer A: Job Processing & Export Systems**
- **Focus**: Job database, export functionality, CLI commands
- **Key Files**: `core/job_database.py`, `cli/`, export systems
- **Patterns**: Resumable processing, SQLite operations, CLI integration

### **Developer B: Classification & Learning Systems**
- **Focus**: Classification algorithms, learning database, cost optimization
- **Key Files**: `classification/`, learning systems, pattern extraction
- **Patterns**: Multi-layered classification, learning optimization, spatial intelligence

## ⚡ **Quick Start Checklist**

### **Environment Setup**
- [ ] Poetry virtual environment activated
- [ ] All dependencies installed via `poetry install`
- [ ] CLI functional: `poetry run leadscout --help`
- [ ] Database access validated

### **Architecture Understanding**
- [ ] Multi-layered classification approach understood
- [ ] Resumable job framework patterns clear
- [ ] Learning database optimization approach understood
- [ ] Integration points with existing system identified

### **Development Ready**
- [ ] Test cases planned before implementation
- [ ] Existing patterns reviewed and understood
- [ ] Integration points with other developers coordinated
- [ ] Success criteria and validation approach defined

## 🆘 **When You Need Help**

### **Technical Questions**
- Review existing codebase patterns first
- Consult complete CLAUDE_RULES.md for detailed standards
- Check architecture documentation for design decisions

### **Integration Issues**
- Coordinate with Project Manager for cross-developer dependencies
- Validate integration patterns against existing functionality
- Test integration points thoroughly before reporting completion

### **Architecture Decisions**
- Consult CLAUDE.md for project context and current status
- Follow established patterns rather than creating new ones
- Escalate only when existing patterns don't support requirements

---

**Next Step**: Read complete CLAUDE_RULES.md for comprehensive standards  
**Success Pattern**: Follow proven architecture + verify everything with testing  
**Remember**: This system has achieved 68.6% cost efficiency - build on success!