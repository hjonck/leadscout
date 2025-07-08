# Epic 1: Ethnicity Confirmation System - Developer A Assignment

**Developer Role**: Job Processing & Export Systems Specialist  
**Epic Focus**: Ethnicity Confirmation with Record Tracing  
**Timeline**: 3 weeks (Phases 1-3)  
**Business Priority**: **CRITICAL** - Immediate need for dialler team workflow

## 🎯 **Mission Statement**

Implement complete ethnicity confirmation lifecycle with precise record tracing. Enable seamless workflow: AI prediction → enhanced Excel export → dialler team confirmation → learning system improvement.

**Core Deliverable**: Enriched Excel files with AI predictions + empty confirmation dropdown columns for dialler team workflow.

## 📋 **Essential Reading (MANDATORY - Complete Before Starting)**

### **Critical Documents (Read in Order)**
1. **`CLAUDE_RULES.md`** - Complete development standards (NON-NEGOTIABLE)
2. **`CLAUDE.md`** - Project context and technical architecture  
3. **`docs/design/ethnicity-confirmation-system.md`** - Complete technical specification
4. **`docs/design/ethnicity-confirmation-backlog.md`** - Implementation roadmap
5. **`docs/coding-standards.md`** - Code quality requirements

### **Key Architecture Files**
6. **`src/leadscout/core/job_database.py`** - Existing job processing patterns
7. **`src/leadscout/cli/`** - Existing CLI command patterns
8. **`src/leadscout/models/`** - Data model patterns

## ⚠️ **CRITICAL DEVELOPMENT RULES (NON-NEGOTIABLE)**

### **Verification & Testing Requirements**
- **NEVER ASSUME ANYTHING WORKS** until tested and verified
- **MANDATORY**: Test all code changes with actual test cases before claiming success
- **FORBIDDEN**: Over-optimistic assumptions about functionality without verification
- **REQUIRED**: Provide actual test results and evidence when reporting functionality
- **CRITICAL**: **NEVER use `importlib.reload()`** - breaks Pydantic enum validation

### **Architecture Consistency**
- **NEVER** deviate from established modular architecture in `src/leadscout/`
- **ALWAYS** follow existing patterns: dependency injection, async processing, pluggable scoring
- **FORBIDDEN**: Monolithic code, synchronous blocking operations, hardcoded values

### **Code Quality Standards**
- **MANDATORY**: Type hints on all functions and class attributes
- **MANDATORY**: Google-style docstrings for all public functions/classes
- **MANDATORY**: Error handling with custom exception hierarchy
- **FORBIDDEN**: Wildcard imports, hardcoded credentials, print statements

### **Resumable Job Framework (CRITICAL PRODUCTION REQUIREMENT)**
- **MANDATORY**: ALL operations MUST be resumable from any interruption point
- **REQUIRED**: Stream processing with SQLite intermediate storage
- **FORBIDDEN**: In-memory processing without persistent checkpoints
- **REQUIRED**: Conservative resume strategy - always resume from last committed batch

## 📊 **PHASE 1: Enhanced Database Schema (Week 1)**

### **Task 1.1: Core Confirmation Tables**
**Objective**: Implement precise record tracing with source tracking

```sql
-- Implementation required: ethnicity_confirmations table
CREATE TABLE ethnicity_confirmations (
    confirmation_id TEXT PRIMARY KEY,
    source_file_identifier TEXT NOT NULL,  -- filename + hash
    source_row_number INTEGER NOT NULL,    -- 1-based Excel row
    source_job_id TEXT NOT NULL,
    original_entity_name TEXT NOT NULL,
    original_director_name TEXT NOT NULL,
    -- [Complete schema in design doc]
);
```

**Success Criteria**:
- [ ] Table created with all 20+ columns from design specification
- [ ] Indexes created for performance optimization
- [ ] Foreign key constraints properly implemented
- [ ] **VERIFIED**: Database integrity checks pass
- [ ] **TESTED**: Record insertion and retrieval works correctly

### **Task 1.2: Canonical Ethnicity System**
**Objective**: Standardized ethnicity validation with SA-specific data

```sql
-- Implementation required: canonical_ethnicities table
CREATE TABLE canonical_ethnicities (
    ethnicity_code TEXT PRIMARY KEY,
    ethnicity_display_name TEXT NOT NULL,
    ethnicity_order INTEGER NOT NULL,  -- For dropdown ordering
);
```

**Success Criteria**:
- [ ] Canonical ethnicity table implemented with SA ethnicity hierarchy
- [ ] Initial data loaded (African, White, Coloured, Indian, Asian, etc.)
- [ ] Validation functions implemented for ethnicity checking
- [ ] **VERIFIED**: All ethnicity validations work correctly
- [ ] **TESTED**: Dropdown ordering functions correctly

### **Task 1.3: File Identification System**
**Objective**: Precise file tracking for record traceability

```python
def generate_file_identifier(file_path):
    """Generate unique identifier for source file tracking."""
    # Implementation required: filename + content hash
```

**Success Criteria**:
- [ ] File identifier generation implemented (filename + MD5 hash)
- [ ] Spatial context hash generation for correlation analysis
- [ ] **VERIFIED**: Unique identifiers generated for same/different files
- [ ] **TESTED**: Hash generation handles various file types correctly

### **Task 1.4: Enhanced Job Processing Integration**
**Objective**: Integrate confirmation support into existing job framework

**Success Criteria**:
- [ ] Enhanced `lead_processing_results` table with source tracking columns
- [ ] File processing session tracking implemented
- [ ] Integration with existing job database patterns
- [ ] **VERIFIED**: Existing job processing continues to work
- [ ] **TESTED**: New source tracking data stored correctly

## 📝 **PHASE 2: Enhanced Export System (Week 2)**

### **Task 2.1: 21-Column Excel Export Format**
**Objective**: Professional Excel output with AI predictions + confirmation columns

```
Required Excel Schema:
Original (11) + AI Enhancement (5) + Confirmation (2) + Metadata (3) = 21 columns
```

**Success Criteria**:
- [ ] 21-column export format implemented exactly per specification
- [ ] All original columns preserved in correct order
- [ ] AI enhancement columns (ethnicity, confidence, method, spatial_context, processing_notes)
- [ ] Empty confirmation columns (confirmed_ethnicity, confirmation_notes)
- [ ] Metadata columns (source_row_number, job_id, processed_at)
- [ ] **VERIFIED**: Excel file opens correctly in Excel/LibreOffice
- [ ] **TESTED**: All data exports accurately with proper formatting

### **Task 2.2: Professional Dropdown Validation**
**Objective**: Excel dropdown validation for confirmation columns

```python
def create_ethnicity_dropdown_validation(worksheet, start_row, end_row):
    """Create dropdown validation for confirmed_ethnicity column."""
    # Implementation required: Professional Excel dropdowns
```

**Success Criteria**:
- [ ] Excel dropdown validation implemented using openpyxl
- [ ] Ethnicity options ordered by frequency (African, White, Coloured, Indian...)
- [ ] Error messages configured for invalid selections
- [ ] Help prompts configured for user guidance
- [ ] **VERIFIED**: Dropdowns work correctly in Excel
- [ ] **TESTED**: Invalid entries properly rejected with clear error messages

### **Task 2.3: Confidence-Based Color Coding**
**Objective**: Visual confidence indicators for AI predictions

```python
def apply_confidence_color_coding(worksheet, start_row, end_row):
    """Apply color coding based on AI confidence levels."""
    # Green: >0.8, Yellow: 0.6-0.8, Red: <0.6
```

**Success Criteria**:
- [ ] Color coding implemented (green/yellow/red based on confidence)
- [ ] Colors applied to director_ethnicity column based on confidence values
- [ ] Professional color scheme using light, non-intrusive colors
- [ ] **VERIFIED**: Colors display correctly in Excel
- [ ] **TESTED**: Color coding logic handles edge cases correctly

### **Task 2.4: Enhanced CLI Export Command**
**Objective**: Integrate with existing CLI system

```bash
# New command implementation required:
poetry run leadscout jobs export-for-confirmation <job-id> --output leads_for_dialler.xlsx
```

**Success Criteria**:
- [ ] New CLI command `export-for-confirmation` implemented
- [ ] Integration with existing job management system
- [ ] Output path generation with timestamp if not specified
- [ ] Support for both Excel and CSV formats
- [ ] **VERIFIED**: Command executes successfully via Poetry
- [ ] **TESTED**: Generated files contain all required columns and formatting

## 🔄 **PHASE 3: Confirmation Upload System (Week 3)**

### **Task 3.1: CLI Confirmation Commands**
**Objective**: Complete CLI suite for confirmation management

```bash
# Implementation required:
poetry run leadscout ethnicity upload-confirmations --file confirmed_leads.xlsx --job-id <job-id>
poetry run leadscout ethnicity confirm --job-id <job-id> --row-number 25 --ethnicity "African"
poetry run leadscout ethnicity bulk-confirm --csv confirmations.csv
poetry run leadscout ethnicity status <job-id>
```

**Success Criteria**:
- [ ] All 4 CLI commands implemented following existing Click patterns
- [ ] Comprehensive help text for all commands
- [ ] Progress indicators for long-running operations
- [ ] **VERIFIED**: All commands execute via Poetry without errors
- [ ] **TESTED**: Each command performs its intended function correctly

### **Task 3.2: Excel Upload Validation System**
**Objective**: Robust validation for confirmation uploads

```python
class EthnicityConfirmationUploader:
    """Handle confirmation uploads with strict validation."""
    
    async def upload_confirmations_from_excel(self, file_path, job_id):
        # Implementation required: Comprehensive validation
```

**Success Criteria**:
- [ ] Excel file validation (required columns, data types)
- [ ] Ethnicity validation against canonical list
- [ ] Row-by-row error reporting with specific messages
- [ ] Bulk processing with transaction safety
- [ ] **VERIFIED**: Invalid files properly rejected with clear error messages
- [ ] **TESTED**: Valid confirmations uploaded successfully to database

### **Task 3.3: Confirmation Database Operations**
**Objective**: Efficient database operations for confirmations

**Success Criteria**:
- [ ] Confirmation record storage with proper indexing
- [ ] Bulk update operations for performance
- [ ] Duplicate handling and conflict resolution
- [ ] **VERIFIED**: Database operations maintain integrity
- [ ] **TESTED**: High-volume confirmation uploads perform adequately

### **Task 3.4: Status and Analytics Commands**
**Objective**: Visibility into confirmation lifecycle

**Success Criteria**:
- [ ] Job confirmation status reporting
- [ ] Statistics on confirmation rates and coverage
- [ ] Integration with existing analytics patterns
- [ ] **VERIFIED**: Status commands provide accurate information
- [ ] **TESTED**: Analytics calculations are mathematically correct

## 🎯 **Integration Requirements**

### **With Existing Systems**
- [ ] **Job Processing**: Seamless integration with existing job framework
- [ ] **Export System**: Enhancement of existing export functionality
- [ ] **CLI System**: Consistent with existing command patterns
- [ ] **Database**: Proper foreign key relationships and indexing

### **With Developer B's Work**
- [ ] **Learning Integration**: Provide confirmed data for spatial learning
- [ ] **Address Integration**: Support address canonicalization for spatial context
- [ ] **Shared Patterns**: Consistent learning database patterns

## 🧪 **Testing & Validation Requirements**

### **Unit Testing**
- [ ] Database schema validation tests
- [ ] File identifier generation tests
- [ ] Excel export formatting tests
- [ ] CLI command functionality tests

### **Integration Testing**
- [ ] End-to-end job processing with confirmation support
- [ ] Excel export → confirmation upload → learning integration
- [ ] CLI command integration with existing system

### **Performance Testing**
- [ ] Large file export performance (10K+ leads)
- [ ] Bulk confirmation upload performance
- [ ] Database query optimization validation

### **Business Validation**
- [ ] Dialler team workflow testing with actual Excel files
- [ ] Confirmation upload process validation
- [ ] Excel dropdown functionality in production environment

## 📊 **Success Metrics & Acceptance Criteria**

### **Technical Success**
- ✅ **100% Record Traceability**: Every ethnicity links to exact source row
- ✅ **95%+ Export Success Rate**: Reliable Excel generation with all formatting
- ✅ **95%+ Upload Success Rate**: Robust confirmation validation and processing
- ✅ **Zero Breaking Changes**: Existing functionality unaffected

### **Business Success**
- ✅ **Dialler Team Efficiency**: Clean Excel files with AI predictions + confirmation dropdowns
- ✅ **Zero Manual Lookup**: All context available in Excel file
- ✅ **Data Quality**: Canonical validation prevents invalid entries
- ✅ **Seamless Workflow**: Fits existing job processing pipeline

### **Performance Success**
- ✅ **Export Performance**: <30 seconds for 10K lead export
- ✅ **Upload Performance**: <60 seconds for 1K confirmation upload
- ✅ **Memory Efficiency**: Constant memory usage regardless of file size
- ✅ **Database Performance**: <100ms for typical confirmation queries

## 🚨 **Blockers & Dependencies**

### **Before Starting**
- [ ] Complete all mandatory reading
- [ ] Verify existing codebase understanding
- [ ] Set up development environment with Poetry
- [ ] Validate database access and existing job processing

### **During Development**
- [ ] Coordinate with Developer B on learning integration patterns
- [ ] Validate Excel functionality on target systems
- [ ] Test CLI commands in actual Poetry environment
- [ ] Confirm database schema changes with existing data

## 📋 **Weekly Check-ins & Reporting**

### **Week 1 Report (Database Schema)**
**Required Evidence**:
- Database schema creation scripts executed successfully
- Test data inserted and retrieved correctly
- Integration with existing job processing validated
- Actual test results and database query outputs

### **Week 2 Report (Export System)**
**Required Evidence**:
- Sample Excel file with all 21 columns and formatting
- Dropdown validation working in Excel
- Color coding displaying correctly
- CLI command execution screenshots

### **Week 3 Report (Upload System)**
**Required Evidence**:
- Confirmation upload working end-to-end
- CLI commands functional via Poetry
- Error handling working with invalid data
- Performance metrics for bulk operations

## ⚠️ **Critical Reminders**

1. **NEVER** assume functionality works without testing
2. **ALWAYS** provide concrete test results when reporting progress
3. **MANDATORY** adherence to existing architecture patterns
4. **FORBIDDEN** breaking changes to existing functionality
5. **REQUIRED** comprehensive error handling and validation

## 🆘 **Support & Resources**

- **Technical Questions**: Reference existing codebase patterns
- **Architecture Decisions**: Consult CLAUDE.md and system design docs
- **Code Quality**: Follow CLAUDE_RULES.md exactly
- **Integration Issues**: Coordinate with Project Manager for Developer B integration

---

**Assignment Status**: Ready for Implementation  
**Success Pattern**: Build on proven job processing + export patterns  
**Business Impact**: Critical - Immediate dialler team workflow improvement