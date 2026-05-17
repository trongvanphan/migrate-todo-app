# Specification: [Spec Name]

> Date: [Date]
> Version: 1.0
> Location: spec-driven/[spec-slug]/spec.md
> Tracking: [Rally ID / link, or "N/A"]
> Source: [How this spec was created — e.g., "Interactive elicitation", "Draft from PRD (docs/prd.md)", "Rally import (E123) + elicitation"]

> **Provenance Key**: Content sources are marked inline:
> - **[User]** — Directly stated by the user
> - **[Rally]** — Imported from Rally data
> - **[Inferred]** — Synthesized by the agent from available context
> - **[Default]** — Standard default applied
> - **[Codebase]** — Derived from codebase analysis

<!-- Multi-project workspace support (optional — omit entire section for single-project specs).
     When present, all downstream artifacts (plan, tasks, progress) inherit this block.
     When absent, single-project mode applies — full backward compatibility.

     Schema:
     - name: logical short name, used as qualifier in file paths (e.g., auth-service::src/auth.ts).
       Must match [a-z0-9-]+. Must be unique. Must not contain ::.
     - identity: repo remote URL for portable resolution. Format: hostname/org/repo
       (no protocol prefix, no .git suffix). Use "local" for non-git directories.
     - artifact_home: which project hosts the spec-driven/ directory.
       Defaults to the primary working directory's project if omitted.

     Render as a ## Projects heading with a YAML code fence when multi-project:
-->
<!--
## Projects

```yaml
projects:
  - name: auth-service
    identity: ghe.coxautoinc.com/org/auth-service
  - name: client-sdk
    identity: ghe.coxautoinc.com/org/client-sdk
artifact_home: auth-service
```
-->

## Project Context

**Parent Project**: See `CLAUDE.md` for project-wide principles and patterns. **[Codebase]**

**Scope**: This specification defines requirements for a single feature or capability. Each spec is kept bounded and context-efficient. **[User]**

## Overview

[2-3 paragraph summary of what's being built and why. Include the problem being solved, the target users, and the expected business value.] **[Rally]**

### Current State
[What exists today — the baseline this feature changes. If greenfield, state "No existing system."
Include: current tools/processes being used, current pain points, current workarounds.] **[Codebase]**

## Goals

### Primary Goal
[Main objective this feature achieves] **[Rally]**

### Secondary Goals
1. [Secondary goal 1] **[Rally]**
2. [Secondary goal 2] **[Inferred]**

### Non-Goals (Explicitly Out of Scope)
- [What this feature will NOT do] **[User]**
- [Future work that's not part of this release] **[Inferred]**

## Users

### Primary Users
| User Type | Description | Goals | Pain Points |
|-----------|-------------|-------|-------------|
| [User Type] | [Who they are] | [What they want] | [Current frustrations] |

### Secondary Users
| User Type | Description | Goals | Pain Points |
|-----------|-------------|-------|-------------|
| [User Type] | [Who they are] | [What they want] | [Current frustrations] |

## Functional Requirements

### FR-1: [Requirement Title]

**Description**: [What the system must do] **[Rally]**

**User Story**: As a [user type], I want [capability] so that [benefit].

**Acceptance Criteria**:

| ID | Criterion | Given | When | Then |
|----|-----------|-------|------|------|
| AC-1.1 | [Name] | [Precondition] | [Action] | [Expected outcome] **[Rally]** |
| AC-1.2 | [Name] | [Precondition] | [Action] | [Expected outcome] **[Inferred]** |

**Priority**: [Must Have | Should Have | Nice to Have]

**Goal**: [Primary | Secondary-N | TBD]

**Dependencies**: [Other FRs this depends on, or "None"]

---

### FR-2: [Requirement Title]

**Description**: [What the system must do] **[User]**

**User Story**: As a [user type], I want [capability] so that [benefit].

**Acceptance Criteria**:

| ID | Criterion | Given | When | Then |
|----|-----------|-------|------|------|
| AC-2.1 | [Name] | [Precondition] | [Action] | [Expected outcome] **[User]** |
| AC-2.2 | [Name] | [Precondition] | [Action] | [Expected outcome] **[Codebase]** |

**Priority**: [Must Have | Should Have | Nice to Have]

**Goal**: [Primary | Secondary-N | TBD]

**Dependencies**: [Other FRs this depends on, or "None"]

---

### FR-3: [Requirement Title]

[Continue pattern for all functional requirements]

---

## Non-Functional Requirements

### NFR-1: [Performance Requirement]

**Category**: Performance

**Description**: [What quality attribute is required]

**Metric**: [How we measure compliance]

**Target**: [Specific measurable target]

**Verification**: [How we test this]

---

### NFR-2: [Security Requirement]

**Category**: Security

**Description**: [What quality attribute is required]

**Metric**: [How we measure compliance]

**Target**: [Specific measurable target]

**Verification**: [How we test this]

---

### NFR-3: [Reliability Requirement]

**Category**: Reliability

**Description**: [What quality attribute is required]

**Metric**: [How we measure compliance]

**Target**: [Specific measurable target]

**Verification**: [How we test this]

---

### NFR-4: [Cost Requirement]

**Category**: Cost

**Description**: [What quality attribute is required]

**Metric**: [How we measure compliance]

**Target**: [Specific measurable target]

**Verification**: [How we test this]

---

### NFR-5: [Operability Requirement]

**Category**: Operability

**Description**: [What quality attribute is required]

**Metric**: [How we measure compliance]

**Target**: [Specific measurable target]

**Verification**: [How we test this]

---

### NFR-6: [Additional Quality Requirement]

[Continue pattern for all non-functional requirements]

---

## Scope

### In Scope
- [Explicitly included functionality]
- [Explicitly included functionality]
- [Explicitly included functionality]

### Out of Scope
- [Explicitly excluded - may be future work]
- [Explicitly excluded - not this project]
- [Explicitly excluded - handled elsewhere]

### Constraints
- [Hard boundary — non-negotiable requirement, e.g., "Must comply with GDPR"]
- [Technical constraint — e.g., "Must integrate with existing PostgreSQL database"]
- [Organizational constraint — e.g., "Must be deployable by Platform team"]

### Assumptions
- [What we're assuming to be true]
- [Dependencies on external systems]
- [User behavior assumptions]

### Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| [Risk 1] | [High/Medium/Low] | [High/Medium/Low] | [Strategy] |
| [Risk 2] | [High/Medium/Low] | [High/Medium/Low] | [Strategy] |

## Success Metrics

### Primary Metrics
| Metric | Current Baseline | Target | Measurement Method |
|--------|------------------|--------|-------------------|
| [Metric 1] | [Baseline or N/A] | [Goal] | [How measured] |
| [Metric 2] | [Baseline or N/A] | [Goal] | [How measured] |

### Secondary Metrics
| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| [Metric 3] | [Goal] | [How measured] |

## Dependencies

### External Systems
- [External API or service dependencies]

### Internal Dependencies
- [Other features or teams this depends on]

### Data Dependencies
- [Required data sources or migrations]


## Open Questions

> Questions that need stakeholder input before implementation

1. [Unresolved question 1]
2. [Unresolved question 2]
3. [Unresolved question 3]

## Agent Decisions

> Decisions made by the agent during elicitation. Review these — they represent assumptions that may need validation.

| # | Decision | Context | Rationale | Affects |
|---|----------|---------|-----------|---------|
| 1 | [What was decided] | [Why a decision was needed] | [Why this choice] | [Which FRs/sections] |
