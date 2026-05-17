---
name: sds.spec
description: |
  Create a specification document through interactive elicitation. Use when someone says
  "write a spec", "spec this out", "create a specification", "I need a spec for",
  "spec-driven", or "define requirements for".
---

# Specification Elicitation

Create a specification document through interactive conversation. Guides through structured phases to extract requirements.

## Trigger

```bash
/sds.spec
/sds.spec "User Authentication"
/sds.spec --minimal
/sds.spec --from ./docs/prd.md
/sds.spec --from https://ghe.coxautoinc.com/org/repo/blob/main/docs/brief.md
/sds.spec --from ./docs/prd.md --draft
```

## Flags

| Flag                    | Description                               |
| ----------------------- | ----------------------------------------- |
| First argument (quoted) | Specify feature/capability name directly  |
| `--minimal`             | Skip Phase 4 (NFRs/Success), use defaults |
| `--from <path-or-url>`  | Provide a file path or URL as input context (PRD, brief, meeting notes, etc.) |
| `--draft`               | Synthesize spec from available context, present for validation instead of full interactive flow |
| `--minimal + --draft`   | Generate draft with default NFR placeholders. Skip Phase 4 elicitation and post-elicitation validation. Present draft for user review. |

## Output

- Creates spec file at: `spec-driven/<spec-slug>/spec.md`
- Two output backends (detected in Phase 0):
  - **Markdown** (default): writes spec.md directly from template — [references/output-markdown.md](references/output-markdown.md)
  - **Graph**: writes typed nodes via `sds` CLI, exports spec.md — [references/output-graph.md](references/output-graph.md)

---

## Tool Usage

**Structured input**: For all bounded-answer questions (confirmations, yes/no, select-from-list, priority categorization, or any question where valid responses can be enumerated), use the platform's interactive question or prompt mechanism — not inline text. Present options as selectable choices. Use conversational text only for genuinely open-ended questions (feature descriptions, problem statements, explanations).

Never present bounded options as plain-text numbered or lettered lists — always use the interactive mechanism. This includes clarification questions, confirmation gates, and quality nudges.

See [references/elicitation-guide.md](references/elicitation-guide.md) > Interaction Policy for multiSelect rules, Skip option guidance, and combined exchange details.

---

## Phase 0: Context Analysis (Always Runs)

**Before starting**: Read these reference files — they contain detailed guidance that this document summarizes:
- [references/elicitation-guide.md](references/elicitation-guide.md) — interaction policy, field extraction map, codebase context rules, adaptive flow thresholds, phase-by-phase question details
- [references/rally-integration.md](references/rally-integration.md) — Rally field mappings and import flow

Runs on every invocation before any interactive questions. Analyzes all available context to determine what is already known.

**Backend detection** (silent, before context gathering): Check if `sds` and `dolt` are available in PATH by running `which sds && which dolt`. If both are available, use the **graph backend**. If either is unavailable, use the **markdown backend** (default). Remember the detected backend for this session — it determines which output reference to load at the first write point. Do not load the output reference yet (load at point of action, after Phase 0).

**Context sources (in priority order):**

1. User's trigger message and any inline text
2. Content from `--from` flag:
   - If local path: read the file directly
   - If URL matching a known MCP service (e.g., GHES at `ghe.coxautoinc.com`): use the corresponding MCP tool (e.g., `getGithubRepositoryContent`)
   - If other URL: fetch the URL content
   - If fetch fails: inform the user and ask them to paste the content directly
3. Rally data (if MCP tools are available — offer import as part of this phase)
4. Codebase signals (automatic when code exists in the working directory — see elicitation guide for scan rules)

**Continuation rule**: Phase 0 is non-interactive except where a context source requires user input (session resume, Rally import offer). Automated steps — scanning, fetching, subagent delegation — proceed without pausing.

**First interactive point**: The first structured input after context gathering is the gap analysis presentation or the Adaptive Flow confirmation.

### Multi-Project Resolution (Phase 0)

<!-- Multi-project resolution — keep in sync across spec, plan, task, execute skills -->

When the workspace includes multiple project directories, resolve logical project names to local filesystem paths. Resolution is ephemeral — never written to committed artifacts.

**Project Map Schema**:
- `projects` array: each entry has `name` (string, `[a-z0-9-]+`, unique, must not contain `::`) and `identity` (string, `hostname/org/repo` format — no protocol prefix, no `.git` suffix; use `local` for non-git directories)
- `artifact_home`: which project hosts `spec-driven/` (defaults to primary working directory's project if omitted)
- When `projects` is absent AND only one workspace directory exists → single-project mode, skip resolution entirely (zero overhead)

**Resolution algorithm**:
1. Check workspace directories from the Environment section in the system prompt:
   ```
   # Environment
    - Primary working directory: /absolute/path/to/project-a
    - Additional working directories:
      - /absolute/path/to/project-b
   ```
2. If multiple workspace directories exist but no `projects` block is present → offer **late-entry discovery**: "This workspace has N directories. Does this feature span multiple projects?" If yes → present directory list, let user select which projects are in scope, assign logical names, write `projects` to the spec as a `## Projects` section with a YAML code fence (see spec template for format). If no → single-project mode.
3. For each project in the map:
   a. Scan each workspace directory: run `git -C "<dir>" remote get-url origin`
   b. Normalize the remote URL: strip protocol (`https://`, `git@`, `ssh://`), strip `.git` suffix, strip trailing slashes, lowercase → yields `host/org/repo`
   c. If no match by origin: try all remotes via `git -C "<dir>" remote -v`
   d. Compare normalized URL with the project's `identity` field (also normalized)
   e. On match → record: `project.name → <dir absolute path>`
   f. No match by remote URL → try basename match: `basename "<dir>" == project.name`
   g. No match by either → prompt user: "Which directory contains '[project-name]'?"
4. Validate: all projects must resolve. If any fail after prompting → exclude project from spec with a gap note
5. Store resolved map in session memory (not on disk, not in committed artifacts)

**Spec-specific behavior**: The spec skill is the primary discovery point — it always offers project discovery when the workspace is multi-directory. On resolution failure, exclude the unresolvable project from the spec and note the gap rather than blocking.

**Per-project CLAUDE.md**: Read `CLAUDE.md` from each resolved project directory (not just the primary). Claude Code does NOT auto-load CLAUDE.md from additional directories. Skills must read them explicitly to capture per-project conventions, patterns, and constraints.

**Developer doesn't have all projects cloned**: Offer: "I don't have this project locally — skip it." Exclude that project from the spec scope.

<!-- End multi-project resolution -->

**Flow:**

**[1/4] Session check** — Emit: `[1/4] Checking for existing sessions...`
Check for existing in-progress sessions (`spec-driven/.sessions/*.spec.json`) — offer resume if found (see elicitation guide).

**[2/4] Context gathering** — Emit: `[2/4] Gathering context from codebase and external sources...`
Gather codebase and external context (see Context Gathering below). If delegating to subagents for deep scanning, emit periodic status every ~60 seconds.

**[3/4] Rally + inline context** — Emit: `[3/4] Importing Rally data and collecting inline context...` *(skip if Rally is not available)*
Parse the user's trigger message for requirements data and offer Rally import if MCP tools are available.

**[4/4] Gap analysis** — Emit: `[4/4] Analyzing gaps and determining elicitation flow...`
Map all extracted information to spec template fields. Present a gap analysis: what's already answered vs. what still needs asking. **This is the first interactive moment** — end the gap analysis with structured input (e.g., "Looks correct — proceed" / "Needs corrections" / "Let me add context") to transition into guided elicitation. Then determine flow (see Adaptive Flow below).

### Context Gathering (Phase 0)

Before beginning interactive phases, gather codebase and external context:

**Inline scanning (default)**: Read project-level signals directly — this completes in seconds and avoids subagent overhead. Do NOT read files in `spec-driven/` — previous specifications may pollute context.

1. Read `CLAUDE.md` (project-level, then global)
2. Read `README.md`
3. Read package manifest (`package.json`, `pom.xml`, `Cargo.toml`, etc.)
4. Top-level directory listing

Map findings to the gap analysis: tech stack → project context, conventions → defaults, existing structure → Current State. Tag all inline-scanned content with `[Codebase]` provenance.

**Deep scanning (large codebases)**: If the project has 10+ top-level source directories (excluding `node_modules`, `dist`, `.git`, `build`, `coverage`, `__pycache__`, `.next`, `.cache`) or the user explicitly requests deep analysis, delegate to a subagent. The subagent reads [references/codebase-scan-instructions.md](references/codebase-scan-instructions.md) as its first action, then scans `<project-dir>` in DEEP MODE. Expected output: Deep Schema JSON.

Reserve subagent delegation for cases that justify the latency cost.

**Multi-project deep scanning**: When `projects` is present and deep scanning is warranted, spawn one subagent per resolved project directory, running in parallel. Each subagent reads [references/codebase-scan-instructions.md](references/codebase-scan-instructions.md) as its first action, then scans its assigned project directory in DEEP MODE. Each scanner focuses on one project's tech stack, patterns, and conventions — avoiding context exhaustion from mixing disparate codebases.

Per-project results aggregate as `{ "project-name": DeepSchemaJSON, ... }`. If a scanner fails, its project falls back to inline scanning; other projects' results are preserved.

**External context enrichment** (if `--from` sources exist): Delegate to a subagent. The subagent reads [references/context-enrichment-instructions.md](references/context-enrichment-instructions.md) as its first action, then extracts context from: [source paths/URLs/Rally IDs]. Expected output: Context Enricher Schema JSON.

If both deep scanning and context enrichment are needed, run them in **parallel** (they are independent).

**Consuming gathered context:**
- Map codebase signals to the gap analysis: techStack → project context, conventions → defaults
- Map context-enricher output to spec template fields using the field extraction map in elicitation-guide.md
- Tag codebase-sourced content with `[Codebase]` provenance; tag enricher-synthesized content with `[Inferred]`

**Subagent failure fallback**: When a subagent fails, fall back to the most direct method for that source type:

| Subagent | Fallback |
|----------|----------|
| Codebase scanner | Inline scanning (CLAUDE.md, README, manifest, directory listing) |
| Context enricher | Read `--from` local files directly in the main context. For URLs that failed to fetch, ask the user to paste content. Rally sources follow Rally error recovery in the Rally reference. |

After context is gathered, proceed with the gap analysis logic.

> See [references/elicitation-guide.md](references/elicitation-guide.md) for detailed Context Analysis guidance including the field extraction map and codebase context rules.
> See [references/rally-integration.md](references/rally-integration.md) for Rally-specific field mappings.

---

## Adaptive Flow

Based on Phase 0 output, adapt the elicitation approach:

- **Rich context** (Phase 0 answered all Phase 1+2 questions from subagent output, `--from` sources, or Rally): Present synthesized overview, goals, users, and scope for explicit user confirmation. Wait for acknowledgment, then proceed through Phases 3-4 and Post-Elicitation Validation. Exception: `--draft` mode (explicit or auto-triggered) skips confirmation — the draft itself is the confirmation artifact.
- **Partial context** (Phase 0 answered some questions): Ask only about gaps. If 3 or fewer questions remain across Phases 1+2, combine them into a single exchange.
- **No context** (bare trigger like `/spec`): Standard phase flow, unchanged.
- **`--draft` with insufficient context**: If `--draft` is explicit but context covers fewer than half of Phase 1 fields, fall back to interactive elicitation and inform the user: "Not enough context for a draft — switching to interactive mode."

**Key rule**: Never ask a question whose answer is already available from Context Analysis (including inline scan results or subagent output).

---

## Phase 1: Core Understanding (Required)

Single exchange to establish the "what" and "why".

**Questions**:

1. What is this feature/capability in one sentence?
2. Who is this for and what problem does it solve?
3. Why does this matter to the business? *(Optional — skip if obvious from Q2)*

**Slug generation**: If a feature name was provided in the trigger, generate the slug immediately and confirm it — see elicitation guide for rules.

**Output**: Spec name/slug, Overview (including Current State), Primary goal

---

## Phase 2: Users and Context (Required)

Define who uses this and the surrounding context.

**Questions**:

1. Who are the primary users? (multi-select: e.g., Consumers, Dealers, Internal employees, API consumers/developers, Other)
2. Existing systems this interacts with? *(Only ask if the feature likely integrates with other systems. Skip for clearly standalone features.)*

**Output**: Users section, Dependencies

---

## Phase 3: Functional Requirements (Required)

Extract core capabilities needed.

**Process**:

1. Synthesize capabilities from Phase 1-2 answers
2. Present categorized list (Must Have / Should Have / Nice to Have)
3. User validates, adds, removes items
4. Clarify ambiguous items (max 2 follow-ups)
5. **Multi-project FR association**: When `projects` is present, associate each FR with the project(s) it affects: "Which project does this requirement affect?" FRs can affect multiple projects. Record the association in the FR description for downstream use by the plan skill.
6. Now that capabilities are established, ask: "What should this explicitly NOT do?" and "Are there any hard constraints?" (see elicitation guide for details)

**AC ID format**: `AC-{FR}.{seq}` (e.g., AC-1.1, AC-1.2) — the hierarchical format preserves the AC-to-FR relationship in the ID itself, enabling downstream tools to parse the parent FR without a lookup.

**Output**: FRs with BDD acceptance criteria (Given/When/Then), Goal assignment per FR, In Scope (derived: summarize the validated FRs into a concise scope statement), Out of Scope / Non-Goals, Constraints, Assumptions

---

## Phase 4: NFRs and Success (Optional)

Capture quality attributes and success metrics.

**Skip if `--minimal` flag provided.**

**Questions**:

1. Performance requirements?
2. Security considerations?
3. Reliability requirements?
4. Cost constraints?
5. Operability requirements?
6. How will you know this is successful?

**Output**: NFRs, Success Metrics

---

## Handling Unknowns

| Pattern         | Detection                              | Response                                                     |
| --------------- | -------------------------------------- | ------------------------------------------------------------ |
| "I don't know"  | "not sure", "TBD", "?"                 | Add as Open Question, use smart default if available         |
| "Figure it out" | "you decide", "whatever works", "agent's choice" | Announce decision with rationale (see elicitation guide for format); document with "Agent Decision" tag |
| Empty/Skip      | Blank or "skip"                        | Use default if available, else add Open Question             |
| Vague answer    | Short (< 5 words) for complex question | One clarifying follow-up, then accept                        |

---

## Post-Elicitation Validation (after Phase 3, Phase 4, or draft acceptance)

Emit to user: `Validating spec quality...`

After writing the spec to `spec-driven/<slug>/spec.md`, run validation following the output reference for the detected backend.

**Presenting validation results:**
- If overallStatus is "pass": Proceed to completion. Mention "Spec passed quality validation."
- If overallStatus is "advisory" or "fail": Present findings to the user as reviewable items, NOT as blocking errors:
  ```
  Quality Review Findings:
  - [ADVISORY] SQ-9: All FRs are marked Must-Have. Consider if any could be Should-Have or Nice-to-Have.
  - [FAIL] SQ-1: FR-3 has only 1 acceptance criterion. Must-Have FRs should have at least 2.
  ```
- Ask the user: "Would you like to address any of these findings, or proceed as-is?"
- User can choose to fix items or skip — validation is advisory, never blocking.

**Open question sweep (all paths)**: After validation (or after spec generation if validation was skipped via `--minimal`), check the spec for remaining Open Questions. If any exist, present them:

  ```
  There are [N] open questions remaining:
  1. [Open question text]
  2. [Open question text]

  Want to resolve these now, or leave them for later?
  ```

If the user answers, update the spec inline and present an edit summary (see the Edit Summaries section in the output reference). If they choose "leave for later," proceed to completion.

**Open question batching**: Batch all open questions into a single prioritized list rather than asking them one at a time. Order with the most impactful questions first — those affecting Must-Have FRs or blocking implementation decisions.

**Fallback**: If the validator subagent fails (timeout or error), skip validation and proceed to completion.

**`--draft` mode**: Run validation after the draft is generated and accepted by the user. The draft replaces interactive phases, but validation still applies to the resulting spec.

**`--minimal` flag**: When `--minimal` is provided, skip this validation step entirely to reduce latency. Codebase scanning and context enrichment still run normally.

---

## Spec Generation

### Persist content incrementally after each phase

After each phase completes, persist all captured content and update the sidecar. Before the first write, read the output reference for the detected backend:

- **Graph**: [references/output-graph.md](references/output-graph.md)
- **Markdown**: [references/output-markdown.md](references/output-markdown.md)

Follow the output reference for all subsequent writes. Both backends produce `spec-driven/<slug>/spec.md` as the human-readable artifact.

Emit to user after each write: `Spec written to spec-driven/<slug>/spec.md`

This preserves content if the session ends unexpectedly. The sidecar tracks which phases are complete; the spec file contains the actual content. Write the spec before updating the sidecar.

### Finalize after all phases complete

Emit to user: `Finalizing spec document...`

After all phases (and optional validation) are complete:

1. If the spec file already exists (regeneration), read the current Version number and increment it (1.0 → 1.1)
2. Run the finalization step from the output reference (with updated version if applicable)
3. Delete the session sidecar file for this slug (terminal action)
4. Present a summary of what was captured, including any agent decisions that need review
5. Offer to commit: "Want me to commit this spec?" (If yes, use message: `docs(spec): add <spec-slug> specification`)
6. Present actionable next steps:
   - "Want to refine any section? Name it (e.g., 'FR-2', 'NFRs', 'scope')"
   - "Ready to move to design? Use `/sds.design` to explore the codebase and make architecture decisions"

