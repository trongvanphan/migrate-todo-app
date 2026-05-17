# Design Guide

Detailed guidance for the design skill. Referenced from [SKILL.md](../SKILL.md).

---

## Three-Tier Spec Input Model

The design skill handles input at three fidelity levels. Detection runs during Phase 0.

### Tier 1: Native Spec

**Detection**: The input contains `FR-N` identifiers (e.g., `FR-1`, `FR-2`) and `AC-N.M` acceptance criteria (e.g., `AC-1.1`, `AC-2.3`). Typically output from the `spec` skill at `spec-driven/<slug>/spec.md`.

**Behavior**: Use identifiers directly. Finding and Decision references use the exact FR-N and AC-N.M from the spec.

**Frontmatter**: `spec_tier: 1`

### Tier 2: Structured Non-Spec (markdown backend only)

**Detection**: The input contains numbered requirements, structured headings, or organized bullet lists — but no `FR-N`/`AC-N.M` identifiers. Common for PRDs, RFCs, design docs, or meeting notes. This tier applies only when using the markdown backend via `--from`. The graph backend requires a populated spec — redirect to `/spec --from` first.

**Behavior**:

1. Assign synthetic identifiers: `FR-S1`, `FR-S2`, etc. The `S` prefix marks these as auto-generated.
2. For each requirement, derive synthetic ACs where possible: `AC-S1.1`, `AC-S1.2`.
3. Inform the user: "I've assigned synthetic requirement IDs (FR-S1, FR-S2...) since the input doesn't use the FR-N format. These are for traceability within this design."
4. Proceed with design normally.

**Frontmatter**: `spec_tier: 2`

### Tier 3: Unstructured

**Detection**: Free-form text with no detectable requirements structure — e.g., a Slack message, rough notes, or a paragraph description.

**Behavior**: Do not attempt to extract requirements. Redirect to the spec skill:

> "This input doesn't contain structured requirements that I can design against. Run `/sds.spec --from <this-file>` to create a spec first, then run the design skill on the output."

---

## Test Approach Resolution

Resolve the test approach to one of: `tdd`, `test-after`, `none`. Resolution runs after codebase-analyzer results are consumed. Signals reference subagent output fields (`techStack.testFramework`, `relevantFiles`).

**Detection signals** (checked in order, first match wins):

1. **Explicit user instruction**: User said "use TDD", "test-driven", "write tests first" → `tdd`. User said "test after", "add tests after" → `test-after`. User said "no tests", "skip tests" → `none`.
2. **CLAUDE.md convention**: Any resolved project's CLAUDE.md declares a test approach (e.g., "we use TDD", "always write tests after implementation") → resolve accordingly. Source annotation: `[from CLAUDE.md]`.
3. **Spec NFR signal**: Spec NFR requires test coverage, mentions TDD, or sets coverage targets → `tdd`. Note the source (e.g., `NFR-3`).
4. **Test framework detected, test files exist**: `techStack.testFramework` is non-null AND `relevantFiles` includes test files → `tdd` (recommended default). Source annotation: `[detected: <framework> + existing tests]`.
5. **Test framework detected, no test files**: `techStack.testFramework` is non-null but no test files found in `relevantFiles` → ambiguous. Elicit from user (see below).
6. **No test framework detected** → `none`. Source annotation: `[no test framework]`.

**Elicitation** (signal 5 — ambiguous case only): Before the Research Scope Review, present structured input: "I detected [framework] but found no existing test files. What test approach should this design use?" Options: "TDD (write tests first)" / "Test-after (write tests after implementation)" / "None (skip tests)".

For all other signals, the approach is resolved without asking — the Research Scope Review provides correctability.

### Test Capabilities Detection

After resolving `test_approach`, classify detected test frameworks by their primary level to populate `test_capabilities`. This runs in the same step — it is not a separate phase.

**Detection**: Scan package manifests (`package.json`, `requirements.txt`, `go.mod`, `pom.xml`, `Cargo.toml`) and test directories (`__tests__/`, `tests/`, `e2e/`, `integration/`, `spec/`) from the codebase-analyzer output. Classify each detected framework by its primary test level: unit, integration, or e2e (e.g., Jest is typically unit, Supertest is typically integration, Playwright is typically e2e). When a framework operates at multiple levels depending on project convention (e.g., Jest with TestContainers for integration), classify by the project's actual usage — check existing test file locations and patterns.

Record in design frontmatter:

```yaml
test_capabilities:
  unit: jest       # framework name or null
  integration: supertest  # or null
  e2e: null        # or null
```

**Gap-aware recommendation**: For each level where no framework is detected, cross-reference against the architecture to determine if that level matters. The heuristic is the same at every level: do the FRs or ADs describe behavior whose natural verification level matches the gap?

- **Unit null** + FRs with algorithmic, validation, or data-transformation logic: recommend. Example note: "No unit test framework detected — FRs involving [specific logic] would benefit from one."
- **Integration null** + FRs crossing component boundaries (database queries, API calls, service interactions): recommend. Example note: "No integration test framework detected — cross-component architecture (AD-N) would benefit from one."
- **E2E null** + full user flows or walking skeleton slices: recommend. Example note: "No e2e framework detected — skeleton verification will fall back to integration level."
- When the architecture does not suggest a need at a given level, null requires no recommendation.

Include recommendations in the design output's Overview section alongside the `test_capabilities` values. These inform the task skill's verify clause level selection — a null with a recommendation signals the gap is meaningful, not incidental.

---

## Research Output Contract

Each research subagent returns a JSON object matching these summary fields. The authoritative schema is in research-subagent-instructions.md — defer to it if discrepancies exist:

| Field | Type | Orchestrator Use |
|---|---|---|
| `aspect` | string | The architectural question investigated |
| `findings[]` | objects (`content`, `source`, `confidence`, `relatedFRs`, `relatedFiles`, `implications`) | Fed into F-N assignment and file inventory |
| `approaches[]` | objects (`name`, `description`, `fit`, `tradeoffs`, `recommendation`, `references`) | Presented at Research Findings gate for user direction |
| `patterns[]` | objects (`name`, `location`, `applicability`) | Merged with codebase-analyzer patternInventory |
| `risks[]` | strings | Categorized as technical risks in step 6 |
| `resolved_uncertainties[]` | objects (`question`, `answer`, `evidence`) | Carried to Resolved Uncertainties section |
| `uncertainties[]` | strings | Surfaced at Research Findings gate |

Subagents return ONLY this JSON. No conversational text.

**Source values**: `codebase` (directly observed in files), `web_research` (found via documentation/article search), `training_knowledge` (model knowledge when search is unavailable), `spec` (derived from the spec document — a known, pre-existing input). Downstream consumers weight confidence accordingly — `web_research` with authoritative documentation gets `high` confidence; `training_knowledge` defaults to `medium` unless the pattern is well-established.

---

## Research Subagent Sizing

| Adaptive Flow | Subagent Count | Guidance |
| --- | --- | --- |
| Rich context | 0 | Codebase-analyzer output is sufficient. Standards extraction runs inline. |
| Partial context | 2-3 | One per major FR cluster or architectural aspect not covered by Phase 0 |
| Minimal context | 3-5 | One per major architectural aspect (e.g., data layer, API layer, auth, state management, integration) |

Derive aspects from FRs and NFRs:
- Group FRs by architectural aspect (auth, data, UI, integration, etc.)
- Each NFR with a non-trivial verification method may warrant its own aspect
- If two FRs share the same architectural aspect, combine them into one aspect

Cap at 5 subagents regardless of FR count. If more aspects exist, prioritize by: Must-Have FRs first, then FRs with external dependencies, then remaining FRs.

---

## Finding Format (F-N)

Each finding is a discrete piece of research output, numbered sequentially.

```markdown
### F-1: [Brief title]

- **Source**: codebase | web_research | training_knowledge | spec
- **Confidence**: high | medium | low
- **Related**: FR-1, FR-3
- **Files**: `src/services/auth.ts`, `src/middleware/jwt.ts`

[Content: what was discovered and its implications for the design. 2-5 sentences.]
```

**ID assignment**: Sequential starting from F-1. Do not skip numbers.

**Confidence levels**:
- `high` — directly observed in codebase or confirmed by documentation
- `medium` — inferred from patterns or partial evidence
- `low` — speculative, based on limited information or inaccessible systems

---

## Architecture Decision Template (AD-N)

```markdown
### AD-1: [Decision Title]

- **Context**: [The forces in tension — competing concerns that make this a real decision]
- **Decision**: [What we will do, stated as "We will..."]
- **Rationale**: [Why this over alternatives — reference the findings (F-N) that informed this]
- **Alternatives Considered**: [What was rejected and why]
```

**When to create an AD:**

- Two or more valid approaches exist and the choice has lasting consequences
- The decision constrains downstream implementation in a way the executor should understand
- The choice involves a trade-off (performance vs. simplicity, consistency vs. flexibility)

**When NOT to create an AD:**

- The choice is obvious from existing codebase patterns
- Only one reasonable approach exists
- The decision is trivially reversible

**ID assignment**: Sequential starting from AD-1. Each AD must reference at least one Finding (F-N) that informed it.

---

## Standard Format (S-N)

Each standard is a coding rule extracted from CLAUDE.md, steering documents, or company ADRs.

```markdown
### S-1: [Rule statement]

- **Domain**: testing | error-handling | security | naming | api-design | state-management | other
- **File Type**: .tsx | .ts | .py | .sql | * (all)
- **Action Type**: create | modify | * (all)
- **Source**: [path to source document, e.g., `auth-service/CLAUDE.md`]
```

**Applicability metadata** enables downstream matching. A standard with `file_type: .tsx` and `action_type: create` applies to any step that creates a `.tsx` file.

**Multi-project scoping**: Standards from a project's `CLAUDE.md` apply only to files in that project. Standards from user-provided company documents or cross-project steering docs (identified at the Research Scope Review) apply to all projects.

**What qualifies as a standard** (vs. a finding or decision):
- A standard is a **pre-existing rule** from an authoritative source (CLAUDE.md, company ADRs, steering docs)
- A finding is a **discovered fact** about the codebase or domain
- A decision is a **choice made** during this design to resolve a tension

If CLAUDE.md says "use parameterized queries" → standard. If you discover the codebase already uses parameterized queries → finding. If you choose between parameterized queries and an ORM → decision.

---

## File Inventory Format

A flat table of files the implementation will likely create or modify.

```markdown
## File Inventory

| Action | Path | Related FRs | Rationale |
| --- | --- | --- | --- |
| create | src/services/auth.ts | FR-1 | New authentication service |
| modify | src/routes/index.ts | FR-1 | Add auth routes |
| create | src/middleware/jwt.ts | FR-1, FR-2 | JWT validation middleware |
| modify | src/config/env.ts | FR-1 | Add auth config variables |
```

**Multi-project paths**: Use `project::path` notation (e.g., `auth-service::src/services/auth.ts`). Unqualified paths resolve against `artifact_home`.

**Completeness**: The inventory is best-effort. It captures files identified during research, not an exhaustive list. The downstream task skill refines this during decomposition.

**Action values**: `create` (new file), `modify` (change existing file), `delete` (remove file).

---

## Session Sidecar

### File Location

`spec-driven/.sessions/<slug>.design.json`

The slug comes from the invocation argument or is derived from `--from` content.

### Contents

```json
{
  "slug": "user-auth",
  "adaptiveFlow": "partial",
  "backend": "markdown",
  "specSource": "spec-driven/user-auth/spec.md",  // or the --from path for Tier 2 input (e.g., "docs/prd.md")
  "specHash": "sha256:a1b2c3...",
  "phasesCompleted": [0],
  "lastUpdated": "2026-03-27T12:00:00Z",
  "partialData": {
    "findings": [],
    "standards": [],
    "fileInventory": [],
    "approachRecommendations": [],
    "resolvedUncertainties": [],
    "dependenciesAndCoupling": [],
    "constraints": [],
    "assumptions": [],
    "risks": []
  }
}
```

`backend` (optional, values: `"graph"` | `"markdown"`): Records the detected or overridden backend. Set during sidecar creation. When present, resume logic uses this value instead of re-running PATH detection — a previous session's graph-to-markdown fallback must be honored.

Record `adaptiveFlow` before proceeding to Phase 1.

### Lifecycle

1. **Create**: At the start of Phase 0 (after session check confirms no existing sidecar, or after user chooses "Start fresh")
2. **Update**: After each phase completes — record `phasesCompleted` and `partialData`
3. **Delete**: On finalization (terminal action) — the design artifact is the durable state, not the sidecar

Write sidecar updates after the design artifact write. The design write is idempotent; if the session dies between the two, the next session re-runs the write safely.

---

## References Directory (Markdown Backend)

The markdown backend writes deep content to `spec-driven/<slug>/references/` to keep `design.md` within the ~8-12K token target. The task skill loads `design.md` as its primary input; references/ files are loaded on demand.

### references/research.md

Full research results organized by aspect. For each aspect:
- The architectural question investigated
- Key findings with source annotations and confidence
- Approaches evaluated with tradeoff analysis
- Resolved uncertainties with evidence
- External references (URLs, documentation links)

### references/standards.md

Complete standards inventory with typed applicability metadata. One section per standard (S-N) with `domain`, `file_type`, `action_type`, and `source_document`. The task skill matches standards to steps using `file_type` and `action_type`.

### references/contracts.md (optional)

API contract definitions when the design involves API changes. Include request/response shapes, endpoint structures, error formats. Only generated when the design introduces or modifies API boundaries.

## Artifact Sizing

Target **~8-12K tokens** for `design.md`. This keeps the task skill's context budget manageable: spec (~5K) + design.md (~10K) + skill instructions (~5K) ≈ 20K tokens.

Deep content that exceeds this budget goes in `references/`:
- Full research results → `references/research.md`
- Complete standards inventory → `references/standards.md`
- API contracts → `references/contracts.md` (optional)

`design.md` carries summaries with pointers: "See references/research.md for full codebase analysis" in the References section.

---

## Container Setup

**Guard**: If `spec-driven/README.md` already exists, skip this section entirely.

Only if `spec-driven/README.md` does NOT exist, perform first-run container setup:

1. Create `spec-driven/` directory if it does not exist
2. Create `spec-driven/README.md` with content covering these topics (exact wording is not critical):
   - Structure: `spec-driven/<slug>/` containing `spec.md`, `design.md`, `tasks.md`, `bundle-N.md`, `progress.md`
   - `.sessions/` directory for ephemeral session state (gitignored)
   - Workflow: `spec → design → task → execute → verify`
3. Add `spec-driven/.sessions/` to the repository root `.gitignore` if the entry is missing:
   ```
   # Spec-driven workflow session files (ephemeral)
   spec-driven/.sessions/
   ```

This setup is idempotent — any skill can trigger it, but it only runs once per project.

---

## Spec Compatibility Reference

The design skill consumes the exact output format of the `spec` skill. Extract every element listed below — each has distinct downstream behavior in the design skill:

| Spec Element | Location in Spec | Design Usage |
| --- | --- | --- |
| `FR-N` identifiers | `## Functional Requirements` > `### FR-N` | Finding provenance (F-N → FR-N), AD traceability |
| `AC-N.M` (Given/When/Then) | AC table under each FR-N | Informs research scope — ACs reveal boundary conditions |
| Priority | `Priority:` field under each FR-N | Research prioritization — Must-Have FRs explored first |
| NFR-N | `## Non-Functional Requirements` > `### NFR-N` | Research aspects, standard extraction triggers |
| Current State | `## Overview` > `### Current State` | Determines if work is greenfield, extension, or migration |
| Constraints | Typed nodes (graph) or `## Scope` > `### Constraints` (markdown) | Hard boundaries — design MUST respect these. Design adds technical constraints with `source: "codebase"` or `source: "technical"`. |
| Assumptions | Typed nodes (graph) or `## Scope` > `### Assumptions` (markdown) | Validate or extend during research. Design adds assumptions with `source: "design"`. |
| Risks | Typed nodes (graph) or `## Scope` > `### Risks` (markdown) | Address or extend with technical risks. Design adds risks with `source: "codebase"` / `source: "research"`. |
| Dependencies | `## Dependencies` | Integration point research |
| Out of Scope | `## Scope` > `### Out of Scope` | Negative constraints — design MUST NOT cover these |
| Open Questions | `## Open Questions` | Carried forward with default-if-unresolved |
| Projects | `## Projects` (YAML code fence) | Multi-project resolution input |
