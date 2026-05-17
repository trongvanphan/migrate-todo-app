---
name: sds.task
description: |
  Decompose a specification and architectural design into individually-executable implementation
  steps organized into slices and bundles. Use when someone says "decompose", "create tasks",
  "task this", "break down the design", "task decomposition", or "create steps".
---

# Task Decomposition

Read a spec (FRs, ACs, NFRs) and design (Findings, Decisions, Standards) to produce enriched STEPs organized into vertical Slices and execution Bundles. Each STEP carries intent, verify clauses, effort sizing, and file paths.

## Trigger

```bash
/sds.task user-auth
/sds.task user-auth --strategy max-parallelism
/sds.task user-auth --context docs/team-structure.md
/sds.task user-auth --minimal
```

## Flags

| Flag | Description |
| --- | --- |
| First argument (slug) | Slug identifying the spec. Resolves to data via detected backend: markdown reads `spec-driven/<slug>/design.md` + `spec.md`, graph queries upstream nodes by slug. |
| `--strategy [walking-skeleton\|max-parallelism\|dependency-first]` | Override decomposition strategy. If omitted, recommended at GATE 1 based on context analysis. |
| `--context <path>` | Additional context file (team structure, execution preferences, constraints). Must be a file path. |
| `--minimal` | Skip qualitative validation (Layer 2). Mechanical validation still runs. |

## Output

- Creates task file at: `spec-driven/<slug>/tasks.md`
- Uses template from [assets/task-template.md](assets/task-template.md)
- Creates `spec-driven/<slug>/bundle-N.md` per bundle (self-contained execution units)
- Creates `spec-driven/<slug>/progress-bundle-N.md` per bundle (initialized, all steps `pending`)

Execution topology (parallelism, branch isolation, team coordination) is an execute-skill concern. The task skill produces the same output structure regardless. Progress is always bundle-specific — no shared progress file.

Flags are independent and combinable unless explicitly stated otherwise.

---

## Tool Usage

**Structured input**: For all bounded-answer questions (confirmations, yes/no, select-from-list, or any question where valid responses can be enumerated), call a blocking tool that presents selectable options and pauses execution until the user responds — see Structured Input Resolution in task-guide.md for the platform-specific mechanism. Text output alone does not satisfy this requirement. Use conversational text only for genuinely open-ended questions.

Never present bounded options as plain-text numbered or lettered lists — always use the interactive mechanism. Plain-text lists allow the model to continue without waiting for an actual user selection, defeating mandatory interaction gates.

**Wait for user response**: When presenting structured input, wait for the actual response before proceeding. Generating or inferring a response corrupts decomposition — the user decides the strategy, reviews the STEPs, and controls what gets committed.

**Progress milestones**: Phase 0 uses `[N/3]` numbered format. Phases 1-3 use label prefixes (`[Decompose]`, `[Bundle]`, `[Validate]`).

**Mandatory interaction gates** (never self-answered — self-answering produces decompositions the user has not reviewed, undermining the skill's collaborative design):
1. **Decomposition Approach** (end of Phase 0): Strategy selection, slice structure preview. Express flow path still presents strategy selection at GATE 1, but defers the slice structure preview — present it at GATE 2 alongside STEPs and bundles (see Adaptive Flow).
2. **Task Review** (Phase 3): Complete decomposition review before finalization
3. **Commit Decision** (Phase 3): Separate from task approval

**Commit constraint**: NEVER run `git add` or `git commit` without receiving explicit user approval at the commit gate — unapproved commits cannot be undone and may include structural issues the user would have caught at review.

---

## Phase 0: Context Gathering (Always Runs)

**Before starting**: Read these reference files — they contain detailed guidance that this document summarizes:
- [references/task-guide.md](references/task-guide.md) — input model, parsing rules, strategies, STEP format, bundling heuristics, progress format, sidecar lifecycle
- [references/intent-guide.md](references/intent-guide.md) — intent authoring guidance
- [references/behavioral-verify-guide.md](references/behavioral-verify-guide.md) — verify clause derivation

**Backend detection** (silent, first step): Check if `sds` and `dolt` are available in PATH by running `which sds >/dev/null 2>&1 && which dolt >/dev/null 2>&1`. If both available, use **graph backend**. Otherwise, use **markdown backend** (default). Remember for session. Load the output backend reference now — graph: [references/output-graph.md](references/output-graph.md), markdown: [references/output-markdown.md](references/output-markdown.md). These contain write commands needed during Phase 1 and Phase 2 incremental writes.

**Steps:**

Emit: `[1/3] Checking for existing sessions...`

1. **Resolve inputs**:
   - Read design via detected backend. Markdown: read `spec-driven/<slug>/design.md`. Graph: query Finding, Decision, Standard, Constraint, Assumption, Risk nodes by slug. If design data is missing, stop: "No design found. Run `/design <slug>` first."
   - If design has `status: draft` in frontmatter, warn: "Design is still in draft." Structured input: "Proceed with draft" / "Stop and finalize design first". On "Stop": stop with guidance: "Run `/design <slug>` to finalize."
   - Read spec via detected backend. Markdown: read `spec-driven/<slug>/spec.md`. If not found, read from the path in the design's `spec_source` frontmatter field. Graph: query FR, AC, NFR nodes. If spec data is missing, stop: "No spec found. Run `/spec` first."
   - If any graph query fails, discard all partially-read graph data from Phase 0 and fall back to markdown backend for the session. Re-read design and spec from markdown files before continuing. For graph write failures during Phase 1 or Phase 2, follow the CLI Failure Handling rules in the loaded output backend reference.

2. **Session check**: Check for existing sidecar at `spec-driven/.sessions/<slug>.task.json`.
   - If found but not parseable as valid JSON: delete it and inform: "Found corrupt session file — starting fresh." Re-evaluate the remaining conditions in this step (the sidecar no longer exists).
   - If found and valid: offer resume (see Resume Behavior in task-guide.md for phase-skip logic). If the user declines, delete the sidecar and start fresh from step 1 (backend detection is already cached for the session).
   - If no sidecar but `tasks.md` exists: offer "Regenerate" / "Review existing." On "Review existing": load the existing tasks.md, present the GATE 2 summary, and offer the same review options (Looks good / Adjust / Regenerate). On "Looks good": skip Phases 1-2 and Phase 3 validation — proceed directly to GATE 3 (Commit Decision). On "Adjust": follow up conversationally, apply changes, then re-present review options. On "Regenerate": proceed to step 3.
   - If no sidecar and no `tasks.md`: create the `spec-driven/.sessions/` directory if it does not exist. Create the sidecar at `spec-driven/.sessions/<slug>.task.json`. Required fields: slug, designSource, designHash, specSource, specHash, backend, strategy (null until GATE 1), phasesCompleted, lastUpdated, partialData. See task-guide.md Session Sidecar for the full schema. Update `phasesCompleted` as each phase completes.

3. **Design freshness check**: Compute SHA-256 of design.md. If the file cannot be read (deleted or inaccessible), re-read the file once. If still unreadable, stop: "Cannot read design.md for freshness check — verify the file exists." If existing tasks.md has a different `design_hash`, inform: "Design changed since tasks were generated." Structured input: "Regenerate" / "Keep existing". On "Regenerate": delete existing tasks.md and continue to step 4. On "Keep existing": continue to step 4 (stale design hash will be noted in the context summary).

4. **Extract identifiers**: Parse FR-N, AC-N.M, NFR-N from spec. Parse F-N, AD-N, S-N from design. Extract File Inventory, Dependencies and Coupling, Technical Approach, Constraints, Assumptions, Risks, Open Questions, test approach, test_capabilities (if test_approach or test_capabilities are absent, see Missing Input Handling in task-guide.md for defaults).

   **Full AC text**: For each AC-N.M parsed from spec.md, extract the full Given/When/Then text (not just the identifier). Store as the AC text registry for Phase 2 preamble assembly. See AC Text Extraction in task-guide.md for parsing rules.

   **Reference file reads** (markdown backend only — graph backend reads these as nodes directly): Conditionally read design reference files at `spec-driven/<slug>/references/`. For each of `research.md`, `standards.md`, `contracts.md`: if the file exists, read and extract per Reference File Parsing in task-guide.md. If the file does not exist, note the absence and proceed — no error. Store all extracted data in the upstream context registry for Phase 2 preamble assembly.

Emit: `[2/3] Scanning codebase for file inventory...`

5. **Multi-project resolution**: When the workspace includes multiple project directories, resolve logical project names to filesystem paths. Inherit `projects` from design frontmatter. For each project entry, resolve `name` to a workspace directory using these rules in order: (1) match `identity` field against normalized git remote URLs (`git -C "<dir>" remote get-url origin`, strip protocol/`.git`/trailing slashes, lowercase), (2) basename match (`basename "<dir>" == project.name`), (3) if no match, prompt the user. If the command fails (not a git repo, no origin remote), rule (1) is a non-match; proceed to rule (2). If the user cannot provide a valid path at rule (3), skip that project's file inventory and flag the gap.

6. **Codebase scan**: In single-project mode (no `projects` in design frontmatter), scan the project root directory. In multi-project mode, scan each successfully-resolved project directory from step 5 — skip projects that failed resolution (their gap was already flagged). Run Glob patterns for file inventory. The scan results provide file paths for conflict analysis (Phase 2, H4) and standards matching (Phase 1, STEP production). In multi-project mode, use absolute paths per resolved project directory. If the scan returns zero files, flag as greenfield context for adaptive flow routing (Full flow path trigger).

Emit: `[2/3] Codebase scan complete — N files indexed.`

7. **Standards extraction**: Read each resolved project's CLAUDE.md. If a project has no CLAUDE.md, skip standards extraction for that project and note: "No CLAUDE.md found for [project] — no project-specific standards extracted." Identify statements that prescribe how code should be written — naming conventions, required patterns, forbidden practices, security rules, test expectations, linting/formatting requirements. Record each as a short rule with its domain (e.g., "testing", "security", "style"). If CLAUDE.md references external standards by relative path, follow those references and read the referenced files (one level of indirection only — do not follow references within the referenced files). Keep the extracted standards organized by domain — reference them during Phase 1 when matching standards to STEPs by file type. In multi-project mode, maintain per-project lists.

Emit: `[3/3] Analyzing context...`

8. **Read `--context` file** if provided. If the file does not exist at the provided path, inform: "Context file not found at [path]. Proceeding without additional context." and continue to step 9. If context content reveals gaps (unresolved assumptions, missing file paths, dependency unknowns), treat as unresolved assumptions for adaptive flow routing purposes.

9. **Adaptive flow determination**: Evaluate the Adaptive Flow conditions below and assign the flow path (Full, Partial, or Express).

10. **Complexity bounds**:
    - **Upper**: If the spec has more than 25 Must-Have ACs, present: "This spec has [N] Must-Have ACs. Recommend splitting into smaller specs before decomposing." Structured input: "Split first" / "Proceed anyway". On "Split first": stop. On "Proceed anyway": continue with a warning in the context summary.

11. **Context summary**: Present using the Context Summary Template section in [task-guide.md](references/task-guide.md). Include: design/spec stats, codebase overview, test approach, flow routing, and gaps (if any).

### GATE 1: Decomposition Approach

If `--strategy` was provided, skip this gate — inform: "Using [strategy] (from --strategy flag)."

If the Express flow path was selected, present the recommended strategy with rationale at this gate (same criteria below). The user confirms strategy before decomposition begins — even on Express, the strategy checkpoint is mandatory because decomposition is expensive to redo.

Otherwise, recommend a strategy based on context:
- **Walking skeleton** (default): new feature areas, unfamiliar codebases, multiple integration points
- **Max parallelism**: multiple agents/team members, file-disjoint feature areas, minimal cross-feature coupling
- **Dependency-first**: safety-critical domains, tight coupling, complex dependency chains

Present: strategy recommendation with rationale, proposed slice structure (phase names and approximate STEP counts), and total estimated STEPs.

Structured input: "Proceed with [recommended strategy]" / "Use max-parallelism" / "Use dependency-first" / "Adjust"

On "Adjust": follow up conversationally, update strategy, re-present.

Wait for the user's actual response — self-answering produces decompositions the user has not reviewed.

---

## Adaptive Flow

Route to one of three flow paths based on Phase 0 output. Evaluate in order: Full, Partial, Express. Use the first match. Never repeat information already gathered.

**FR count gate**: Count FRs explicitly. If count exceeds 8, Express flow path MUST NOT be used — compressing decomposition for large specs produces unreviewable output and increases drift risk in the combined non-interactive stretch. Route to Partial or Full based on the remaining conditions.

- **Full** (all phases, intermediate review): 15+ FRs, OR greenfield project (zero files from codebase scan), OR complex dependency chains (3+ components forming a linear dependency chain in the design's Dependencies and Coupling section, OR any dependency cycle detected there). Full phases with intermediate review between Phase 1 and Phase 2.
- **Partial** (surface gaps): 9-14 FRs, OR gaps in file inventory, OR unresolved assumptions. Surface gaps, proceed after resolution. After gap resolution, re-evaluate flow path conditions — if Express conditions are now met, switch to Express. Continue to GATE 1 (Decomposition Approach), then Phase 1. If the user cannot resolve a gap, document it as an assumption in the task output and tag affected STEPs with `[Assumption: gap description]`. Surface unresolved gaps again at GATE 2.
- **Express** (compress Phase 1+2 when ALL: ≤8 FRs AND design status is not draft AND spec exists with parseable FRs/ACs AND complete file inventory AND no unresolved assumptions, missing file paths, flagged unknowns, or unresolved Open Questions):
  - GATE 1 still fires for strategy confirmation — Express compresses the decomposition and bundling phases, not the strategy decision.
  - If `--strategy` was provided, use the provided strategy instead of presenting GATE 1.
  - After each slice completes, emit: `[Decompose] Slice N complete — K STEPs produced.`
  - After all STEP production completes, emit: `[Decompose] N STEPs produced across M slices. Proceeding to bundling...`
  - Before bundling, verify: (1) every Must-Have FR has at least one STEP, (2) no STEP is missing intent or verify clauses, (3) every verify clause has a level field. If any check fails, present the gap and offer: "Fix and continue" / "Proceed anyway". On "Fix": apply the correction and re-verify. On "Proceed": note the gap in the context for GATE 2 review.
  - After bundling completes, verify every bundle has a `**Bundle Verify**:` block. If any bundle is missing one, generate it before proceeding — derive from the bundle's slice goal using the format in Phase 2.
  - Emit: `[Bundle] M bundles created. Running conflict analysis...`
  - Present full decomposition — slices, STEPs, and bundles — at GATE 2 for review.

**Express flow path milestones**: Emit `[1/3]` before context, `[2/3]` before scan, `[3/3]` before the combined decomposition+bundling pass. Validation and GATE 2 follow as normal.

---

## Phase 1: Vertical Slicing & STEP Decomposition

Transform design and spec into individually-executable STEPs organized into Slices.

Emit: `[Decompose] Creating slices and STEPs...`

For specs with 10+ FRs, emit intermediate progress every 3 FRs: `[Decompose] (K/N FRs decomposed)...`

### Slice Creation

Apply the strategy selected at GATE 1. See [task-guide.md](references/task-guide.md) for per-strategy slice structures.

Each slice has: name, description (slice goal), stage (`skeleton`/`depth`/`integration`), execution order. Slice "stage" is a categorization label for the slice's role in the build-up sequence — distinct from skill "Phases" (0-3) which track the decomposition process itself. All STEPs in a slice share the same stage — mixing stages within a slice breaks the execution ordering guarantee: skeleton slices must complete before depth slices start, and a mixed slice cannot be scheduled at either level without violating that dependency.

### STEP Production

For each FR/AC, produce one or more STEPs. Each STEP specifies:

- **Title**: human-readable name
- **Trace**: `[FR-N -> AC-N.M]` inline reference (MANUAL STEPs use `MANUAL -> [description]`)
- **File paths**: from design's File Inventory, with action (`create`/`modify`/`delete`) and `repo_name`
- **Effort**: XS/S/M/L (derive from file count and change complexity). XL flags for splitting — present the XL STEP with a recommended split point and offer: "Split as suggested" / "Keep as-is" / "Adjust split". Do not split autonomously.
- **Intent** (NOT NULL): derive from design Findings, Decisions, and Constraints. Name specific risks, boundary conditions, or domain semantics. See [intent-guide.md](references/intent-guide.md). Structural STEPs use `N/A — structural step`.
- **Implementation guidance**: max 5 actionable bullets for the executing agent
- **Pattern reference**: existing file to follow (from design's File Inventory or codebase scan)
- **Verify clauses**: derive from intent. Render step-level verify clauses in pipe-delimited format: `- Level: X | Given: Y | Action: Z | Outcome: W`. The level field (unit/integration/e2e/inspection) is selected using the Tetris Principle — see [behavioral-verify-guide.md](references/behavioral-verify-guide.md) step 3b. When the design's `test_capabilities` shows null at the selected level, check whether the design includes a recommendation for that gap — if so, note it; if not, escalate to the next available level. Must-Have FR behavioral STEPs require assertions beyond compilation.
- **Standards**: match S-N from design by `file_type` against the STEP's file paths. Include as `> **Standards**` blockquote.
- **Dependencies**: `Depends on` / `Enables` / `Parallel with`. Seed from design's Dependencies and Coupling section. Use `—` for empty fields.

### Test Approach Impact

Apply the `test_approach` from the design frontmatter to STEP production:

- **tdd**: For each behavioral STEP, generate a paired test STEP immediately before it in the same bundle. Test STEP trace: `MANUAL -> Test-first for STEP-N`. The test STEP's verify clause validates that the test exists and fails before implementation.
- **test-after**: For each behavioral STEP, generate a paired test STEP immediately after it in the same bundle. Test STEP trace: `MANUAL -> Test for STEP-N`.
- **none**: Do not generate separate test STEPs. Verify clauses on implementation STEPs still apply.

Test STEPs count toward bundle cohesion (H6). If adding test STEPs makes a bundle too large to reason about as a unit, split the bundle. When splitting, a TDD test STEP and its paired implementation STEP must remain in the same bundle. Split at a test-implementation pair boundary, not within a pair.

### NFR Disposition

After producing all STEPs, map each NFR from the spec to one of three dispositions:

- **Implemented**: a STEP enforces it — cite the STEP ID and its verify clause
- **Platform**: inherited from infrastructure — cite the enforcing mechanism (e.g., "API Gateway timeout", "ProtectedModuleRoute")
- **Deferred**: explicitly out of scope for this iteration — state justification

An NFR with no disposition is a gap, not a delegation. Include all NFRs in the NFR Traceability section of tasks.md (see template) — this prevents the ambiguity between "intentionally delegated to platform" and "accidentally omitted."

### Traceability Edges

- `traces-to`: STEP -> AC (every non-MANUAL STEP)
- `informed-by`: STEP -> AD-N (when the STEP follows a Decision's chosen approach)

### Incremental Write

Write the task file after this phase completes (before Phase 2). Update the session sidecar `phasesCompleted` to include Phase 1 immediately after the task file write succeeds — if interrupted between the two, resume will safely repeat Phase 1 (the write is idempotent). Express flow path: skip this intermediate write — the combined Phase 1+2 pass writes once at completion. Partial flow path: write without intermediate review. For Full flow path, present for intermediate review: "I've produced N STEPs across M slices. Review before bundling?" Options: "Proceed to bundling" / "Review step list first". On "Review step list first": present the step list organized by slice, then re-offer: "Proceed to bundling" / "Adjust steps". On "Adjust": follow up conversationally, apply changes, re-present.

---

## Phase 2: Bundle Construction

Group STEPs into execution bundles using strategy-specific heuristics.

Emit: `[Bundle] Grouping N STEPs into bundles...`

Apply heuristics H1-H6 in order. See [task-guide.md](references/task-guide.md) for per-strategy heuristic behavior.

**Bundle header format**: Every bundle header includes: `> Stage: [name] | Parallel: [yes/no (reason)] | Files: [comma-separated]`

**Bundle verify clause**: Every bundle gets a bundle-level verify clause placed after the metadata line. This clause is required — the execute skill's Layer 3b reads it to verify the bundle's combined output. Derive it from the bundle's slice goal:
- **Skeleton-stage bundles**: verify end-to-end wiring — can a request traverse the full stack?
- **Depth-stage bundles**: verify the feature area's behavioral contract — does the business logic produce correct output for a representative input?
- **Integration-stage bundles**: verify cross-component interaction — do the wired components communicate correctly?

Render in this exact format (typically integration or e2e level):

```
**Bundle Verify**: [one-sentence summary of what the bundle's combined output achieves]
- **Level**: integration | e2e | inspection
- **Given**: [precondition on the merged execution state]
- **Action**: [concrete command or check to run]
- **Outcome**: [observable result that confirms the slice goal]
```

When `test_capabilities.e2e` is null, fall back to integration or inspection level. See [task-guide.md](references/task-guide.md) for the full derivation heuristic.

**Multi-project optimization**: Cross-project STEPs are file-disjoint by definition. H2 benefits naturally. Conflict analysis (H4) scopes within-project only.

**Bundle cohesion**: Each bundle represents one logical unit of work for a single agent session. If splitting would break cohesion or force artificial dependencies, keep the bundle intact. See H6 in [task-guide.md](references/task-guide.md) for the full heuristic.

### Conflict Analysis

Emit: `[Bundle] N bundles created. Running conflict analysis...`

After bundling, produce a conflict analysis listing hot files and sequencing strategies. Always runs regardless of `--minimal`. See [task-guide.md](references/task-guide.md) for format and scope.

**Context preamble assembly**: For each bundle, assemble the Context preamble between the bundle header and the first STEP. Scope to the bundle's STEPs only — include applicable ACs, Architecture Decisions, Findings, Standards, Constraints, Risks, and Contracts. See Context Preamble Assembly in output-markdown.md for the scoping algorithm and omit-if-empty rules.

### Incremental Write

Update the task file with bundle assignments after this phase completes. Express flow path: skip this intermediate write — the combined pass writes once at completion. Update the session sidecar `phasesCompleted` to include Phase 2 immediately after the file write succeeds — if interrupted between the two, resume will safely repeat Phase 2 (the write is idempotent).

---

## Phase 3: Validate & Review

Emit: `[Validate] Checking task quality...`

### Validation

Under `--minimal`, skip qualitative validation (Layer 2). Mechanical validation (Layer 1) still runs.

**Layer 1 — Mechanical**: `python "<skill-directory>/scripts/validate.py" --slug "<slug>" --project-root "<project-root>"`. Exit 0: all checks passed (parse JSON). Exit 1: findings present (parse JSON). If the script exits with a non-zero, non-1 status or produces non-JSON output, treat mechanical validation as unavailable. If `--minimal` is active (Layer 2 already skipped), proceed to GATE 2 with: "Both validation layers unavailable — review manually." Otherwise, proceed to qualitative validation only.

**Layer 2 — Qualitative**: Delegate to a subagent with this prompt: "Read the validation criteria at `<skill-directory>/references/task-validation-criteria.md`. Then validate the task document at `spec-driven/<slug>/tasks.md` and its bundle files at `spec-driven/<slug>/bundle-N.md`. Read the source design at the path in `design_source` frontmatter and spec at `spec_source` frontmatter. Apply every rule in the criteria. Return JSON matching the output schema in the criteria file." The subagent returns the Validator Schema JSON defined in task-validation-criteria.md.

Merge findings before presenting. If the qualitative validation subagent fails or returns output that does not parse as valid JSON or is missing the required `results` array, treat it as a failure and retry the delegation once. If the second attempt also fails, skip qualitative validation. On retry: `[Retrying validation...]`

**Blocking findings** (TQ-6, TQ-7): Structural problems that must be resolved before finalization.
**Advisory findings** (all others): Quality signals. Present with rule ID and evidence.

**Both layers unavailable**: If mechanical validation (Layer 1) fails AND qualitative validation (Layer 2) is unavailable, proceed to GATE 2 with a warning: "Both validation layers unavailable — review manually."

### Load Task Template

Read the template at [assets/task-template.md](assets/task-template.md) now (the output backend reference was loaded at Phase 0 backend detection; the template is needed here for finalization structure and graph backend export fallback).

### GATE 2: Task Review

NEVER proceed without the user's actual response — self-answering produces decompositions the user has not reviewed.

Present: slice structure, STEP count per slice, bundle summary, parallel annotations, conflict analysis highlights, and validation findings (if any).

If blocking findings (TQ-6, TQ-7) are present, do not offer "Looks good — finalize." Present only "Adjust steps or bundles" / "Regenerate" until blocking findings are resolved. Re-validate after adjustments.

Structured input: "Looks good — finalize" / "Adjust steps or bundles" / "Regenerate"

On "Adjust": follow up conversationally, apply changes. Re-validate if the adjustment changes STEP dependencies, bundle assignments, file paths, or adds/removes STEPs. Skip re-validation for text-only changes to intent wording, implementation guidance, titles, or verify clause phrasing.
On "Regenerate": discard and return to Phase 1 (retaining Phase 0 context).

**Open question sweep**: Check for unresolved Open Questions from design/spec. Document assumptions.

### GATE 3: Commit Decision

NEVER run `git add` or `git commit` without the user's actual response — unapproved commits cannot be undone and may include structural issues the user would have caught at review.

Write mechanics differ by backend — see the loaded output reference for backend-specific operations.

On "Looks good — finalize":
1. Write `bundle-N.md` per bundle (self-contained execution units)
2. Write `progress-bundle-N.md` per bundle (all STEPs `pending`)
3. Compute SHA-256 hashes of design and spec; include as `design_hash` and `spec_hash` in the format `sha256:<hex-digest>`
4. Update frontmatter from `status: draft` to `status: final`, set `validation` based on which validation layers ran, set `title` to `Tasks: [Feature Name]` using the design's feature name, set `version` to `2.0`, set `date` to the current ISO date, and write `tasks.md`

**Validation field mapping**: `subagent` if qualitative validation (Layer 2) ran, regardless of mechanical validation outcome. `fallback` if only mechanical validation (Layer 1) ran. `skipped` if both layers were unavailable.
5. If `spec-driven/README.md` does not exist, run container setup (see task-guide.md)
6. Delete session sidecar

Write order matters: bundle files first, then tasks.md with final status, then sidecar deletion. If interrupted after step 4, all referenced bundle files exist. If interrupted before step 4, the sidecar still exists and enables resume.

Structured input: "Yes — commit" / "No, I'll commit later"

If yes: `docs(task): add <slug> task decomposition`

Present next steps: "Run `/sds.execute <slug>` to begin execution."

---

## Handling Unknowns

| Pattern | Detection | Response |
| --- | --- | --- |
| Ambiguous AC | AC could map to multiple file changes | One clarifying question, then conservative decomposition. Note assumption. |
| Missing file paths | Design's File Inventory has gaps for an FR | Use Glob inventory to infer. Tag: `[Inferred:Glob]`. |
| Conflicting dependencies | Two STEPs create a dependency cycle | Identify weakest link, propose break, ask user. |
| XL STEP | STEP decomposes to XL effort | Present the XL STEP with a recommended split point and offer: "Split as suggested" / "Keep as-is" / "Adjust split". Do not split autonomously. (See STEP Production, Effort.) |
| Missing design artifact | No Findings or Decisions for an FR area | Note gap. Write intent from spec ACs alone (reduced domain specificity). |
