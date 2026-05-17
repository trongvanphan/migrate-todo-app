---
name: sds.verify
description: |
  Verify executed work against its specification. Traces the artifact chain (spec → design → tasks → progress),
  dispatches 6 parallel verification agents, synthesizes findings into a structured report, and offers
  remediation. Use when someone says "verify", "check the work", "validate execution", "run verification",
  or "are we done".
---

# Verification

Verify executed work by tracing the artifact chain, dispatching parallel verification agents, synthesizing findings into a structured report, and optionally remediating issues. Transforms DONE (executed steps) into VERIFIED (evidence-backed quality assessment).

## Trigger

```bash
/sds.verify user-auth
/sds.verify user-auth --report-only
/sds.verify user-auth --focus traceability,security
/sds.verify user-auth --severity high
/sds.verify
```

## Flags

| Flag | Description |
| --- | --- |
| First argument (slug) | Slug identifying the spec. Resolves to artifact chain via detected backend: markdown reads `spec-driven/<slug>/spec.md`, graph queries provenance chains by slug. |
| `--report-only` | Generate report without entering remediation phase. |
| `--focus <dimensions>` | Comma-separated list of dimensions to verify (default: all). Values: `traceability`, `completeness`, `quality`, `testing`, `regression`, `security` |
| `--severity <level>` | Minimum severity to include in report. Values: `critical`, `high`, `medium`, `low`, `info` (default: `info`) |

## Output

- Verification report at: `spec-driven/<slug>/verify-report.md`
- Remediation brief at: `spec-driven/<slug>/remediation.md` (only if remediation findings are selected)
- Two output backends (detected in Phase 0):
  - **Markdown** (default): git log + artifact traceability — [references/output-markdown.md](references/output-markdown.md)
  - **Graph**: provenance chain traversal via `sds context --profile review` — [references/output-graph.md](references/output-graph.md)

---

## Tool Usage

**Structured input**: For all bounded-answer questions (remediation selection, execution mode choices, re-verification prompts, dimension selection, or any question where valid responses can be enumerated), use the platform's interactive question or prompt mechanism — not inline text. Present options as selectable choices. Use conversational text only for genuinely open-ended follow-ups.

Never present bounded options as plain-text numbered or lettered lists — always use the interactive mechanism.

**Progress milestones**: Emit status at key transitions using the format `[Phase N] description`.

**Mandatory interaction gates** (never self-answered — self-answering skips user review of verification results and remediation decisions):
1. **Prerequisite Check** (Phase 0): If no completed steps found, confirm whether to proceed.
2. **Remediation Selection** (Phase 3b): User selects which findings to address.
3. **Execution Mode** (Phase 3e): User chooses fix-now / plan-first / handle-it.
4. **Convention Reinforcement** (Phase 3d): User approves principles before CLAUDE.md modification.

**Wait for user response**: When presenting structured input, wait for the actual response before proceeding. Generating or inferring a response corrupts remediation — the user decides what gets fixed and how.

---

## Phase 0: Context Loading (Always Runs)

**Before starting**: Read this reference file — it contains agent prompt templates, severity model, verdict algorithm, and detailed lookup tables:
- [references/verification-guide.md](references/verification-guide.md) — agent prompts, output schema, severity definitions, verdict computation, deduplication rules, toolchain extraction, remediation mapping, fallback behavior

> **Authority**: SKILL.md defines the verification protocol. verification-guide.md provides reference tables and algorithms. If they conflict, SKILL.md is authoritative.

**Backend detection** (silent, first step): Check if `sds` and `dolt` are available in PATH by running `which sds && which dolt`. If both available, use **graph backend**. Otherwise, use **markdown backend** (default). Remember for session. The output reference file is loaded at Phase 1 dispatch (not during backend detection).

Runs on every invocation before agent dispatch. Gathers and validates the full artifact chain.

**Steps:**

1. **Resolve slug**:
   - If slug provided: proceed to step 2.
   - If no slug provided: scan `spec-driven/` for `*/spec.md` files. If exactly one: confirm selection. If multiple: present picker. If none: stop: "No spec files found. Run `/sds.spec` to create one."

2. **Session check**: Check for existing sidecar at `spec-driven/.sessions/<slug>.verify.json`.
   - If found: offer re-verification options. Structured input: "Fresh verification" / "Re-verify specific dimensions" / "View last report". On "Re-verify specific dimensions": prompt for dimension list, apply as `--focus`. On "View last report": read and present `spec-driven/<slug>/verify-report.md`, skip to Phase 3.
   - If not found: create the sidecar with initial state (`slug`, `backend`, `phasesCompleted: []`). Continue to step 3.

   `[Phase 0] Loading spec and resolving artifact chain...`

3. **Read spec**: Read `spec-driven/<slug>/spec.md`. Validate it is a spec file (has `## Functional Requirements`). If missing or invalid, stop: "Spec not found at `spec-driven/<slug>/spec.md`. Provide a valid slug."

4. **Read design**: Read `spec-driven/<slug>/design.md`. Extract Findings, Decisions, Standards. If missing, note the gap — agents proceed with reduced context.

5. **Resolve artifact chain** — locate execution artifacts:
   - Tasks: read `spec-driven/<slug>/tasks.md` and all `bundle-N.md` files. Extract STEP entries with verify clauses.
   - Progress: read all `spec-driven/<slug>/progress-bundle-N.md` files. Extract step statuses, commit hashes, deferred verifications.
   - If tasks are missing, note: "No task file — only spec-level analysis available."

6. **Extract verification commands** — scan all STEP entries in bundle files for `**Verify**:` lines. Collect as expected toolchain commands. Also collect deferred verifications from progress file Notes columns. See verification-guide.md § Toolchain Extraction for parsing rules.

7. **Prerequisite checks**:
   - If no progress files exist or no steps have status `done`: warn "No completed steps found. Verification requires executed work." Structured input: "Continue anyway (spec-only analysis)" / "Stop — I'll complete execution first".
   - If progress files show steps still `in-progress` or `pending`: note "Execution appears incomplete — N of M steps are done. Verification will assess completed work only."

8. **Multi-project resolution**: When the workspace includes multiple project directories, resolve logical project names to filesystem paths. Inherit `projects` from spec frontmatter. For each project entry, resolve `name` to a workspace directory using these rules in order: (1) match `identity` field against normalized git remote URLs (`git -C "<dir>" remote get-url origin`, strip protocol/`.git`/trailing slashes, lowercase), (2) basename match (`basename "<dir>" == project.name`), (3) if no match, prompt the user. If the user cannot provide a valid path, exclude that project from verification scope.

9. **Read CLAUDE.md** from each resolved project directory (not just the primary). Extract conventions for the Code Quality agent.

10. **Collect changed files** — identify files changed during execution:

    Read the execution branch name from the sidecar or derive from convention: `spec-driven/<slug>/exec`. Read baseline hashes from the progress files or sidecar.

    **Single-project**: `git log --oneline --grep="STEP-" <baseline>..HEAD` on the execution branch. Collect changed files: `git diff --name-only <baseline>..HEAD`. Filter out gitignored paths: run `git ls-files -i --exclude-standard` and remove matches from the changed file list. This excludes files that `.gitignore` rules would prevent from being committed.

    **Multi-project**: Repeat per-project using `git -C "<resolved-dir>"` with per-project baselines. Apply the gitignore filter per-project.

    `[Phase 0] Artifact chain loaded. N changed files identified.`

11. **Build agent context package** — assemble the shared context each agent will receive:
    - Spec content (FRs, ACs, NFRs, constraints, success metrics)
    - Design content (Findings, Decisions, Standards)
    - Task content (STEP entries with verify clauses from bundle files)
    - Progress (step statuses, commit hashes from all progress-bundle-N.md files)
    - Changed file list (per-project in multi-project mode; gitignored paths excluded)
    - CLAUDE.md conventions per project
    - Toolchain commands (for Regression agent)
    - Baseline commit hashes and exit codes (for Regression agent)

    **Graph backend enrichment**: For each done step, include the provenance chain from `sds context STEP-N --profile review --format json --slug "<slug>" --project-root "<project-root>"`. This gives agents the full Decision→Finding→FR/NFR chain.

12. Present context summary: "Loaded artifact chain for `<slug>`. N FRs, M ACs, K steps (J done). Ready to dispatch verification agents."

---

## Handling Unknowns

| Pattern | Detection | Response |
| --- | --- | --- |
| Missing spec | Slug doesn't resolve to a spec file | Stop: "Spec not found. Provide a valid slug." |
| Missing design | No `design.md` found | Note gap. Agents proceed with reduced context. |
| Missing tasks | No `tasks.md` or bundle files found | Note gap. Only spec-level analysis available. |
| Missing progress | No `progress-bundle-N.md` files found | Warn: "No progress files — execution may not have been tracked." Proceed with git-only evidence. |
| Incomplete execution | Progress shows pending/in-progress steps | Note: "Execution incomplete — verifying completed work only." Agents scope to done steps. |
| No test framework | No test runner detected in manifests | Test Quality agent returns MEDIUM finding. Regression agent skips test execution, runs typecheck/lint only. |
| Agent failure | Subagent returns error or times out | Record CRITICAL finding for dimension, set verdict to FAIL. See verification-guide.md § Fallback Behavior. |
| Pre-existing failures | Baseline exit code is non-zero | Note in report. Regression agent compares exit codes only. |
| No changed files | Git diff shows no changes since baseline | Warn: "No file changes detected. Were changes committed?" Proceed with artifact-only analysis. |

---

## Phase 1: Agent Dispatch

**Load output backend reference** (point of action):
- Graph: [references/output-graph.md](references/output-graph.md)
- Markdown: [references/output-markdown.md](references/output-markdown.md)

Dispatch 6 verification subagents in parallel. Each receives the shared artifact context plus dimension-specific focus instructions from verification-guide.md § Agent Prompt Templates.

**Autonomous execution**: Dispatch each subagent with autonomous execution permissions — verification agents run non-interactively and must be able to read files, search code, and run commands (git log, test suites, linters) without per-operation approval.

**When `--focus` is specified**: Only dispatch the named dimensions:
- `traceability` → Traceability (artifact chain integrity)
- `completeness` → AC/NFR Completeness (requirements satisfaction)
- `quality` → Code Quality + Conventions (best practices + CLAUDE.md)
- `testing` → Test Quality (coverage + assertion quality)
- `regression` → Regression (test/typecheck/lint)
- `security` → Security (OWASP + data flow)

**Steps:**

1. **Dispatch all agents simultaneously**. Each agent is a subagent dispatched with the artifact context package and the agent-specific prompt. Launch all in a single message with parallel dispatch.

   **Scope constraint**: Pass the filtered changed file list to every agent. Each agent's analysis scope is the changed file list plus files those changed files directly import. Agents do not scan the working directory at large.

   ```
   [Phase 1] Dispatching verification agents...
     → Traceability (artifact chain integrity)
     → AC/NFR Completeness (requirements satisfaction)
     → Code Quality + Conventions (best practices + CLAUDE.md)
     → Test Quality (coverage + assertion quality)
     → Regression (test/typecheck/lint)
     → Security (OWASP + data flow)
   ```

2. **Collect results**. `[Phase 1] All agents complete. Synthesizing results...` Each agent returns a JSON structure conforming to the common output schema (see verification-guide.md § Common Output Schema). If an agent fails or times out, record a finding: dimension=`<agent>`, severity=`CRITICAL`, description="Agent failed to complete — entire dimension unverified", suggested_fix="Re-run verification with `--focus <dimension>`." Set dimension verdict to `FAIL`. See verification-guide.md § Fallback Behavior for details.

---

## Phase 2: Synthesis

Collect agent results and produce the verification report.

**Steps:**

1. **Parse agent outputs** — extract findings from each agent's JSON response. Each finding has: `id` (dimension-prefixed, e.g., `VF-TR-1`), `severity`, `title`, `description`, `evidence` (file:line references), `affected_acs`, and `suggested_fix`.

2. **Deduplicate cross-agent findings** — see verification-guide.md § Deduplication Rules:
   - Same file + same line range + overlapping description → merge, keep highest severity, combine evidence
   - Same AC referenced by multiple agents for different concerns → keep both (distinct dimensions)

3. **Resolve cross-agent conflicts** — if agents genuinely disagree on implementation status, examine file:line citations and judge. Note: "Agents disagreed — resolved by examining [evidence]."

4. **Cross-validate unique findings** — single-agent findings: verify file:line citations exist. Flag over-interpretations at reduced severity rather than dropping.

5. **Compute per-dimension verdicts**: PASS (no CRITICAL/HIGH), PASS WITH CAVEATS (HIGH present, no CRITICAL), FAIL (any CRITICAL).

6. **Compute overall verdict**: Worst-of across dimensions. See verification-guide.md § Verdict Algorithm.

7. **Apply severity filter** — if `--severity` set, exclude findings below threshold from report display (still count for verdict).

8. **Renumber findings** — flat IDs (`VF-1` through `VF-N`) in severity order. Maintain cross-reference to dimension-prefixed IDs.

9. **Build traceability matrix** — FR → AC → STEP → Commit → Code Evidence → Test Evidence. Mark gaps. Multi-project: per-project commit hashes.

10. **Compare with spec success criteria** — if `## Success Metrics` defined in spec, verify implementation meets them. Note metrics requiring post-launch measurement.

11. **Scan findings for credential patterns** — before writing the report, scan all finding `description`, `snippet`, and `suggested_fix` fields for patterns that resemble credential values. Agent-level redaction is the primary defense; this scan catches credential values that agents failed to redact.
    - Known prefixes: `sk-`, `pk_live_`, `ghp_`, `gho_`, `AKIA`, `xoxb-`, `xoxp-`, `Bearer `, `Basic `
    - Assignment patterns: `password = "..."`, `api_key: "..."`, `token: '...'`, `secret = "..."`
    - If a match is found: replace the value with `[REDACTED]` and append to the finding description: "(Value redacted — verify the original file directly.)"
    - If no match is found: proceed to report write. No modifications needed.

12. **Write verification report** to `spec-driven/<slug>/verify-report.md` using [assets/verify-template.md](assets/verify-template.md). Record source artifact hashes in frontmatter. The report must not contain raw credential values — all references use `[REDACTED]` per the preceding scan.

    If `--report-only`: emit `[Done] Verification complete (<VERDICT> — N HIGH, M MEDIUM). Report: spec-driven/<slug>/verify-report.md` and exit.

13. **Present summary**:

    ```
    [Phase 2] Verification Report: spec-driven/<slug>/verify-report.md

      Overall Verdict: PASS WITH CAVEATS

      Dimension Verdicts:
        Traceability          PASS
        AC/NFR Completeness   PASS WITH CAVEATS
        Code Quality          PASS
        Test Quality          PASS WITH CAVEATS
        Regression            PASS
        Security              PASS

      Findings: 2 HIGH, 4 MEDIUM, 1 LOW
    ```

---

## Phase 3: Remediation (skipped by `--report-only`)

Present findings and offer to fix them. Each sub-phase (3a → 3b → 3c → 3d → 3e) completes before the next begins.

**Triage, selection, and brief (3a–3c)** only run if CRITICAL or HIGH findings exist in the unfiltered set. If all findings are MEDIUM or below: "No critical or high findings. Report written. Review MEDIUM/LOW findings at your convenience." Skip to 3d.

**Convention reinforcement (3d)** runs independently — triggered by theme detection, not gated by CRITICAL/HIGH.

**Execution mode (3e)** runs if findings were selected in 3b.

### Phase 3a: Triage

Present findings grouped by severity (CRITICAL, HIGH, MEDIUM).

`[Phase 3a] Triage summary presented.`

### Phase 3b: Selection

Structured input (multi-select): "Which findings should we address?"
- "All CRITICAL + HIGH" (if any exist)
- Individual HIGH/CRITICAL findings by VF-ID
- "None — accept report as-is"

`[Phase 3b] User selected N findings for remediation.`

### Phase 3c: Remediation Brief

Write `spec-driven/<slug>/remediation.md` with structured fix instructions per selected finding: severity, dimension, evidence, affected ACs, suggested fix, complexity assessment.

`[Phase 3c] Remediation brief written: spec-driven/<slug>/remediation.md`

### Phase 3d: Convention Reinforcement

Detect recurring patterns across findings and offer to codify them as CLAUDE.md principles.

**Skipped** only when: `--report-only` flag set, OR fewer than 2 CRITICAL/HIGH/MEDIUM findings share a common theme.

**Steps:**

`[Phase 3d] Checking for recurring patterns...`

1. **Theme detection** — group findings by theme using verification-guide.md § Principle Extraction heuristics. A theme requires at least 2 CRITICAL/HIGH/MEDIUM findings with a shared pattern.

2. **Principle synthesis** — for each theme, synthesize one principle. Principles must be intent-based, class-level, stable across refactors, and actionable.

3. **Placement** — determine target CLAUDE.md: evidence clustered in one subtree → hierarchical CLAUDE.md; spread across project → root CLAUDE.md; multi-project → scope to appropriate project.

4. **Presentation** — Structured input (multi-select): "These patterns appeared across multiple findings. Which principles should we add to CLAUDE.md?"
   Options: each synthesized principle + "None — skip convention updates"

5. **Application** — for each selected principle: read target CLAUDE.md, find appropriate section, check for semantic duplicates, append.

`[Phase 3d] Convention reinforcement complete. N principles added.` (or `No recurring themes detected.`)

### Phase 3e: Execution Mode

If no findings were selected in 3b, skip to terminal message.

Structured input: "How should we proceed with remediation?"

- **"Fix now"** — apply straightforward fixes directly.
  1. Apply fixes for selected findings.
  2. Structured input: "Re-verify affected dimensions?" — "Yes — re-verify [dimensions]" / "No — done"
  3. If yes, re-invoke verify with `--focus` for affected dimensions only.
  4. One re-verification per invocation. If new findings emerge, present 3e choices again. A second "Fix now" applies fixes without re-verification.

- **"Plan first"** — for complex findings needing design decisions.
  1. Structured input: "Re-verify failed dimensions only or full verification?"
  2. Append re-verification command to remediation brief.
  3. Present: `[Handoff] Entering plan mode with remediation context. After implementation, re-verify with: /sds.verify <slug> --focus <dimensions>`
  4. The generated plan must separate build checks from re-verification into two distinct sections — a `## Build Checks` section and a `## Post-Implementation (Required)` section with the re-verification command. This structural separation prevents the implementing agent from stopping after "all commands passed."

- **"I'll handle it"** — report + remediation brief persist as artifacts.

**Terminal message** (all paths except "Plan first"):

`[Done] Verification complete (<VERDICT> — N HIGH, M MEDIUM). Report: spec-driven/<slug>/verify-report.md`

Delete sidecar: `rm "spec-driven/.sessions/<slug>.verify.json"`

---

## Subagent Delegation

Six subagents dispatched in parallel, all with autonomous execution permissions and prompt-only customization:

| # | Dimension | Concern | Key Activity |
|---|-----------|---------|-------------|
| 1 | Traceability | Artifact chain integrity | Trace spec→design→tasks→progress→commits |
| 2 | AC/NFR Completeness | Requirements satisfaction | Find file:line evidence for each AC/NFR |
| 3 | Code Quality + Conventions | Best practices + CLAUDE.md | Review changed files against standards |
| 4 | Test Quality | Coverage + assertion quality | Map tests↔ACs, assess assertions |
| 5 | Regression | No breakage | Run test/typecheck/lint, diff shared files |
| 6 | Security | OWASP + data flow | Adversarial read of changed code |

See verification-guide.md § Agent Prompt Templates for the full prompts passed to each agent.

---

## Known Limitations

No incremental re-verification (re-runs all agents for single-finding fixes), no CI integration (local only), context window pressure on large codebases (recommend `--focus` for targeted verification).
