---
slug: <slug>
status: draft
spec_source: spec-driven/<slug>/spec.md
spec_tier: 1 | 2
spec_hash: sha256:<hash of spec.md>
adaptive_flow: rich | partial | minimal
test_approach: tdd | test-after | none
test_capabilities:
  unit: <framework or null>
  integration: <framework or null>
  e2e: <framework or null>
created_date: <ISO8601>
last_updated: <ISO8601>
projects:  # if multi-project, inherited from spec
  - name: <name>
    identity: <host/org/repo>
artifact_home: <project-name>  # if multi-project
---

<!-- Lines beginning with > are generation guidance — do not include them in the output artifact. -->

# Architectural Design: <slug>

## Overview

- **Spec**: [spec name] ([N] FRs, [M] NFRs)
- **Architecture**: [new | extension | refactor]
- **Test approach**: [tdd | test-after | none] [source annotation]
- **Test capabilities**: unit=[framework or null], integration=[framework or null], e2e=[framework or null] [recommendations for gaps if applicable]

## Technical Approach

Per-feature-area summary of the chosen technical direction. For each major feature area:
- What exists in the codebase today
- What changes are needed
- The chosen approach (references the AD-N that formalized this choice)
- Key patterns to follow (with file path references)

> This section is the narrative that ties findings and architecture decisions into a coherent story. The task skill reads this to understand the overall direction before decomposing into steps. Write this section in full — it IS the summary.

## Findings

> Summary table only — full finding content is in `references/research.md`.

| ID | Title | Source | Confidence | Related FRs | Summary |
| --- | --- | --- | --- | --- | --- |
| F-1 | [Brief title] | codebase | high | FR-N, FR-M | [One sentence — what was discovered and why it matters] |

## Architecture Decisions

> Write each AD in full — the task skill needs complete context for decomposition.

### AD-1: [Title]

- **Context**: [Forces in tension]
- **Decision**: We will [chosen approach]
- **Rationale**: [Why — references F-N findings]
- **Alternatives Considered**: [What was rejected and why]

### AD-2: ...

## Resolved Uncertainties

> Question and answer only — supporting evidence is in `references/research.md`.

| # | Question | Answer |
| --- | --- | --- |
| 1 | [Technical question] | [What was determined] |

## Standards

> Top standards most relevant to this design. The complete inventory of all N standards with full typed applicability metadata is in `references/standards.md`.

| ID | Rule | Domain | File Type | Action Type |
| --- | --- | --- | --- | --- |
| S-1 | [Rule statement] | [domain] | [.ext] | [create/modify/*] |

## File Inventory

| Action | Path | Related FRs | Rationale |
| --- | --- | --- | --- |
| create | path/to/file | FR-N | [reason] |
| modify | path/to/file | FR-N | [reason] |

## Dependencies and Coupling

> Features that share files or interfaces. Recommendations for the task skill on sequencing and shared structure.

| Feature Area | Shared Files | Recommendation |
| --- | --- | --- |
| [FR-1, FR-3] | `src/models/user.ts`, `src/routes/index.ts` | [e.g., "Hoist shared model into walking skeleton"] |

## Spec Deviations

Values or constraints from the spec that this design changes or reinterprets. If no deviations exist, write "None — all spec values preserved."

| Spec Value | Location | Design Value | Rationale |
| --- | --- | --- | --- |
| [original value] | [AC-N.M or NFR-N] | [new value] | [why the change is warranted] |

> An empty table with no "None" declaration is a gap — it means deviations were not checked.

## Open Questions

[Carried from spec, with confirmed defaults or new questions from research]

## Constraints (Technical)

> Each constraint: category, source, and rationale. Supplements spec-stage constraints.

| Constraint | Category | Source | Rationale |
| --- | --- | --- | --- |
| [constraint description] | [infrastructure / security / performance / compatibility] | [codebase / technical / company-adr] | [why this limits available options] |

## Assumptions

> Each assumption: source and affected FRs. Supplements spec-stage assumptions.

| Assumption | Source | Affects |
| --- | --- | --- |
| [assumption description] | [design / research / codebase] | [FR-N, FR-M] |

## Risks (Technical)

> Each risk: impact, probability, mitigation, and affected FRs. Supplements spec-stage risks.

| Risk | Impact | Probability | Mitigation | Affects |
| --- | --- | --- | --- | --- |
| [risk description] | [high / medium / low] | [high / medium / low] | [mitigation strategy] | [FR-N, FR-M] |

## References

- See `references/research.md` for full research results per aspect
- See `references/standards.md` for complete standards inventory ([N] standards)
- See `references/contracts.md` for API contract definitions (if applicable)
