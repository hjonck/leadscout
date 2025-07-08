# Developer Assignment Handoff Instructions

**Date**: January 2025  
**Project Manager**: Current Claude Session  
**Assignment Status**: Ready for Developer Handoff  

## 🎯 **Assignment Summary**

Two critical epics ready for immediate developer assignment:

- **Epic 1**: Ethnicity Confirmation System → **Developer A** (Job Processing Specialist)
- **Epic 2**: Enhanced Classification & Address Cleaning → **Developer B** (Classification Specialist)

## 📋 **Developer A Assignment - Epic 1**

### **Assignment Document**
**File**: `dev-tasks/EPIC_1_DEVELOPER_A_ASSIGNMENT.md`

### **Handoff Prompt for Developer A**
```
You have been assigned as Developer A for LeadScout's Epic 1: Ethnicity Confirmation System.

CRITICAL: Before starting any development work, you must:

1. READ the condensed rules first: docs/CLAUDE_RULES_CONDENSED.md (4 pages - essential for immediate productivity)

2. READ your complete assignment: dev-tasks/EPIC_1_DEVELOPER_A_ASSIGNMENT.md (comprehensive specifications)

3. READ the design specification: docs/design/ethnicity-confirmation-system.md

4. VALIDATE your understanding of the existing codebase by exploring src/leadscout/core/job_database.py and src/leadscout/cli/ patterns

Your mission: Implement complete ethnicity confirmation lifecycle with precise record tracing. Enable dialler team workflow with enriched Excel files containing AI predictions + empty confirmation dropdown columns.

Timeline: 3 weeks (Phases 1-3)
Business Priority: CRITICAL - Immediate dialler team workflow requirement

Key Success Criteria:
- 100% record traceability (every ethnicity links to exact source row)
- 95%+ export success rate with professional Excel formatting
- 95%+ upload success rate with robust validation
- Dialler team workflow ready with AI predictions + confirmation dropdowns

REMEMBER: NEVER assume anything works without testing. Provide actual test results when reporting progress.

Are you ready to begin? Please confirm you understand the assignment scope and timeline.
```

## 📋 **Developer B Assignment - Epic 2**

### **Assignment Document**
**File**: `dev-tasks/EPIC_2_DEVELOPER_B_ASSIGNMENT.md`

### **Handoff Prompt for Developer B**
```
You have been assigned as Developer B for LeadScout's Epic 2: Enhanced Classification & Address Cleaning.

CRITICAL: Before starting any development work, you must:

1. READ the condensed rules first: docs/CLAUDE_RULES_CONDENSED.md (4 pages - essential for immediate productivity)

2. READ your complete assignment: dev-tasks/EPIC_2_DEVELOPER_B_ASSIGNMENT.md (comprehensive specifications)

3. READ the design specifications: 
   - docs/design/ethnicity-confirmation-system.md (for learning integration)
   - docs/design/address-cleaning-system.md (for address cleaning architecture)

4. VALIDATE your understanding of the existing classification system by exploring src/leadscout/classification/ and src/leadscout/classification/learning_database.py

Your mission: Enhance ethnicity prediction through spatial learning from human confirmations AND implement foundational address cleaning using proven multi-layered classification approach.

Timeline: 4 weeks (includes Epic 1 integration + Epic 2 foundation)
Business Priority: HIGH - Enhances Epic 1 effectiveness + builds future capability

Key Success Criteria:
- 20%+ ethnicity accuracy improvement through confirmed spatial patterns
- 95%+ address component extraction from raw SA addresses
- <100ms processing time maintained
- Learning foundation ready for future LLM integration

Integration with Developer A: You will leverage confirmation data from Epic 1 for spatial learning enhancement.

REMEMBER: Follow the proven multi-layered classification approach that achieved 68.6% cost efficiency.

Are you ready to begin? Please confirm you understand the assignment scope and integration requirements.
```

## 🔄 **Coordination Protocol**

### **Daily Sync Protocol** (10 minutes each morning)
**Format**: 
- Progress update from both developers
- Blocker identification and resolution
- Coordination point validation
- Next-day dependency confirmation

### **Integration Checkpoints**
**Week 1 Day 3**: Confirmation database schema must be completed for Developer B integration  
**Week 2 Day 10**: Export format and address processing integration validation  
**Week 3 Day 17**: End-to-end confirmation → spatial learning workflow validation

### **Weekly Validation Meetings**
**Week 1**: Database schemas and basic integration patterns  
**Week 2**: Export functionality and address processing validation  
**Week 3**: Full workflow integration and performance testing  
**Week 4**: Business validation and production readiness

## 📊 **Project Manager Oversight**

### **Daily Monitoring**
- Track progress against weekly milestones
- Identify and resolve integration blockers
- Validate adherence to architecture patterns
- Ensure testing and verification requirements met

### **Weekly Business Reporting**
- Demonstrate functional progress to stakeholders
- Validate business workflow requirements
- Adjust timeline or scope as needed
- Coordinate business validation testing

### **Success Validation**
- Ensure all success criteria met with evidence
- Validate integration between both epics
- Confirm production readiness
- Coordinate deployment planning

## 🚨 **Critical Success Factors**

### **For Both Developers**
1. **NEVER assume functionality works** without testing and verification
2. **ALWAYS provide concrete test results** when reporting progress
3. **MANDATORY adherence** to existing architecture patterns
4. **REQUIRED coordination** on integration points
5. **FORBIDDEN breaking changes** to existing functionality

### **For Developer A (Epic 1)**
- Focus on immediate business value delivery
- Excel functionality must work in production environment
- Confirmation upload system must be robust and reliable
- Integration with existing job processing must be seamless

### **For Developer B (Epic 2)**
- Build on proven classification success patterns
- Maintain existing performance standards
- Provide spatial learning foundation for Epic 1
- Prepare framework for future LLM cost optimization

## 📋 **Assignment Checklist**

### **Before Assignment**
- [x] Comprehensive developer assignments written
- [x] Success criteria clearly defined
- [x] Integration coordination protocol established
- [x] Condensed rules document created for efficiency
- [x] Project manager tracking framework established

### **During Assignment**
- [ ] Developer A confirms understanding and begins Epic 1
- [ ] Developer B confirms understanding and begins Epic 2
- [ ] Daily coordination protocol implemented
- [ ] Weekly validation meetings scheduled
- [ ] Progress tracking and reporting active

### **Assignment Completion**
- [ ] All success criteria met with evidence
- [ ] Integration between epics validated
- [ ] Business workflow testing completed
- [ ] Production readiness confirmed
- [ ] Deployment planning coordinated

---

**Status**: Ready for Developer Assignment  
**Next Step**: Prompt each developer with their specific assignment  
**Success Pattern**: Multi-Claude specialization with proven architecture leverage  
**Business Impact**: Critical workflow improvement + enhanced spatial intelligence foundation