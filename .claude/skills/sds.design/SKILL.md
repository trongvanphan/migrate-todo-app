---
name: sds.design
description: |
  Research codebase patterns and produce architectural design decisions from a specification.
  Use when someone says "design this", "create a design", "architectural design",
  "research the approach", "I need a design for", or "explore the architecture".
---

# Architectural Design

Research codebase patterns, surface coding standards, and produce architecture decisions from a specification. Do not decompose into implementation steps or assign effort estimates — the task skill handles decomposition using the design as input.

## Trigger

```bash
/sds.design user-auth
/sds.design user-auth --context docs/architecture.md
/sds.design user-auth --context docs/company-adrs/
/sds.design --from docs/prd.md
```

## Flags

| Flag | Description |
| --- | --- |
| First argument (slug) | Slug identifying the spec. Resolves to spec data via detected backend: markdown reads `spec-driven/<slug>/spec.md`, graph queries FR/NFR nodes by slug. |
| `--from <path-or-url>` | Alternate input source (Tier 1/2/3 — see design-guide.md). Markdown backend only — graph backend requires a populated spec (redirect to `/spec --from` first). Slug derived from input using this precedence: (1) YAML frontmatter `title` field if present, (2) first markdown heading (any level), (3) filename without extension, (4) for URLs, extract the last non-empty path segment and strip query parameters and fragments — if the segment is empty, numeric-only, or a generic term (index, page, doc, api), prompt the user for a short identifier. Normalize the chosen value: lowercase, replace non-alphanumeric characters with hyphens, collapse consecutive hyphens, truncate to 64 chars. When using the slug in shell commands, always quote interpolated paths. Present the derived slug at the Research Scope Review for confirmation. |
| `--context <path>` | Additional context: ADRs, architecture docs, steering docs, technical constraints. Accepts a file or directory path. When a directory, reads `.md` files only (one level, no recursion). |

## Output

- Creates design file at: `spec-driven/<slug>/design.md`
- Two output backends (detected in Phase 0):
  - **Markdown** (default): reads `spec-driven/<slug>/spec.md`, writes design.md — [references/output-markdown.md](references/output-markdown.md)
  - **Graph**: reads FR/NFR nodes by slug, writes Finding/Decision/Standard nodes via `sds` CLI — [references/output-graph.md](references/output-graph.md)

---

## Tool Usage

**Structured input**: For all bounded-answer questions (confirmations, yes/no, select-from-list, or any question where valid responses can be enumerated), use the platform's interactive question or prompt mechanism — not inline text. Present options as selectable choices. Use conversational text only for genuinely open-ended questions (describing constraints, explaining context).

Never present bounded options as plain-text numbered or lettered lists — always use the interactive mechanism.

**Progress milestones**: Emit status at key transitions. Phase 0 uses `[N/M]` numbered format. Phases 1-2 use label prefixes (`[Research]`, `[Synthesis]`, `[Validation]`).

**Mandatory interaction gates**: This skill has four gates — all four are mandatory. The first three fire on every path; the fourth fires after finalization completes.

1. **Research Scope Review** (end of Phase 0): Present context summary, planned research scope, and company constraint solicitation. The user confirms, adjusts, or provides additional context before research begins.
2. **Research Findings Review** (end of Phase 1): Present research findings, approach tradeoffs, and resolved uncertainties. The user directs key architectural decisions before synthesis.
3. **Design Review gate** (Phase 2): Present the complete design for user review before finalization.
4. **Commit Decision gate** (Phase 2): Offer to commit the finalized design. Separate from design approval.

**Wait for user response**: After presenting structured input at any gate, stop generating and yield control to the user. Generating or inferring a response corrupts the design — the user's domain knowledge is irreplaceable at gate decisions. This applies to all structured input in this skill, not just the named gates.

**Commit constraint**: NEVER run `git add` or `git commit` without first receiving explicit user approval at the Commit Decision gate — committing is a separate decision from design approval, and the user may want to review files before committing.

---

## Phase 0: Context Gathering (Always Runs)

**Before starting**: Read this reference file — it contains detailed guidance that this document summarizes:
- [references/design-guide.md](references/design-guide.md) — three-tier input model, test approach signals, research output contract, file inventory format, AD template, standards format, sidecar lifecycle

Runs on every invocation before any research. Gathers and analyzes all available context.

**Backend detection** (silent, first step): Check if `sds` and `dolt` are available in PATH by running `which sds && which dolt`. If both are available, use the **graph backend**. If either is unavailable, use the **markdown backend** (default). Remember the detected backend for this session. Do not load the output reference yet — load at Design Draft step 9 in Phase 2.

**Steps:**

Emit: `[1/4] Checking for existing sessions...`

**Directory bootstrap**: Ensure `spec-driven/.sessions/` exists before any file writes. Run `mkdir -p "spec-driven/.sessions/"`. The slug-specific directory (`spec-driven/<slug>/`) is created later during artifact write — do not create it here (the slug may change at the Research Scope Review for `--from` inputs).

1. **Resolve spec input**:
   - If both slug and `--from` provided: stop with guidance: "Provide either a slug or `--from`, not both."
   - If slug provided: read spec via detected backend. Markdown: read `spec-driven/<slug>/spec.md`. Graph: query FR and NFR nodes via `sds query frs --slug "<slug>" --project-root "<project-root>" --format json` and `sds query nfrs`, plus spec-stage Constraint, Assumption, and Risk nodes via `sds query constraints`, `sds query assumptions`, `sds query risks`. Verify spec data exists. If FR and NFR queries both return empty results, stop with guidance: "No spec found for slug '[slug]'. Run `/spec` to create one first." If any `sds query` command fails, fall back to the markdown backend for this session — remember the backend as markdown for sidecar creation in step 2. Inform the user: "Graph query failed — falling back to markdown backend." Read `spec-driven/<slug>/spec.md` instead and continue to step 2. Context enrichment (Phase 0 step 5) proceeds normally regardless of backend fallback.
   - If `--from` provided AND graph backend detected: if `--context` was also provided, verify the `--context` path exists before emitting redirect guidance — if invalid, include a warning: "Note: context path '[path]' was not found." Stop with guidance: "The graph backend requires a populated spec. Run `/sds.spec --from <path>` first to create one, then run `/sds.design <slug>`." If `--context` was provided (and valid), include it in the redirect guidance: "Run `/sds.spec --from <path>` first, then `/sds.design <slug> --context <context-path>` to carry your context forward."
   - If `--from` provided AND markdown backend: verify the source file or URL is accessible. If the file does not exist, stop with guidance: "File not found at '[path]'." If `--from` is a URL, fetch the content using `curl -sfL "<url>"` (or the platform's web fetch tool if available). The `-f` flag causes curl to fail on HTTP errors (status >= 400) instead of returning error pages as content. If the fetch returns an error or empty content, stop with guidance: "Could not fetch '[url]' — verify the URL is accessible." Read the source document. Classify tier (Tier 1/2/3 — see design-guide.md). Tier 3 (unstructured): redirect to spec skill. If `--context` was also provided, include it in the redirect guidance: "Run `/sds.spec --from <path>` first, then `/sds.design <slug> --context <context-path>` to carry your context forward." Tier 2: assign synthetic FR-SN identifiers. Tier 1: use identifiers directly. If `spec-driven/<derived-slug>/spec.md` already exists, compare content — if they differ, inform the user: "A spec already exists at `spec-driven/<derived-slug>/`. Provide a different slug or use that spec directly with `/design <slug>`."
   - If neither slug nor `--from` provided: stop with guidance: "Provide either a slug or `--from` to specify input."
2. **Session check**: The slug for sidecar path resolution is fully determined by step 1 (including `--from`-derived slugs). Check for existing design sidecar at `spec-driven/.sessions/<slug>.design.json`.

   **Sidecar found** — evaluate the sidecar state:

   **2a. Stale sidecar check**: Check if `spec-driven/<slug>/design.md` exists with `status: final` in the design file's frontmatter. If so, the sidecar is stale (interrupted between finalization steps 1 and 2): delete the stale sidecar. Also delete `spec-driven/.sessions/<slug>.codebase-analyzer.json` if that file exists, inform the user "Found a stale session sidecar — the design was already finalized. Cleaned up." Offer "Regenerate" / "Review existing design" using structured input — response handling follows "2c. No sidecar path" below.

   **2b. Active sidecar resume**: If the sidecar is not stale, present resume options using structured input: "Resume from Phase [N]" / "Start fresh".
   - On "Start fresh": delete the existing sidecar and `spec-driven/.sessions/<slug>.codebase-analyzer.json` if it exists. Proceed to step 3.
   - On "Resume from Phase [N]":
     1. Re-run backend detection. If the sidecar contains `backend: "markdown"`, use the markdown backend regardless of PATH detection (a previous session's graph fallback must be honored).
     2. Read `phasesCompleted` and `partialData` from the sidecar.
     3. Re-read the spec to detect changes (compare `specHash`).
           - **Spec inaccessible** (URL unreachable, file deleted): inform the user and present structured input: "Continue with existing data" / "Provide new spec path" / "Start fresh". On "Provide new spec path": re-run input resolution (Phase 0 step 1 logic) against the new source — including tier classification and slug derivation. Update sidecar `specSource` and `specHash`.
           - **Spec changed**: present structured input "Restart from Phase 0" / "Continue with existing data (may use stale research)". On "Restart": delete the sidecar and proceed to step 3. On "Continue": proceed with resume, but note in the design output that the spec changed after research was conducted.
           - **Spec unchanged**: proceed with resume using the `phasesCompleted` value from the sidecar (see table below).
     4. Resume by `phasesCompleted` value:

        | `phasesCompleted` | Resume behavior |
        | --- | --- |
        | Empty (Phase 0 interrupted) | Present "Resume Phase 0" / "Start fresh" using structured input. On "Resume Phase 0": re-run Phase 0 from step 1. On "Start fresh": delete sidecar, proceed to step 3. |
        | `[0]` (Phase 0 complete) | Skip to Phase 1. Re-read the spec and codebase-analyzer output at `spec-driven/.sessions/<slug>.codebase-analyzer.json` (do not re-run codebase analysis). The Research Scope Review still fires. |
        | `[0, 1]` (Phase 1 complete) | Skip to Phase 2 § Design Draft using `partialData.findings`, `partialData.standards`, `partialData.fileInventory`, `partialData.approachRecommendations`, `partialData.resolvedUncertainties`, `partialData.dependenciesAndCoupling`, `partialData.constraints`, `partialData.assumptions`, and `partialData.risks`. |

     5. If `--context` was provided, read context files (per Phase 0 step 5) regardless of resume phase. When resuming Phase 1 complete with new `--context`, treat the new context as supplementary input during Design Draft — it may inform additional findings or revised decisions, but do not discard existing `partialData`.

   **2c. No sidecar path** — also used for stale-sidecar response handling.

   If `spec-driven/<slug>/design.md` exists: offer "Regenerate" / "Review existing design" using structured input.
   - On "Regenerate": proceed with Phase 0 from step 3 (extract identifiers), overwriting the existing design.md during Phase 2 finalization.
   - On "Review existing":

     Emit: `[Review] Validating existing design...`

     1. Read `spec-driven/<slug>/design.md`. If the file does not exist or is empty, inform the user: "Design file not found at `spec-driven/<slug>/design.md`." and proceed to step 3 (extract identifiers) to regenerate.
     2. Extract frontmatter and all sections (Findings, ADs, Standards, File Inventory, Open Questions).
     3. If `--context` was provided, read context files (per Phase 0 step 5) and include as additional validation context.
     4. Load the output backend reference (graph or markdown). If the design's frontmatter indicates a different backend than the current session detected:
        - Graph-created design, graph unavailable: fall back to markdown validation and inform the user: "Design was created with the graph backend, but [reason unavailable]. Validating as markdown." Instruct the qualitative validator to skip DQ-20 (references file existence) — graph-created designs may store research and standards content in the graph rather than in `references/` files.
        - Markdown-created design, graph now available: use markdown validation — the design content exists only in markdown files, not in the graph.
     5. For the graph backend: query the graph for Findings, Decisions, and Standards to supplement the design.md content. If queries fail, fall back to validating design.md as markdown only.
     6. Run Layer 1 and Layer 2 validation against the existing design.
     7. Jump to Phase 2 § Design Review with extracted data and validation results.

   If `spec-driven/<slug>/design.md` does not exist: proceed to step 3.

   **Sidecar creation** (all paths that reach step 3): Create the session sidecar at `spec-driven/.sessions/<slug>.design.json` with the initial schema: `slug`, `backend` (detected or overridden), `specSource` (spec path or `--from` path), `specHash` (SHA-256 of the spec content), empty `phasesCompleted`, current timestamp. See design-guide.md § Session Sidecar for the full schema. This enables recovery if the session is interrupted during Phase 0.

3. **Extract identifiers**: Parse FR-N, AC-N.M, NFR-N identifiers, priorities, dependencies, and open questions from the spec. Extract existing Constraint, Assumption, and Risk nodes (graph) or corresponding Scope subsections (markdown) — these are spec-stage artifacts (created during the spec skill run) that inform research and must be respected by design decisions.

Emit: `[2/4] Gathering context from codebase and external sources...`

4. **Delegate codebase analysis** to subagents (see Subagent Delegation below). In multi-project mode, step 6 (multi-project resolution) must complete before dispatching codebase analysis subagents — resolution determines which project directories to scan.
5. **Context enrichment** (may run in parallel with step 4 in single-project mode, or with step 6 in multi-project mode): If `--context` provided, read context files. If the `--context` path does not exist, inform the user: "Context path not found at '[path]'. Proceeding without additional context." and continue. If `--context` is a directory, read all `.md` files in it (glob `"<dir>"/*.md`, one level, no recursion). If the directory contains no `.md` files, inform the user: "No .md files found in '[path]' (only .md files are read from context directories). Proceeding without additional context." and continue. Tag context-sourced content with `[Context]` provenance. If `--from` provided Tier 2 input with synthetic FR-SN identifiers, treat FR-N references in context documents as informational background — do not map them to synthetic identifiers.

Emit: `[3/4] Resolving test approach and project structure...`

6. **Multi-project resolution** (see below — must complete before step 4 dispatches codebase analysis subagents in multi-project mode).
7. **Test approach resolution**: Resolve test approach to one of: `tdd`, `test-after`, `none`. Then resolve `test_capabilities` (unit/integration/e2e framework detection). When a level is null and the architecture suggests it would be valuable, include a recommendation in the design output. See design-guide.md for both the 6-signal detection table and the test capabilities detection heuristic.

Emit: `[4/4] Analyzing context and determining research scope...`

Steps 7-9 are sequential — each informs the next.

8. **Adaptive flow determination** (see Adaptive Flow below).
9. **Prepare research scope**: Based on spec FRs/NFRs, codebase analysis results, and context, determine which architectural aspects require research. Each aspect maps to a question derived from the requirements (e.g., "How does the existing codebase handle authentication?" for an auth-related FR).

### Multi-Project Resolution (Phase 0)

When the workspace includes multiple project directories, resolve logical project names to local filesystem paths. Resolution is ephemeral — never written to committed artifacts.

**Project Map Schema**:
- `projects` array: each entry has `name` (string, `[a-z0-9-]+`, unique, must not contain `::`) and `identity` (string, `hostname/org/repo` format — no protocol prefix, no `.git` suffix; use `local` for non-git directories)
- `artifact_home`: which project hosts `spec-driven/` (defaults to primary working directory's project if omitted)
- When `projects` is absent AND only one workspace directory exists → single-project mode, skip resolution entirely (zero overhead)

**Resolution algorithm**:
1. Read `projects` from the spec's `## Projects` section (YAML code fence) via `spec_source` in design frontmatter — inheritance chain
2. If absent:
   a. Check workspace: if only one directory exists → single-project mode, skip resolution
   b. If multiple workspace directories exist → offer **late-entry discovery**: "This spec has no `projects` block, but your workspace has N directories. Does this work span multiple projects?" If yes → run project picker, write `projects` to the design's frontmatter. If no → single-project mode.
3. Read workspace directories from the Environment section in the system prompt:
   ```
   # Environment
    - Primary working directory: /absolute/path/to/project-a
    - Additional working directories:
      - /absolute/path/to/project-b
   ```
4. For each project in the map:
   a. Scan each workspace directory: run `git -C "<dir>" remote get-url origin`. If the command returns non-zero (not a git repository), skip remote URL matching for that directory and proceed to basename match.
   b. Normalize the remote URL: strip protocol (`https://`, `git@`, `ssh://`), strip `.git` suffix, strip trailing slashes, lowercase → yields `host/org/repo`
   c. If no match by origin: try all remotes via `git -C "<dir>" remote -v`
   d. Compare normalized URL with the project's `identity` field (also normalized)
   e. On match → record: `project.name → <dir absolute path>`
   f. No match by remote URL → try basename match: `basename "<dir>" == project.name`
   g. No match by either → prompt user: "Which directory contains '[project-name]'?"
5. Validate: all projects must resolve. If any fail after prompting → skip that project's codebase scan, flag gap in design
6. Store resolved map in session memory (not on disk, not in committed artifacts)

**Design-specific behavior**: Inherit `projects` from spec. If the upstream spec has no `projects` and the workspace is multi-directory, offer late-entry discovery and write `projects` to the design's own frontmatter. On resolution failure, skip that project's codebase scan and flag the gap — do not hard-stop.

**Per-project CLAUDE.md**: Read `CLAUDE.md` from each resolved project directory (not just the primary). Claude Code does NOT auto-load CLAUDE.md from additional directories. Skills must read them explicitly to capture per-project conventions, patterns, and constraints. These are primary sources for standards extraction in Phase 1.

**Developer doesn't have all projects cloned**: Offer: "I don't have this project locally — skip it." Skip codebase analysis for that project and flag the gap in the design.

### Subagent Delegation (Phase 0)

Before research, delegate context gathering to subagents:

1. **Codebase analysis**: Dispatch a subagent to perform deep codebase analysis. The subagent scans the project for architecture, patterns, tech stack, and files relevant to the spec's functional requirements.

   **Single-project** (no `projects` block): Dispatch one subagent against the project root. The subagent prompt must include:
   - Instruction to scan the project at the given root path for architecture patterns, component structure, tech stack, integration points, and files relevant to the spec's FRs
   - The list of FR-N identifiers and brief descriptions from the spec
   - Instruction to return structured JSON with: `componentMap` (array of component descriptors), `patternInventory` (array), `integrationPoints` (array), `relevantFiles` (array of file paths), `architecturalPattern` (string), `techStack` (object with sub-fields: `testFramework` string or null, `testCapabilities` object with `unit`/`integration`/`e2e` keys each string or null)
   - Instruction to exclude files in `spec-driven/` from scanning

   **Multi-project** (`projects` block present): Dispatch one subagent per resolved project directory, running in parallel. Each receives the same prompt structure scoped to its project path. Per-project results aggregate as `{ "project-name": result, ... }`. If a subagent fails, its project falls back to inline scanning; other projects' results are preserved.

2. **Lightweight file reads** (always, performed by the orchestrator directly — not a subagent): While codebase analysis subagents are running, read project-level signals:
   - Read `CLAUDE.md` (project-level, then global) from each resolved project
   - Read `README.md`
   - Read package manifest (`package.json`, `pom.xml`, `Cargo.toml`, etc.)
   - Top-level directory listing

   Do NOT read files in `spec-driven/` during lightweight file reads — previous artifacts may pollute context. (The spec itself is already loaded in step 1.)

Codebase analysis subagents and lightweight file reads are independent — do not wait for one before starting the other.

### Consuming Subagent Results

Write the codebase-analyzer output to `spec-driven/.sessions/<slug>.codebase-analyzer.json`. Verify the file was written successfully. If the write fails, log a warning and dispatch research subagents without a codebase-analyzer path — they perform their own file exploration as part of research. Research subagents in Phase 1 receive this path — they read the file independently rather than receiving embedded content.

Map codebase-analyzer deep output to research planning:
- `componentMap` → architectural baseline, component boundaries
- `patternInventory` → existing patterns to follow or adapt
- `integrationPoints` → system dependencies and coupling points
- `relevantFiles` → files to explore in Phase 1 research
- `architecturalPattern` → approach classification (new/extension/refactor)
- `techStack.testFramework` → feed into test approach resolution
- `techStack.testCapabilities` → feed into test capabilities detection (unit/integration/e2e framework availability)

Tag subagent-sourced content: `[Codebase:Analyzer]` — conversational output only, not written to the design file.

### Subagent Fallback and Recovery

Each subagent gets 1 retry before the fallback applies. On retry, display the notification from the table below.

| Subagent | On Failure | On Retry |
| --- | --- | --- |
| codebase analysis | Fall back to inline scanning (CLAUDE.md, README, manifest, directory listing, up to 5 targeted source files) | `[Retrying codebase analysis...]` |
| research subagent | Mark that research aspect as "unexplored", note in design output under Findings | `[Retrying research on [aspect]...]` |
| validator | Skip qualitative validation, proceed with mechanical results only | `[Retrying validation...]` |

For **partial subagent results** (valid response but `findings` or `approaches` is empty):
- **Missing findings**: perform targeted inline scanning — read source files relevant to the aspect, derive findings with `source: codebase` and `confidence: low`.
- **Missing approaches**: derive a single recommended approach from codebase patterns and CLAUDE.md conventions. Mark with `source: training_knowledge` and `confidence: low`. Flag at the Research Findings gate that approach evaluation for this aspect was limited.

Do not discard the successful portions of the response.

For **partial codebase-analyzer results**: if `componentMap` is empty but `relevantFiles` is non-empty, proceed with `relevantFiles` as the primary input for research planning and file inventory. If both are empty, treat as complete failure (fall back to inline scanning per the table above).

When codebase analysis falls back to inline scanning, map results to adaptive flow classification: if inline scanning finds application source files, classify as partial context. If no application source files found, classify as minimal context. Rich context requires a successful codebase-analyzer result.

#### GATE: Research Scope Review

NEVER proceed to Phase 1 without completing this gate — research without user-validated scope produces findings the user didn't ask for.

Present the context summary and planned research scope. For rich-context flows with few FRs, keep this concise (3-5 lines). For partial/minimal flows, include the full structure:

```
Here's what I gathered:
- Spec: [Tier 1/2] with [N] FRs, [M] NFRs
- Slug: [derived-slug] (derived from [source])  ← only when --from was used
- Spec-stage artifacts: [N] constraints, [N] assumptions, [N] risks
- Codebase: [tech stack], [N components], [key patterns]
- Test approach: [tdd/test-after/none] [source annotation]
- Test capabilities: unit=[framework or null], integration=[framework or null], e2e=[framework or null] [recommendations if applicable]
- Additional context: [what was provided]

Planned research scope:
- [Aspect 1]: [question derived from FR-N]
- [Aspect 2]: [question derived from FR-M]
- [Aspect 3]: [question derived from NFR-N]
([N] research subagents, estimated [time])

Assumptions from Open Questions:
- [Question] → [assumed default]
```

**Company constraint solicitation** (always include): "Are there company-wide ADRs, architecture guidelines, or technical constraints that should inform this design? Provide file paths or describe them."

Present as interactive choices (not plain text): "Proceed with this scope" / "Adjust the scope" / "Add more context"

Update the sidecar: record `phasesCompleted: [0]` and `adaptiveFlow`. This marks Phase 0 as complete for session recovery.

On "Adjust": follow up conversationally, update scope, re-present. This includes slug changes — for `--from`-derived slugs, the user may correct the slug at this gate. If the slug changes: rename `spec-driven/.sessions/<old-slug>.design.json` to `spec-driven/.sessions/<new-slug>.design.json`. Rename `spec-driven/.sessions/<old-slug>.codebase-analyzer.json` similarly if it exists. Update the `slug` field in the sidecar. If `specSource` contains the old slug, update it to reference the new slug. On "Add more context": accept file paths or descriptions, integrate into research scope, re-present.

NEVER generate a response on the user's behalf — inferring the user's answer corrupts the design. Wait for their actual answer.

---

## Adaptive Flow

Based on Phase 0 output, adapt the research approach. Evaluate conditions in order: rich → partial → minimal. Use the first matching flow. The mandatory Research Scope Review still fires regardless of context richness.

- **Rich context** — Compress Phase 0+1. ALL of:
  - Tier 1 spec input
  - Codebase-analyzer returned a successful deep analysis (componentMap is non-empty, or CLAUDE.md describes architecture and conventions)
  - The project is not greenfield (application source files exist in the codebase-analyzer output)
  - 5 or fewer FRs in the spec
  - The spec has no Open Questions section, or all Open Questions have confirmed defaults

  When rich context applies:
  1. Standards extraction runs (per Phase 1 § Standards Extraction).
  2. Do not dispatch research subagents.
  3. Derive Findings (F-N) from codebase-analyzer output (`componentMap`, `patternInventory`, `integrationPoints`) and from spec analysis. Mark codebase-derived findings with `source: codebase` and spec-derived findings with `source: spec`, `confidence: high`.
  4. Build the file inventory from codebase-analyzer `relevantFiles` and `componentMap`.
  5. Identify dependency relationships from `integrationPoints`.
  6. Categorize constraints/assumptions/risks from codebase-analyzer output and spec analysis.
  7. All derived findings (steps 3-6) constitute the complete finding baseline for Phase 2. Proceed to the Research Findings Review gate with a condensed findings summary.
- **Partial context** — Standard flow. Dispatch 2-3 research subagents for aspects not covered by Phase 0. ANY of:
  - Tier 2 spec input
  - Codebase-analyzer returned limited results (some files found but incomplete analysis) or ran in fallback mode — does not include greenfield (no application source files found), which falls through to minimal. Greenfield classification: codebase-analyzer found no application source files (`.ts`, `.py`, `.java`, `.go`, `.rs`, `.rb`, etc.). Configuration files alone (`package.json`, `README.md`, `Dockerfile`) do not prevent greenfield classification.
  - 6-9 FRs
  - Some Open Questions that can be resolved with defaults
- **Minimal context** — Full research flow. Dispatch 3-5 research subagents. ANY of:
  - Greenfield project (codebase-analyzer found no application source files)
  - Complex spec with 10+ FRs
  - New system or major refactor

**Default**: If no flow matches, use the partial context flow. When conditions match multiple flows, the first-match rule applies. If the selected flow proves insufficient during research, note the gap at the Research Findings Review gate so the user can adjust scope.

---

## Phase 1: Research

Non-interactive phase — proceeds automatically after Research Scope Review approval. If rich-context adaptive flow was selected, this phase is compressed: execute the rich-context steps defined in the Adaptive Flow section above (which includes standards extraction as step 1 — do not run standards extraction separately), then proceed to the Research Findings Review gate.

Emit (partial/minimal flows): `[Research] Dispatching [N] research subagents...`
Emit (rich-context flow): `[Research] Deriving findings from codebase analysis...`
Emit (rich-context flow, before standards extraction): `[Research] Extracting standards from project conventions...`

### Research Subagent Dispatch

Dispatch parallel research subagents. Each subagent reads [references/research-subagent-instructions.md](references/research-subagent-instructions.md) as its first action, then investigates one FR-driven architectural aspect — analyzing the codebase, researching technical approaches, evaluating tradeoffs, and recommending a direction.

Aspects are derived from FRs/NFRs, not a fixed list. Frame each aspect as an aspect question, not a codebase observation question. Each subagent receives:
- The aspect question (e.g., "What approach should we use for real-time notifications given the existing Express + PostgreSQL stack?")
- Path to the codebase-analyzer output (pass the path — do not embed file content in the prompt)
- Project root path
- Tech stack summary from codebase-analyzer (so research targets the right ecosystem)

Each returns structured JSON per the research output contract in design-guide.md — including approach recommendations and tradeoff analysis.

All research subagents run in **parallel**. In multi-project mode, scope each subagent to the project(s) relevant to its aspect.

See design-guide.md for research subagent sizing guidelines (when to dispatch 2 vs 3 vs 5).

Emit (every ~60 seconds if subagents are running): `[Research] [N/M] aspects complete...`

### Standards Extraction

After research subagents return (or immediately in rich-context flow):

1. Read each resolved project's `CLAUDE.md` for coding standards, conventions, and constraints. If `CLAUDE.md` does not exist for a project, skip standards extraction for that project and proceed with available sources.
2. If `CLAUDE.md` references steering documents by relative path (e.g., "see docs/coding-standards.md"), read the referenced steering documents — one level only, no recursive following. If a referenced document is unreadable, note the gap and proceed.
3. If the user provided company ADRs or constraints at the Research Scope Review, read and extract standards from those documents.
4. Categorize each standard with typed applicability metadata: `domain`, `file_type`, `action_type`, `source_document`. See design-guide.md for the standard format (S-N).

### Consuming Research Results

Emit: `[Research] Synthesizing findings...`

1. Parse each research subagent's JSON response. For each finding, assign an ID (F-N) and record: source (`codebase`, `web_research`, `training_knowledge`, or `spec`), confidence (`high`/`medium`/`low`), related FRs, related files, and implications. Collect discovered `patterns` from each subagent — merge with codebase-analyzer `patternInventory` and feed into the Technical Approach narrative and File Inventory.
2. Collect **approach recommendations** from each subagent. Each aspect may have 2-4 approaches with tradeoff analysis and a recommended direction. These feed into the Research Findings gate.
3. Collect **resolved uncertainties** — technical questions answered during research, with evidence.
4. Build the **file inventory** — a flat table of files to create or modify, with FR associations and rationale. In multi-project mode, use `project::path` notation. See design-guide.md for the format.

Emit: `[Research] Building dependency map and categorizing artifacts...`

5. Identify dependency and coupling relationships between feature areas (shared files, shared interfaces).
6. Classify research discoveries that are not findings into typed artifacts — technical constraints, assumptions, and technical risks — for formalization in Phase 2 step 7. Do not assign F-N IDs to these; they are typed artifacts, not findings.
7. Verify all research subagents returned results. If any aspect is marked "unexplored" (subagent failure), note the gap prominently. For unresolved ambiguities in research results, apply the patterns in Handling Unknowns below.

#### GATE: Research Findings Review

NEVER proceed to Phase 2 without completing this gate — synthesizing a design without user-validated architectural direction produces decisions the user didn't ask for.

Present research results organized by aspect. For each aspect:
- Key findings (summarized, not raw subagent output)
- Approaches evaluated with tradeoffs and the recommended direction
- Resolved uncertainties

Where multiple viable approaches exist, highlight the tradeoff and the recommendation. The user selects the direction — do not assume the recommended approach is accepted.

For rich-context flows (no research subagents dispatched), present a condensed findings summary from codebase-analyzer output. The gate still fires.

Structured input: "Proceed with recommendations" / "Adjust approach for [aspect]" / "I have additional context"

On "Adjust": follow up conversationally for the aspect to change, present alternatives, update the selected direction, re-present. On "I have additional context": accept file paths or descriptions, integrate, re-present.

Update the sidecar: record `phasesCompleted: [0, 1]` and all `partialData` fields (findings, standards, fileInventory, approachRecommendations, resolvedUncertainties, dependenciesAndCoupling, constraints, assumptions, risks). This marks Phase 1 as complete for session recovery.

NEVER generate a response on the user's behalf — inferring the user's answer corrupts the design. Wait for their actual answer.

---

## Phase 2: Design Synthesis & Review

Transform findings into design artifacts, validate, and present for review.

### Design Draft

Emit: `[Synthesis] Building architecture decisions from findings...`

The user confirmed architectural directions at the Research Findings gate. Synthesis formalizes those directions into the design artifact. Steps 1-7 are sequential — each builds on the previous. Steps 8 and 9 may run in parallel.

1. **Write Technical Approach**: Per-feature-area narrative — what exists, what changes, the chosen approach, and key patterns to follow. This section ties findings and ADs into a coherent story for the task skill.
2. **Synthesize Findings into Architecture Decisions (AD-N)**: For each non-trivial technical choice confirmed at the Research Findings gate, create an AD-N entry with Context, Decision, Rationale, and Alternatives Considered. Each AD references the findings (F-N) that informed it. See design-guide.md for the AD template and creation criteria.
3. **Formalize Standards (S-N)**: Confirm typed applicability metadata for each standard. Standards from `CLAUDE.md` apply to the originating project only in multi-project mode. Standards from user-provided company documents or cross-project steering docs apply to all projects.
Emit: `[Synthesis] Writing dependencies and cross-referencing spec values...`

4. **Write Dependencies and Coupling**: Feature areas sharing files or interfaces, with recommendations for the task skill on sequencing and shared structure (e.g., "consider hoisting shared model into walking skeleton").
5. **Write Spec Deviations**: Cross-reference design values against spec counterparts. For any value the design changes or reinterprets, document the deviation with the original spec value, the design value, and rationale. If no deviations exist, write "None — all spec values preserved."

Emit: `[Synthesis] Formalizing constraints, standards, and file inventory...`

6. **Write Resolved Uncertainties**: Technical questions answered during research, with evidence. Carried from research subagent output.
7. **Formalize design-stage Constraints, Assumptions, and Risks**: Write technical constraints (`source: "codebase"` or `source: "technical"`), assumptions (`source: "design"`), and risks (`source: "codebase"` or `source: "research"`) discovered during Phase 1. Design-stage constraints, assumptions, and risks supplement spec-stage ones. They are NOT Findings — do not assign F-N IDs. Each is a typed artifact with specific downstream semantics. Link Assumptions and Risks to affected FRs via `affects` edges.
8. **Resolve remaining uncertainties**: If findings reveal ambiguities not covered by spec Open Questions or the Research Findings gate, present each ambiguity with the proposed default from the Handling Unknowns table, and ask the user to confirm or override. Use conversational text (not structured input) since these are genuinely open-ended. Document resolutions.
9. **Load the output backend reference** (may run in parallel with step 8). If the sidecar records a backend override from an earlier fallback, use that backend regardless of current PATH detection. Read the appropriate file now:
   - Graph: [references/output-graph.md](references/output-graph.md)
   - Markdown: [references/output-markdown.md](references/output-markdown.md). Also read [assets/design-template.md](assets/design-template.md), [assets/research-template.md](assets/research-template.md), and [assets/standards-template.md](assets/standards-template.md).
10. **Write the design artifact and references/** after steps 8 and 9 are both complete, following the loaded output reference. Both backends produce `spec-driven/<slug>/design.md` (target ~8-12K tokens) plus `spec-driven/<slug>/references/` files. Write all findings to the backend only after synthesis is complete (steps 1-9) — partial writes create misleading provenance chains.

### Validation

Emit: `[Validation] Checking design quality...`

Run two-layer validation after writing the design. Layer 1 and Layer 2 are independent — run them in parallel when possible.

**Layer 1 — Mechanical**: `python "<skill-directory>/scripts/validate.py" --slug "<slug>" --project-root "<project-root>"` where `<skill-directory>` is the directory containing this SKILL.md.
Returns standard validation JSON (`{"pass": bool, "findings": [...]}`). If mechanical validation fails to execute (Python not found, script error, or non-JSON output), skip mechanical validation and note: "Mechanical checks unavailable." Proceed to qualitative validation.

**Layer 2 — Qualitative**: Delegate to a subagent. The subagent reads the backend-appropriate criteria file as its first action, then validates the design:
- Markdown backend: [references/design-validation-criteria-markdown.md](references/design-validation-criteria-markdown.md) — structural + semantic checks
- Graph backend: [references/design-validation-criteria-graph.md](references/design-validation-criteria-graph.md) — semantic focus only (`sds check` handles structural integrity mechanically). Uses iterative subgraph analysis: walks provenance chains (FR→Finding, Finding→Decision, Decision→Standard) individually rather than evaluating the whole design at once.

Expected output: Validator Schema JSON (see the Output Schema section in the criteria file).

Merge mechanical and qualitative findings before presenting to user.

**Fallback**: If the qualitative validator subagent fails, skip qualitative validation and present mechanical results only. If both validation layers are unavailable, proceed to Design Review with a warning: "Both validation layers unavailable — review the design manually." Proceed to review.

#### GATE: Design Review

NEVER proceed past this gate without presenting structured input and receiving the user's actual response — finalizing an unreviewed design commits architectural decisions the user may disagree with.

Present the complete design:
- Technical Approach (per-feature-area summary)
- All Findings (F-N) with sources and confidence
- All Architecture Decisions (AD-N) with rationale and alternatives
- Resolved Uncertainties
- All Standards (S-N) with applicability metadata
- File Inventory
- Dependencies and Coupling
- Spec Deviations (or confirmation of none)
- Constraints (Technical) with source and rationale
- Assumptions with source and affected FRs
- Risks (Technical) with impact, probability, and mitigation
- Test approach (resolved value and source)
- Validation findings (if any)

Structured input: "Looks good — finalize" / "Adjust the design" / "Regenerate"

On "Adjust": follow up conversationally for what to change, apply changes, re-validate if structural changes were made (new ADs, changed findings), re-present. Skip re-validation for wording-only changes. Present edit deltas conversationally — ephemeral to the session, not written to the design file.

On "Regenerate": discard the current design draft. Return to Phase 1 § Research Subagent Dispatch (partial/minimal flows) or Phase 1 § Standards Extraction (rich-context flow) using the existing Phase 0 context. The Research Scope Review does NOT re-fire — scope was already confirmed. Proceed through Phase 1 and Phase 2 normally, producing a fresh design draft.

**Open question sweep**: Verify all spec Open Questions are documented with confirmed defaults. If new questions emerged during research, present them now with proposed defaults before finalizing.

On "Looks good — finalize":
1. Write the final design artifact:
   - Markdown backend: Rewrite `spec-driven/<slug>/design.md` with `status: final`, `created_date` and `last_updated` set to the current ISO 8601 timestamp, and `spec_hash` set to the spec file's SHA-256 hash.
   - Graph backend: Run the final export with `status: final` metadata.
2. After the design file write succeeds: delete the session sidecar at `spec-driven/.sessions/<slug>.design.json` if it exists, and `spec-driven/.sessions/<slug>.codebase-analyzer.json` if it exists
3. If `spec-driven/README.md` does not exist, run first-run container setup (see design-guide.md § Container Setup)

#### GATE: Commit Decision

NEVER run `git add` or `git commit` without receiving the user's actual response to this question. This is a separate decision from design approval. NEVER generate a response on the user's behalf — inferring the user's answer corrupts the design. Wait for their actual answer.

Structured input: "Yes — commit" / "No, I'll commit later"

If yes: stage design artifacts (`git add "spec-driven/<slug>/design.md" "spec-driven/<slug>/references/"`) and commit with message `docs(design): add <slug> architectural design`. If `spec-driven/README.md` was created during container setup, include it in the staged files.

If no: skip commit. The design is already finalized at `spec-driven/<slug>/design.md`.

Present next steps: "Run `/sds.task` to decompose this design into implementation tasks."

---

## Handling Unknowns

| Pattern | Detection | Response |
| --- | --- | --- |
| Ambiguous FR | Vague or multi-interpretable description | One clarifying question, then conservative interpretation. Document the assumption in the design. |
| Missing context | No codebase patterns exist for a required capability | Note as Finding (F-N) with source `training_knowledge`, low confidence. Describe the approach in an AD rather than referencing a pattern. |
| Conflicting constraints | Two standards or ADRs contradict each other | Surface as AD-N with both options and a recommendation. The user resolves the conflict. |
| "Just pick one" | User defers a design choice | Make a reasonable decision, document as AD-N with rationale and alternatives. |
| Unknown integration | External system not accessible for analysis | Note as Finding with low confidence. Flag in design risks section. Recommend the user provide documentation via `--context`. |
