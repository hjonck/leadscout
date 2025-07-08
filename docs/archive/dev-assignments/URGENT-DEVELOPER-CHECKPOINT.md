# 🚨 URGENT: Developer Checkpoint - Rules Compliance Verification

## STOP ALL CURRENT WORK

**Before continuing any development, you MUST complete this checkpoint to ensure you're following project rules.**

## WHY THIS IS CRITICAL

You may have started working without following our mandatory initialization checklist. This could result in:
- Architecture violations that break integration
- Code that doesn't meet quality standards
- Environment setup issues
- Missing context that leads to wrong implementation choices

## MANDATORY CHECKPOINT ACTIONS

### 1. STOP Current Work
- Commit any work in progress with message: "WIP: checkpoint before rules validation"
- Do NOT continue development until this checkpoint is complete

### 2. Read ALL Core Project Files (MANDATORY)
```bash
cd /Users/hjonck/Development/gitprojects/AgileWorksZA/leadscout

# REQUIRED READING (in order):
Read CLAUDE.md                    # Complete project overview and context
Read CLAUDE_RULES.md              # NON-NEGOTIABLE development rules  
Read PROJECT_PLAN.md              # Current status and your role
```

### 3. Environment Validation
```bash
# Verify you're using the correct environment
source .venv/bin/activate
python --version                 # Must be 3.11+
which python                     # Must be in .venv directory
poetry --version                 # Must be available
```

### 4. Architecture Compliance Check
Review your current work against these NON-NEGOTIABLE rules:

**Code Quality (MANDATORY):**
- [ ] All functions have complete type hints
- [ ] All functions have Google-style docstrings  
- [ ] All code uses async patterns for I/O operations
- [ ] No hardcoded credentials or sensitive data
- [ ] All imports follow the established order (stdlib, third-party, local)

**Environment Rules (MANDATORY):**
- [ ] All Python commands use `source .venv/bin/activate &&` prefix
- [ ] No global package installations
- [ ] Poetry used for all dependency management

**Architecture Rules (MANDATORY):**
- [ ] Following established package structure in src/leadscout/
- [ ] Using established data models and patterns
- [ ] Implementing proper error handling with custom exceptions
- [ ] Following async patterns throughout

### 5. Quality Gates Validation
```bash
# Run these checks on your current code:
source .venv/bin/activate

# Type checking
mypy src/leadscout/

# Code formatting  
black --check src/
isort --check-only src/

# Linting
flake8 src/

# Tests (if you've created any)
pytest --version
```

## COMPLIANCE REPORT REQUIRED

Create `dev-tasks/[your-role]-compliance-report.md` with:

```markdown
# [Developer A/B] Rules Compliance Report

## Checkpoint Status
- [ ] Read CLAUDE.md completely
- [ ] Read CLAUDE_RULES.md completely  
- [ ] Read PROJECT_PLAN.md completely
- [ ] Environment setup validated
- [ ] Architecture rules reviewed

## Current Work Review
**Files I've created/modified:**
- [List all files you've touched]

**Architecture Compliance:**
- [ ] Type hints on all functions: ✅ PASS / ❌ FAIL / 🔄 PARTIAL
- [ ] Google docstrings: ✅ PASS / ❌ FAIL / 🔄 PARTIAL
- [ ] Async patterns: ✅ PASS / ❌ FAIL / 🔄 PARTIAL
- [ ] Package structure: ✅ PASS / ❌ FAIL / 🔄 PARTIAL
- [ ] Error handling: ✅ PASS / ❌ FAIL / 🔄 PARTIAL

**Quality Gates:**
- [ ] mypy: ✅ PASS / ❌ FAIL
- [ ] black: ✅ PASS / ❌ FAIL  
- [ ] isort: ✅ PASS / ❌ FAIL
- [ ] flake8: ✅ PASS / ❌ FAIL

**Environment Compliance:**
- [ ] Using .venv: ✅ YES / ❌ NO
- [ ] Poetry for dependencies: ✅ YES / ❌ NO
- [ ] No global installs: ✅ YES / ❌ NO

## Issues Found
[List any rules violations you discovered]

## Fixes Applied
[List what you fixed to comply with rules]

## Architecture Understanding
**My role in the system:**
[Demonstrate you understand your role and integration points]

**Key APIs I provide/consume:**
[Show you understand the integration requirements]

## Ready to Continue
✅ I have read all rules and my code complies
❌ I need to fix violations before continuing

## Questions/Clarifications Needed
[Any questions about rules or architecture]
```

## WHAT HAPPENS NEXT

1. **If you're compliant**: Continue with your original assignment
2. **If you have violations**: Fix them before continuing
3. **If you have questions**: Document them in your compliance report

## TIMELINE

Complete this checkpoint immediately before any further development.

---

**This checkpoint ensures we maintain code quality and architectural integrity. It's not optional.**