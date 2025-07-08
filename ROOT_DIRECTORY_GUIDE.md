# LeadScout Root Directory Guide

**Purpose**: Guide to the clean, production-ready root directory structure.

## 📋 **Essential Documentation**

### **Primary Documentation (Read First)**
1. **`README.md`** - Main project overview and CLI usage guide
2. **`CLAUDE.md`** - Optimized development context (194 lines, focused on architecture)
3. **`CLAUDE_RULES.md`** - Development rules and coding standards

### **Technical Documentation**
4. **`docs/PRODUCTION_DEPLOYMENT_GUIDE.md`** - Production deployment procedures
5. **`docs/coding-standards.md`** - Code quality requirements
6. **`docs/architecture/system-design.md`** - System architecture
7. **`docs/UTILITY_SCRIPTS_REFERENCE.md`** - Utility scripts documentation

## 🛠️ **Utility Scripts (Production-Ready)**

### **Data Management & Export**
- **`export_job_results.py`** - Export job results to Excel (standalone version of CLI export)
- **`analyze_job_statistics.py`** - Comprehensive job analysis (standalone version of CLI analyze)

### **System Analysis & Performance**
- **`analyze_learning_performance.py`** - Learning database performance analysis
- **`benchmark_learning_performance.py`** - Performance benchmarking tool
- **`validate_production.py`** - Production readiness validation
- **`validate_system_performance.py`** - System performance validation

### **Data Acquisition**
- **`download_cipc_data.py`** - CIPC data acquisition for system foundation
- **`check_cipc_availability.py`** - CIPC file availability checking
- **`simple_cipc_download.py`** - Simple CIPC download utility

### **Development & Testing**
- **`run_logistics_demo.py`** - Production demo script for business presentations
- **`quick_llm_test.py`** - Quick LLM functionality test
- **`check_results.py`** - Quick result validation and display

## 📁 **Directory Structure**

### **Core Directories**
- **`src/leadscout/`** - Main application source code
- **`tests/`** - Production test suite
- **`docs/`** - Comprehensive documentation
- **`cache/`** - SQLite databases (jobs.db, llm_learning.db)
- **`data/`** - Data files and outputs

### **Development Support**
- **`scripts/`** - Additional utility scripts
- **`config/`** - Configuration files
- **`dev-tasks/`** - Development task management

### **Archives**
- **`archive/development-scripts/`** - Archived development/test scripts (24 files)
- **`archive/CLAUDE_COMPREHENSIVE_ORIGINAL.md`** - Original comprehensive CLAUDE.md (1,214 lines)
- **`docs/archive/`** - Archived documentation and reports

## 🚀 **Production CLI System**

The system now provides complete functionality through clean CLI commands:

### **Lead Processing**
```bash
# Simple enrichment
poetry run leadscout enrich leads.xlsx --output enriched.xlsx

# Production job management
poetry run leadscout jobs process leads.xlsx --batch-size 100
```

### **Job Management & Analysis**
```bash
# List and manage jobs
poetry run leadscout jobs list
poetry run leadscout jobs status <job-id>

# Export and analyze results
poetry run leadscout jobs export <job-id> --output results.xlsx
poetry run leadscout jobs analyze <job-id>
```

### **System Configuration**
```bash
# Configuration management
poetry run leadscout config set openai_api_key YOUR_KEY
poetry run leadscout config test

# Cache management
poetry run leadscout cache status
poetry run leadscout cache clean --older-than 30
```

## 🔧 **When to Use Scripts vs CLI**

### **Use CLI Commands For:**
- ✅ Regular lead processing and job management
- ✅ Standard export and analysis workflows
- ✅ Configuration and cache management
- ✅ Production operations

### **Use Standalone Scripts For:**
- 🛠️ Custom analysis and research workflows
- 🛠️ Integration with external tools
- 🛠️ Direct database access needs
- 🛠️ Performance benchmarking and testing
- 🛠️ System validation and diagnostics

## 📊 **Current Status**

### **Production Ready**
- ✅ Complete CLI implementation with Poetry integration
- ✅ Zero operational costs through intelligent learning
- ✅ Enterprise performance (0.8ms average, 625x faster than targets)
- ✅ Production reliability with resumable job framework
- ✅ Professional documentation and clean codebase

### **Archive Summary**
- 📦 **24 development scripts** moved to `archive/development-scripts/`
- 📦 **63 development documents** organized in `docs/archive/`
- 🧹 **Temporary files** cleaned up (coverage, validation, locks)
- 📝 **All preserved scripts** have comprehensive docstrings

## 🎯 **Future Development**

### **Root Directory Maintenance**
- Keep only production-essential scripts in root
- Archive completed development artifacts
- Maintain comprehensive docstrings for all preserved scripts
- Regular cleanup of temporary files

### **Script Enhancement**
- All preserved scripts follow coding standards
- Each script has clear purpose and usage documentation
- Scripts complement rather than duplicate CLI functionality
- Integration points with external tools are well-documented

## 📋 **Quick Reference**

### **For New Developers**
1. Read `README.md` for project overview
2. Read `CLAUDE.md` for development context
3. Follow `CLAUDE_RULES.md` for development standards
4. Use CLI for standard operations
5. Use standalone scripts for specialized workflows

### **For Production Deployment**
1. Follow `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`
2. Use `validate_production.py` for deployment validation
3. Monitor with `validate_system_performance.py`
4. Export data with CLI or `export_job_results.py`

---

**Status**: Production-ready system with clean, maintainable root directory structure.
**Last Updated**: January 2025 - Post CLI completion and root directory cleanup.