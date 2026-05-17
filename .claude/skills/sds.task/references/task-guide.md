# Task Guide

Detailed guidance for the task skill. Referenced from [SKILL.md](../SKILL.md) for decomposition strategies, STEP format, bundling heuristics, and operational details.

---

## Structured Input Resolution

SKILL.md marks mandatory user interaction points with "Structured input:" followed by options. Implement each by calling the platform's interactive question tool with the listed options. The tool call blocks execution until the user responds — do not generate, infer, or assume the user's selection.

| Platform | Mechanism |
|----------|-----------|
| Claude Code | Call `AskUserQuestion` with each option as a selectable choice. Execution pauses until the user selects. |
| VS Code Copilot | Use the `showQuickPick` API or equivalent interactive prompt. |
| Other platforms | Present options via whatever mechanism blocks until user input is received. If no blocking mechanism exists, present a numbered list and explicitly state "Waiting for your selection" — do not continue. |

Every "Structured input:" line in SKILL.md requires a blocking tool call. Text output alone (inline bullets, markdown lists) does not satisfy this requirement — the model can continue generating after text output, bypassing the interaction gate.

---

## Input Model

The task skill reads two required artifacts (`design.md` and `spec.md`) and up to three supplementary reference files from the design phase. Both required artifacts must exist before invocation.

### Required Inputs

| Artifact | Location | What to Extract |
|---|---|---|
| **design.md** | `spec-driven/<slug>/design.md` | Findings (F-N), Decisions (AD-N), Standards (S-N), File Inventory, Dependencies and Coupling, Technical Approach, Constraints, Assumptions, Risks, test approach |
| **spec.md** | `spec-driven/<slug>/spec.md` (or path from design's `spec_source`) | FR-N (identifiers, priorities, descriptions), AC-N.M (acceptance criteria per FR), NFR-N |
| **references/research.md** | `spec-driven/<slug>/references/research.md` | F-N full content: title, related FRs, implications. Conditional — read only if file exists. |
| **references/standards.md** | `spec-driven/<slug>/references/standards.md` | Complete S-N records with full applicability metadata. Conditional — read only if file exists; falls back to design.md Standards table. |
| **references/contracts.md** | `spec-driven/<slug>/references/contracts.md` | API endpoint definitions with FR annotations. Conditional — read only if file exists. |

### Missing Input Handling

| Condition | Response |
|---|---|
| design.md missing | Stop: "No design found at `spec-driven/<slug>/design.md`. Run `/design <slug>` to create one first." |
| spec.md missing | Stop: "No spec found. Run `/spec` to create one first." |
| design.md exists but has `status: draft` | Warn: "Design is still in draft. Finalize with `/design <slug>` before decomposing, or proceed with draft." |
| Graph backend, empty FR/AC query results | Stop: "No spec data found in graph. Run `/spec` first." |
| Graph backend, empty Finding/Decision query results | Stop: "No design data found. Run `/design <slug>` first." |
| test_approach missing from design frontmatter | Default to `none`. Inform: "No test_approach in design — defaulting to none (no test STEPs generated)." |
| test_capabilities missing from design frontmatter | Assume all levels available (unit, integration, e2e). Verify clauses select levels normally. |
| references/research.md absent | Proceed. Note: "No references/research.md — using design.md Finding summaries only." Intent authoring uses design.md summary table. |
| references/standards.md absent | Proceed. Use design.md Standards table only. Note: "No references/standards.md — using design.md Standards summary." |
| references/contracts.md absent | Proceed. No Contracts section in bundle preambles. |

---

## Design and Spec Parsing

### From design.md

**Findings** — extract `F-N` identifiers, source, confidence, related FRs, and content. Findings inform STEP intent: they reveal codebase risks and constraints the executing agent needs to know.

**Decisions** — extract `AD-N` identifiers, chosen approach, rationale, and alternatives. Each STEP should reference the Decisions it follows via `informed-by` traces.

**Standards** — extract `S-N` identifiers with typed applicability metadata (`domain`, `file_type`, `action_type`, `source_document`). Match standards to STEPs by file type during Phase 1.

**File Inventory** — extract file paths with FR associations and create/modify actions. This is the primary seed for STEP `file_paths` declarations.

**Dependencies and Coupling** — extract shared files and sequencing recommendations. Informs bundling heuristics (H3, H5).

**Technical Approach** — per-feature-area narrative. Informs slice boundaries: each feature area may map to a depth-phase slice.

### From spec.md

**FRs and ACs** — extract all FR-N and AC-N.M identifiers. ACs are the primary trace targets for STEPs. Must-Have FRs require complete AC coverage.

**NFRs** — extract NFR-N identifiers. NFRs may produce MANUAL STEPs (e.g., "add performance monitoring") or constrain STEP implementation (e.g., "response time < 200ms").

**Priorities** — extract FR priority (Must-Have, Should-Have, Nice-to-Have). Priority affects coverage validation: Must-Have FRs require full AC->STEP coverage; Should-Have and Nice-to-Have may have partial coverage.

### Reference File Parsing

Read these files during Phase 0 step 4 (markdown backend only — graph backend reads these as nodes directly). Store results in the upstream context registry. Do not merge them into the design.md extractions — they carry different levels of detail.

**From references/research.md**:
- For each `F-N` finding section: extract the F-N identifier, title, `Related FRs` list, and implication sentence(s) from the body content.
- Do not extract Approaches Evaluated or Resolved Uncertainties — only finding-level data for preamble use.

**From references/standards.md**:
- For each `S-N` standard entry: extract identifier, rule, Domain, File Type, Action Type, and Source fields.
- When both references/standards.md and the design.md Standards table exist, references/standards.md is authoritative — it is the complete inventory; design.md carries a subset.

**From references/contracts.md** (optional — file may not exist):
- For each endpoint definition block: extract the HTTP method, path, FR associations (look for `Related FRs:` or `Affects:` annotations), and request/response shape summary.
- If the file has no FR annotations on endpoints, associate all endpoints with all FRs and annotate as `[inferred: no FR annotation in contracts.md]`.

### AC Text Extraction

For each AC-N.M in spec.md's acceptance criteria tables, extract the full text of the Criterion, Given, When, and Then columns. Store as a registry keyed by AC identifier:

```
{ "AC-1.1": { "criterion": "...", "given": "...", "when": "...", "then": "..." }, ... }
```

If spec.md uses inline prose instead of a table for ACs, extract the criterion text verbatim and store as a single `criterion` field (given/when/then will be absent).

This registry is used during Phase 2 bundle writing to populate the Applicable ACs section of each bundle's Context preamble. See Context Preamble Assembly in output-markdown.md.

---

## Decomposition Strategies

Three strategies control how STEPs are organized into Slices and Bundles. The strategy is selected at GATE 1 (Decomposition Approach) or via the `--strategy` flag.

### Walking Skeleton (Default)

**Optimizes for**: Risk reduction. Proves the architecture works end-to-end before adding depth.

**Slice structure**:
- **Skeleton** (Stage: skeleton): One thin STEP per feature area, wired end-to-end. The minimum implementation that proves the architecture — stubs, interfaces, route registration, basic wiring. Typically 3-6 STEPs.
- **Depth** (Stage: depth): Feature-area-specific STEPs that flesh out the business logic. Each feature area becomes a depth slice. STEPs within a depth slice are often file-disjoint and can be bundled for parallel execution.
- **Integration** (Stage: integration): Cross-cutting STEPs that wire components together, run end-to-end verification, and handle remaining edge cases.

**When to recommend**: New feature areas, unfamiliar codebases, features with multiple integration points. This is the default recommendation when no strong signal points to another strategy.

### Maximum Parallelism

**Optimizes for**: Speed with multiple executors. Groups STEPs by file-disjoint feature areas to maximize concurrent execution.

**Slice structure**:
- **Shared infrastructure** (Stage: skeleton): STEPs that create shared interfaces, types, or configuration consumed by multiple feature areas. Must complete before feature slices start.
- **Feature slices** (Stage: depth): One slice per file-disjoint feature area. All feature slices can run in parallel. Each slice is self-contained — no cross-slice file dependencies.
- **Convergence** (Stage: integration): STEPs that merge feature-area outputs, run cross-feature tests, and handle shared-file updates (barrel files, route registration).

**When to recommend**: Multiple agents or team members available, feature areas are clearly file-disjoint, design's Dependencies and Coupling section shows minimal cross-feature sharing.

### Dependency-First

**Optimizes for**: Correctness and safety. Strict topological ordering based on the dependency graph. No speculative parallelism.

**Slice structure**:
- **Foundation** (Stage: skeleton): STEPs with no dependencies (leaf nodes in the dependency graph). These are the first to execute.
- **Layers** (Stage: depth): One slice per dependency level. Each slice contains STEPs whose dependencies are all satisfied by prior slices. No parallelism annotations within slices unless explicitly file-disjoint.
- **Terminal** (Stage: integration): STEPs that depend on everything else — integration tests, final wiring, verification.

**When to recommend**: Safety-critical domains, tight coupling in the design's Dependencies section, complex dependency chains where ordering errors cause cascading failures.

---

## Strategy Impact on Heuristics

The six bundling heuristics (H1-H6) adapt per strategy. H4 (conflict check), H5 (interface-first), and H6 (cohesion check) are strategy-independent.

| Heuristic | Walking Skeleton | Max Parallelism | Dependency-First |
|---|---|---|---|
| H1 (grouping) | By stage: skeleton -> depth -> integration | By feature area: shared -> features (parallel) -> convergence | By dependency level: topological order |
| H2 (file scope) | Standard: separate file-disjoint STEPs within a phase | Primary criterion: feature areas are defined by file disjointness | Secondary: within a dependency level, separate file-disjoint STEPs |
| H3 (dependencies) | Standard: respect declared dependencies | Standard: feature slices are independent by construction | Primary criterion: strict topological ordering |
| H4 (conflict check) | Standard | Standard | Standard |
| H5 (interface-first) | Interfaces go in skeleton slice | Interfaces go in shared infrastructure slice | Interfaces at earliest dependency level |
| H6 (cohesion check) | Standard | Standard | Standard |

---

## STEP Format Reference

Every STEP has these fields:

| Field | Required | Schema Column | Description |
|---|---|---|---|
| title | Yes | `step.title` | Human-readable name |
| intent | Yes (NOT NULL) | `step.intent` | Why this step matters: risks, boundary conditions, domain semantics. See [intent-guide.md](intent-guide.md) |
| effort | Yes | `step.effort` | `XS`, `S`, `M`, `L`. XL flags for splitting — write only if the user explicitly chooses "Keep as-is" (see SKILL.md STEP Production, Effort) |
| file_paths | Yes | `step_file_paths` | Files to create/modify/delete, each with `action` and `repo_name` |
| implementation_guidance | Yes | `step.implementation_guidance` | Actionable bullet points (max 5) for the executing agent |
| pattern_reference | No | `step.pattern_reference` | Existing file path to follow as a pattern |
| verify clauses | Yes | `verify_clause` | At least one clause with level/condition/action/expected_outcome. See [behavioral-verify-guide.md](behavioral-verify-guide.md) |
| standards | No | via `applies-to` edges | Applicable S-N references, matched by file type |
| dependencies | Yes | via `depends-on` edges | `Depends on`, `Enables`, `Parallel with` — use `—` for empty fields |

### STEP Header Format (Markdown)

```
#### STEP-N: [Title]
[FR-N -> AC-N.M] | action `file/path` | Effort: size
```

- `STEP-N` — sequential identifier, starting at 1
- `[FR-N -> AC-N.M]` — trace to FR and AC. Multiple ACs comma-separated. Multiple FRs pipe-separated: `[FR-1 -> AC-1.1 | FR-2 -> AC-2.1]`
- `action` — one of: `create`, `modify`, `delete`
- `` `file/path` `` — primary file path (multi-project: `project::file/path`)
- `Effort: size` — XS/S/M/L

### MANUAL STEP Header Format

```
#### STEP-N: [Title]
MANUAL -> [brief description of why this step exists outside the spec]
```

MANUAL STEPs have no FR/AC traces. They trace to infrastructure needs (CI, docs, deployment, migrations). Validation accepts MANUAL as valid. MANUAL STEPs should be the minority — when a decomposition is dominated by MANUAL STEPs, reassess whether infrastructure concerns belong in this decomposition or should be a separate task.

---

## Granularity Guidelines

Each STEP targets one logical unit of work at the file level:

| Too Abstract | Right Level | Too Granular |
|---|---|---|
| "Implement authentication" | "Create `AuthService` with `login()`/`logout()` in `src/services/auth.ts`" | "Add import statement to line 3" |
| "Build the API layer" | "Add `POST /api/users` endpoint in `src/routes/users.ts`" | "Write the request body validation schema" |

**Rules of thumb**:
- One STEP per file (for create actions) or per logical change (for modify actions)
- Max 5 implementation guidance bullets per STEP. If a STEP needs more, split it.
- Each STEP has exactly one set of verify clauses — if a STEP requires unrelated verifications, it's doing too much.
- XL effort means the STEP should be split. Flag to the user: "STEP-N is XL — consider splitting."

**Tightly coupled exception**: A STEP may touch 2-3 files when they are tightly coupled (e.g., a component + its direct consumer in the same create-then-wire flow) AND the total bullet count stays within 5 AND splitting would create STEPs that cannot be independently verified.

---

## Bundle Construction Heuristics

Apply these six heuristics in order. Bundling is judgment-based — these are reasoning guides, not algorithms.

### H1: Group by Strategy

Apply the strategy's primary grouping rule (see Strategy Impact on Heuristics table). Walking skeleton groups by stage (skeleton, depth, integration). Max parallelism groups by feature area. Dependency-first groups by topological level.

### H2: Separate by File Scope

Within each group, examine declared file paths. STEPs that touch entirely different files can be placed in parallel bundles (annotated `Parallel: yes (file-disjoint)`). STEPs that share files must stay in the same sequential bundle or in explicitly ordered sequential bundles.

### H3: Respect Dependencies

A STEP goes into the earliest bundle where all its `Depends on` targets are in prior bundles. Dependency declarations from the design's file inventory and coupling analysis seed the initial dependencies — they may be tightened but not relaxed.

### H4: Check for Conflicts After Grouping

After initial grouping, scan each parallel bundle: if two STEPs in the same parallel bundle declare the same file path, move the later STEP to the next sequential bundle. Record moved STEPs in the conflict analysis.

### H5: Interface Changes Go First

When one STEP modifies a shared interface (type definition, API contract, config schema) and other STEPs consume it, place the interface STEP in an earlier bundle. Expand-contract pattern: expand first, consumers adapt in parallel.

### H6: Review Bundle Cohesion

Each bundle represents one logical unit of work for a single agent session. If a bundle has more STEPs than can be held in working memory with their full context, split it — both halves may be `Parallel: yes` if file-disjoint. If splitting would break logical cohesion or create artificial dependencies between the resulting bundles, keep the bundle intact.

### Bundle Verify Clause

Each bundle gets a bundle-level verify clause that tests the combined output of its steps. Place it in the bundle header after the metadata line.

**Format**:

```markdown
**Bundle Verify**: [one-sentence summary of what the bundle's combined output achieves]
- **Level**: unit | integration | e2e | inspection
- **Given**: [precondition for testing the slice goal]
- **Action**: [concrete action to exercise the combined output]
- **Outcome**: [observable result that confirms the slice goal is met]
```

**Derivation heuristic** (by slice stage):
- **Skeleton**: Verify end-to-end wiring. Can a request traverse the full stack? Example: "Application server running with skeleton routes → send GET to /api/users → returns HTTP response (not connection refused)."
- **Depth**: Verify the feature area's behavioral contract. Does the business logic produce correct output for a representative input? Example: "Auth service running → login with valid credentials → returns a signed JWT with expected claims."
- **Integration**: Verify cross-component interaction. Do the wired components communicate correctly? Example: "Auth + user service running → create user then login → login response includes the created user's ID."

When `test_capabilities` at the desired level is null, fall back to the next available level. A skeleton bundle in a project with no e2e framework falls back to integration (hit the endpoint directly) or inspection (verify the wiring exists in code).

**Verify level distribution** (quality signal): A well-decomposed task set has verify clauses distributed like a pyramid — mostly unit-level, some integration, fewer e2e and inspection. When inspection-level clauses dominate, the spec may be infrastructure-heavy or the decomposition may be too coarse. Use this as a judgment signal, not a numeric threshold.

---

## Traceability Rules

### Two-Level Chain

```
Spec Level:   FR-1          (functional requirement)
              AC-1.1        (acceptance criterion)

Task Level:   STEP-1        (implementation step)
              [FR-1 -> AC-1.1]  (inline back-reference)
```

The `traces-to` edge connects STEP -> AC. The FR is reached transitively through AC's `fr_id` FK.

### Traceability Invariants

1. **No orphan STEPs** — every STEP references at least one AC or is marked MANUAL.
2. **No missed ACs** — every AC for Must-Have FRs is covered by at least one STEP.
3. **Must-Have coverage** — every Must-Have FR has complete AC coverage.
4. **No dangling references** — every AC and FR cited in a STEP's trace must exist in the spec.
5. **MANUAL ratio** — MANUAL STEPs should be the minority. A decomposition dominated by MANUAL STEPs suggests infrastructure concerns may warrant a separate task.

---

## Conflict Analysis

Produced during Phase 2 after bundle construction. Always runs regardless of `--minimal`.

### Scope

Scoped to **explicitly declared file paths only** — paths in STEP `file_paths` declarations. Does not predict implicit touches.

**Multi-project paths**: `project::path` notation. Conflict analysis compares within each project only. Cross-project conflicts are impossible.

Include this disclaimer in every conflict analysis section:

> Note: Covers explicitly declared file paths only. Implicit touches (barrel files, shared configs, type re-exports, route registration) may require manual sequencing during execution.

### What to Report

For each hot file (touched by STEPs in different bundles):

| Hot File | Touched By | Strategy |
|---|---|---|
| src/routes/index.ts | STEP-2 (Bundle 1), STEP-7 (Bundle 3) | Sequential (Bundle 1 before Bundle 3) |

STEPs within the same sequential bundle do not need conflict analysis rows.

### Common Implicit Touches

When reviewing STEP declarations, check whether these file types may be touched implicitly:
- **Barrel/index files** — re-exports updated when new modules added
- **package.json** — dependency additions from any STEP
- **Shared type definitions** — `types.ts`, `interfaces.ts`
- **Route registration** — `app.ts`, `server.ts`, `routes/index.ts`
- **Migration files** — ordering constraints in `migrations/`
- **Lock files** — `package-lock.json`, `yarn.lock`

Note these in the disclaimer if likely touched.

---

## Progress Tracker Format

Progress is always tracked per-bundle. No shared `progress.md` — each bundle has its own file.

### File Location

`spec-driven/<slug>/progress-bundle-N.md` — committed to version control.

### Format

See the progress tracker template in [task-template.md](../assets/task-template.md).

**Status values**: `pending`, `in-progress`, `done`, `blocked`.
**Commit column**: Populated by the executor with git commit short hash (e.g., `abc1234`).
**Progress summary line**: Updated after each step completes: `X/M steps complete`.

### Session Log Template

```markdown
### [date] — [context]
- Completed: STEP-N: [brief title], STEP-M: [brief title]
- Decisions: [any decisions made, or "none"]
- Next: STEP-P: [brief title]
```

No free-form prose. Three lines per entry.

### Consolidation (Agent and Team Modes)

After all parallel bundles in a level complete, the orchestrator consolidates:
1. Read all `progress-bundle-N.md` files for the completed level
2. Verify all STEPs in those bundles are `done`
3. Proceed to the next level's bundles

The orchestrator reads per-bundle progress files — it does not write a merged summary.

---

## Adaptive Flow Rules

Conditions are defined in SKILL.md's Adaptive Flow section — SKILL.md is authoritative. This section describes supplementary behavior for each flow path.

### Express Flow Path

**Behavior**: Compress Phase 1 + Phase 2 (Phase 0 always runs). Present the full decomposition directly at GATE 2 without intermediate gap-surfacing. The user sees slices, STEPs, and bundles in one pass.

### Partial Flow Path

**Behavior**: Surface gaps during Phase 0. Present the context summary with an "I still need to understand" section. Proceed through remaining phases after gap resolution. If the user cannot resolve a gap, document it as an assumption and tag affected STEPs with `[Assumption: gap description]`.

### Full Flow Path

**Behavior**: Full flow with no skips. Intermediate review between Phase 1 and Phase 2.

---

## Downstream Contract

The task output is consumed by the execute skill. This defines the contract.

### Invocation

The execute skill receives:
- A bundle identifier (e.g., `Bundle 1`) or a step ID (e.g., `STEP-3`)
- A path to the task or bundle file

### STEP Context

Each STEP is self-contained for a single agent session. The execute skill reads:
- **File paths**: `create`/`modify`/`delete` declared in the STEP header
- **Implementation guidance**: Bullet-point checklist (max 5 bullets)
- **Verify clauses**: Structured level/condition/action/outcome tuples
- **Pattern reference**: Existing file path to follow
- **Dependencies**: `Depends on: STEP-N` — executor confirms these are `done` before starting

### Completion Signal

After completing a STEP, the executor:
1. Creates a git commit with `[STEP-N]` in the message
2. Records the commit short hash in the bundle's progress tracker

### Failure Protocol

If a STEP cannot be completed:
1. Mark as `blocked` in progress tracker
2. Record blocker in Notes column
3. Do not proceed to dependent STEPs
4. Surface the blocker for resolution

### Read-Only Task Document

The executor must NOT modify `tasks.md` or `bundle-N.md`. All execution state lives in `progress-bundle-N.md`.

### Bundle Context Preamble

Each bundle-N.md includes a Context preamble between the bundle header block and the first STEP. The preamble provides upstream context scoped to this bundle's STEPs — the execute skill reads it before beginning the first step to understand the relevant requirements, decisions, and constraints without loading the full spec or design artifacts.

The preamble is assembled during Phase 2 (post-bundling). It is a read-only reference for the executor — the executor must NOT modify it. See Context Preamble Assembly in output-markdown.md for the full structure and scoping algorithm.

### Bundle Topology

Bundle sequences may contain multiple alternating sequential and parallel groups. The execute skill groups contiguous same-annotation bundles into phases and processes them in order. No constraint limits the number or arrangement of phases.

---

## Design Compatibility Reference

The task skill consumes the design skill's output. Process every row in this table — the last three rows extract from frontmatter rather than document sections. Field mapping:

| Design Element | Location | Task Usage |
|---|---|---|
| Findings (F-N) | `## Findings` section | Inform STEP intent — name codebase risks |
| Decisions (AD-N) | `## Architecture Decisions` | Create `informed-by` edges. STEPs follow chosen approaches. |
| Standards (S-N) | `## Standards` | Match to STEPs by file_type. Surface as `> **Standards**` blockquote. |
| File Inventory | `## File Inventory` | Seed STEP file_paths. FR associations inform traceability. |
| Dependencies and Coupling | `## Dependencies and Coupling` | Inform bundling (H3, H5). Shared files inform conflict analysis. |
| Technical Approach | `## Technical Approach` | Inform slice boundaries. Per-feature-area narrative maps to slices. |
| Constraints | `## Constraints (Technical)` | Carry into STEP intent for affected FRs. |
| Assumptions | `## Assumptions` | Document in STEP intent. May produce MANUAL STEPs if assumption needs validation. |
| Risks | `## Risks (Technical)` | Inform verify clauses — test the risky condition. |
| test_approach | Frontmatter | `tdd`: generate test STEPs before implementation. `test-after`: test STEPs after. `none`: skip. |
| test_capabilities | Frontmatter | Maps verification levels (unit, integration, e2e) to available/null. When null at a level, escalate verify clauses to the next available level. |
| spec_source | Frontmatter | Path to spec.md for reading FRs/ACs. |
| Open Questions | `## Open Questions` | Check for unresolved items affecting decomposition. Must be empty for Express flow path routing. Surface at GATE 2 open question sweep. |
| spec_hash | Frontmatter | Recorded at finalization for downstream freshness checks. |

> When `references/research.md`, `references/standards.md`, or `references/contracts.md` exist, they supplement the corresponding design.md sections (Findings, Standards) with full detail. See Required Inputs for extraction rules.

---

## Session Sidecar

### File Location

`spec-driven/.sessions/<slug>.task.json` — ephemeral, gitignored.

### Contents

```json
{
  "slug": "string",
  "designSource": "string — relative path to design.md",
  "designHash": "string — SHA-256 of design.md at Phase 0",
  "specSource": "string — relative path to spec.md",
  "specHash": "string — SHA-256 of spec.md at Phase 0",
  "backend": "markdown | graph",
  "strategy": "walking-skeleton | max-parallelism | dependency-first",
  "phasesCompleted": [0, 1, 2],
  "lastUpdated": "ISO 8601 timestamp",
  "partialData": {
    "steps": "STEP-N entries (if Phase 1 complete)",
    "bundles": "bundle assignments (if Phase 2 complete)",
    "frCount": "number",
    "flowPath": "express | partial | full"
  }
}
```

### Resume Behavior

When a sidecar is found, check `phasesCompleted`:
- Phase 0 complete: re-read context (may have changed). Compute SHA-256 of design.md and spec.md. If either differs from the sidecar's stored hashes, inform: "Design/spec changed since last session." Offer: "Restart from Phase 0" / "Continue with updated inputs". On restart: delete the sidecar and restart. On continue: update the sidecar hashes and proceed to Phase 1.
- Phase 1 complete: read STEPs from `partialData.steps`, proceed to Phase 2
- Phase 2 complete: read bundles from `partialData.bundles`, proceed to Phase 3
- Express flow path (phasesCompleted [0, 1, 2]): proceed directly to Phase 3 validation. Express flow path updates phasesCompleted to [0, 1, 2] after the combined decomposition+bundling completes.

### Cleanup

Sidecar is deleted on finalization. On invocation, check for existing sidecar — offer resume if found.

---

## Context Summary Template

Phase 0 presents this summary before GATE 1. Match this format:

```
Here's what I gathered:
- Design: [N] Findings, [M] Decisions, [K] Standards
- Design freshness: [current | stale — design changed since last task generation]
- Spec: [N] FRs ([M] Must-Have), [K] ACs, [J] NFRs
- Codebase: [N files scanned], [key patterns]
- Test approach: [tdd/test-after/none]
- Additional context: [what was provided via --context, or "none"]
- Flow: [Full | Partial | Express] — [reason]

Recommended strategy: [Walking Skeleton | Max Parallelism | Dependency-First]
Rationale: [1-2 sentences explaining why]

[If gaps exist:]
I still need to understand:
- [gap 1]
- [gap 2]
```

---

## Closing Message Template

> This is the closing message format only — the full finalization flow (write sequence, commit gate) is in SKILL.md Phase 3.

**Next steps**: "Run `/sds.execute <slug>` to begin execution."

---

## Container Setup

**Guard**: If `spec-driven/README.md` already exists, skip entirely.

Only if `spec-driven/README.md` does NOT exist:
1. Create `spec-driven/` directory if needed
2. Create `spec-driven/README.md` describing the workflow structure
3. Add `spec-driven/.sessions/` to `.gitignore` if missing

This setup is idempotent — any skill can trigger it, runs once per project.
