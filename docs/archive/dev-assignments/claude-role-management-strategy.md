# Claude Role Management Strategy

## Overview

This document defines the optimal strategy for managing multiple Claude Code sessions across different roles in the LeadScout project. It establishes clear role boundaries, communication protocols, and session management practices.

## Role Definitions

### 1. Technical Project Lead & Lead Architect
**Responsibilities:**
- Overall project architecture and technical direction
- Coordination between Developer A and Developer B
- Quality assurance and code review
- Research coordination and decision making
- PROJECT_PLAN.md maintenance and milestone tracking
- Integration validation and system-wide optimization

**Session Characteristics:**
- Longest sessions with deepest project context
- Architectural decision-making authority
- Cross-cutting concerns and system integration
- Research validation and technical decisions

### 2. Developer A: CIPC Integration & Caching Specialist
**Responsibilities:**
- CIPC data integration and processing
- Multi-tier caching architecture (Redis + PostgreSQL)
- Database schema design and optimization
- Company search engine implementation
- Performance optimization for data layer
- API design for Developer B integration

**Session Characteristics:**
- Deep technical focus on data infrastructure
- Performance and scalability optimization
- Database and caching expertise
- API provider role in the architecture

### 3. Developer B: Name Classification & Enrichment Specialist
**Responsibilities:**
- Multi-layered name classification system
- South African cultural context and name patterns
- LLM integration and cost optimization
- Lead enrichment pipeline (website, LinkedIn, contacts)
- Scoring engine and business logic
- AI/ML algorithm implementation

**Session Characteristics:**
- Deep technical focus on AI/ML systems
- Cultural sensitivity and domain expertise
- Algorithm optimization and accuracy tuning
- Business logic and scoring implementation

### 4. Research Specialist (Optional)
**Responsibilities:**
- Investigate unknowns and validate approaches
- External service evaluation and testing
- Cost-benefit analysis of different solutions
- Technical feasibility research
- API integration testing and validation

**Session Characteristics:**
- Research-focused with investigation deliverables
- External service testing and evaluation
- Documentation of findings and recommendations
- Short-term focused sessions with specific outcomes

## Session Management Best Practices

### 1. Session Initialization Protocol

#### For Technical Project Lead
```bash
# Standard initialization sequence
cd /Users/hjonck/Development/gitprojects/AgileWorksZA/leadscout
source .venv/bin/activate

# Read core context files
Read CLAUDE.md                    # Role and project overview
Read PROJECT_PLAN.md              # Current status and priorities
Read CLAUDE_RULES.md              # Development standards
git log --oneline -10            # Recent changes
git status                       # Current state

# Check developer progress
ls dev-tasks/                    # Review assignments
grep -r "status.*completed" dev-tasks/ # Check completion status
grep -r "blocker\|blocked\|issue" dev-tasks/ # Check for problems
```

#### For Developer A
```bash
# Use the initialization prompt
Read dev-tasks/developer-a-initialization-prompt.md
# Follow the complete checklist in that file
```

#### For Developer B
```bash
# Use the initialization prompt
Read dev-tasks/developer-b-initialization-prompt.md
# Follow the complete checklist in that file
```

#### For Research Specialist
```bash
# Read research assignment
Read dev-tasks/research-and-development.md
Read dev-tasks/research-assignment-[topic].md  # Specific assignment
# Focus on assigned research area
```

### 2. Communication Protocols

#### Progress Reporting (All Roles)
1. **Immediate Updates**: Update PROJECT_PLAN.md when completing tasks
2. **Commit Messages**: Use descriptive conventional commit format
3. **Status Files**: Create status update files in dev-tasks/ for blockers
4. **Integration Points**: Document API changes immediately

#### Coordination Between Developers
```bash
# Developer A → Developer B communication
dev-tasks/developer-a-status.md        # Current progress and API availability
dev-tasks/developer-a-api-docs.md      # API specifications and examples

# Developer B → Developer A communication  
dev-tasks/developer-b-status.md        # Current progress and integration needs
dev-tasks/developer-b-requirements.md  # API requirements and SLA needs

# Technical Project Lead coordination
dev-tasks/integration-status.md        # Overall integration progress
dev-tasks/next-priorities.md          # Immediate next steps
```

#### Escalation Protocol
1. **Technical Blockers**: Document in dev-tasks/blockers-[role].md
2. **Integration Issues**: Escalate to Technical Project Lead immediately
3. **Architecture Questions**: Require Technical Project Lead decision
4. **Performance Issues**: Require cross-team coordination

### 3. Quality Assurance & Integration

#### Developer Handoff to Technical Project Lead
```markdown
## Handoff Checklist for [Developer Role]
- [ ] All assigned tasks completed per PROJECT_PLAN.md
- [ ] Code passes all quality gates (tests, typing, formatting)
- [ ] Performance targets met and benchmarked
- [ ] Integration tests passing with realistic data
- [ ] API documentation complete and tested
- [ ] No known blockers or technical debt
- [ ] Commit messages follow conventional format
- [ ] PROJECT_PLAN.md updated with completion status
```

#### Technical Project Lead Validation
```bash
# Code quality validation
source .venv/bin/activate
poetry run pytest --cov=leadscout     # Test coverage
poetry run mypy src/                  # Type checking
poetry run black --check src/         # Code formatting
poetry run isort --check-only src/    # Import organization

# Architecture validation
Read src/leadscout/[module]/          # Review code structure
Check API contracts and interfaces    # Validate integration points
Test performance benchmarks          # Verify SLA compliance
Review error handling patterns       # Ensure robustness
```

## Role Transition Strategies

### 1. Planned Handoffs
**Technical Project Lead → Developer A/B:**
- Create detailed task assignment in dev-tasks/
- Ensure all context files are current
- Provide clear acceptance criteria
- Set integration milestones and deadlines

**Developer A/B → Technical Project Lead:**
- Complete handoff checklist thoroughly
- Update all documentation and status files
- Commit all work with descriptive messages
- Document any architectural decisions made

### 2. Emergency Handoffs
**Mid-session transitions:**
- Create emergency handoff file: dev-tasks/emergency-handoff-[timestamp].md
- Document current working state and immediate context
- List any incomplete work and next steps
- Provide debugging context for any current issues

### 3. Role Substitution
**If primary role holder unavailable:**
- Any Claude session can read initialization prompt for role
- Follow complete session initialization protocol
- Prioritize communication with Technical Project Lead
- Err on side of caution for architectural decisions

## Optimal Session Patterns

### 1. Technical Project Lead Sessions
**Recommended Session Length**: 2-4 hours
**Optimal Frequency**: Daily coordination, architectural decisions as needed
**Focus Areas**: 
- Cross-cutting concerns and integration
- Research review and decision making
- Quality assurance and code review
- Project planning and milestone tracking

### 2. Developer Sessions  
**Recommended Session Length**: 3-6 hours for deep technical work
**Optimal Frequency**: Daily development progress, as assigned
**Focus Areas**:
- Deep technical implementation in specialized area
- Performance optimization and testing
- API development and documentation
- Integration with partner developer

### 3. Research Sessions
**Recommended Session Length**: 1-3 hours for focused investigation
**Optimal Frequency**: As assigned by Technical Project Lead
**Focus Areas**:
- Specific research question investigation
- External service evaluation and testing
- Technical feasibility analysis
- Documentation of findings and recommendations

## Session Context Management

### 1. Context Preservation
**Essential Files for Session Continuity:**
- CLAUDE.md (role definition and project overview)
- PROJECT_PLAN.md (current status and priorities)
- dev-tasks/[role]-status.md (role-specific progress)
- Recent git commits (technical context)
- Integration status files (coordination context)

### 2. Context Handoff
**Between sessions of same role:**
- Update PROJECT_PLAN.md with completed tasks
- Document current working state in status files
- Commit all work with descriptive messages
- Note any pending decisions or blockers

**Between different roles:**
- Create role-specific handoff documentation
- Update shared status files and project plan
- Ensure clean git state with committed work
- Provide integration status and next steps

### 3. Context Recovery
**Starting sessions with incomplete context:**
- Follow complete initialization protocol for role
- Review all recent commits and changes
- Check for any emergency handoff documentation
- Validate current state against PROJECT_PLAN.md
- Contact Technical Project Lead for clarification if needed

## Coordination Optimization

### 1. Minimize Communication Overhead
- Use structured markdown files for all coordination
- Avoid real-time communication dependencies
- Document all decisions and context in version-controlled files
- Maintain clear role boundaries to reduce coordination needs

### 2. Maximize Parallel Development
- Ensure clean API contracts between Developer A and B
- Use mock implementations during development
- Maintain independent development environments
- Plan integration points to minimize blocking dependencies

### 3. Maintain Quality Standards
- Enforce consistent coding standards across all roles
- Require Technical Project Lead validation for integration
- Use automated testing and quality gates
- Document architectural decisions and rationale

This role management strategy enables efficient coordination while maintaining the specialized expertise benefits of role separation. The key is clear communication through documentation and structured handoff processes.