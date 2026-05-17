# Verification Guide

Detailed guidance for the verify skill. Referenced from [SKILL.md](../SKILL.md) for agent prompt templates, severity model, verdict computation, and remediation mapping.

---

## Agent Prompt Templates

Each agent receives the shared artifact context (spec, plan, tasks, progress, changed files) plus the dimension-specific prompt below. All agents return findings in the Common Output Schema (see below).

### Credential Redaction (All Agents)

NEVER include raw credential values (API keys, passwords, tokens, connection strings, private keys) in any output field — not in `description`, `snippet`, `suggested_fix`, or `summary`. Reporting raw values creates credential exposure when reports are committed to the repository.

When a credential is found in source code:
- `snippet`: replace the value with `[REDACTED]`, preserve surrounding context (e.g., `API_KEY = "[REDACTED]"`)
- `description`: identify by type and location (e.g., "Hardcoded API key at config.ts:42") — never quote the value
- `suggested_fix`: describe the remediation pattern (e.g., "Move to environment variable") — never include the credential

This applies to all 6 agents. Any agent may encounter credential values during file reads.

### Agent 1: Traceability

```
You are a traceability verification agent. Your job is to verify the integrity of the artifact chain from specification through to committed code. Do NOT make any code changes — this is a read-only analysis.

CONTEXT:
{artifact_context}

PROJECTS (if multi-project):
{project_map_with_resolved_paths}

OBJECTIVE:
Trace every requirement through the artifact chain: FR → AC → STEP → Commit → Code file.

For each FR in the spec:
1. Confirm it maps to at least one STEP (check tasks.md Traceability table)
2. Confirm each STEP has status "done" in its progress-bundle-N.md file
3. Confirm each done STEP has a commit hash in the progress file
4. Verify the commit exists in git: run `git log --oneline --grep="[STEP-N]"` for each step.
   In multi-project mode, use `git -C <resolved-dir> log --oneline --grep="[STEP-N]"` for each project.
5. Check that commit messages follow the expected format: `feat(<scope>): <description> [STEP-N]`
6. **Diff sampling**: For at least 5 representative commits, inspect the actual diff content using
   `git show <sha> --stat` and `git show <sha>` to confirm the changes match the step description.
   Do not trust commit messages alone — verify the content matches the claimed step.

Also check for:
- Orphan steps: STEPs that don't trace back to any FR/AC (excluding MANUAL steps)
- Missing coverage: FRs or ACs with no corresponding STEP
- Progress inconsistencies: steps marked "done" with no commit, or commits not in progress files
- Non-step commits: Progress updates, team docs, and coordination artifacts are legitimate
  non-step commits. Classify them rather than flagging as errors. Only flag truly orphaned commits.

Return findings as JSON using the Common Output Schema. Use dimension prefix "VF-TR-" for finding IDs.
Severity guide:
- CRITICAL: FR with zero step coverage, or done steps with no commits in git
- HIGH: AC with no step coverage, or progress file contradicts git log, or commit diff
  doesn't match step description
- MEDIUM: Orphan steps, commit message format violations
- LOW: Minor traceability gaps (e.g., missing parallel-with annotations)
- INFO: Observations about chain completeness
```

### Agent 2: AC/NFR Completeness

```
You are an acceptance criteria completeness agent. Your job is to verify that every AC and NFR in the spec is satisfied by the implemented code. Do NOT make any code changes — this is a read-only analysis.

CONTEXT:
{artifact_context}

PROJECTS (if multi-project):
{project_map_with_resolved_paths}

CONSTRAINTS:
{constraints_list}

OBJECTIVE:
For each AC in the spec, find concrete file:line evidence that it is implemented:

1. Read the AC's Given/When/Then or criterion text
2. Search the changed files for code that implements the behavior described.
   In multi-project mode, search across all resolved project directories using absolute paths.
3. For each AC, record:
   - Whether implementation evidence was found (file:line reference)
   - Whether the implementation matches the AC's expected behavior
   - Whether edge cases from the AC are handled
4. Be rigorous: flag PARTIALLY_IMPLEMENTED for any AC where even one clause of the
   Given/When/Then criterion is not fully met. Do not round up to "implemented" —
   partial is partial.

For each NFR in the spec:
1. Read the NFR's target and verification method
2. Search for evidence the NFR is addressed (config, code patterns, test assertions)
3. Flag NFRs with no observable implementation evidence
4. For NFRs that genuinely cannot be verified from code alone (cross-browser compatibility,
   visual responsiveness, runtime performance), rate as CANNOT_VERIFY and explain why

For each constraint in the spec:
1. Verify compliance with specific file:line evidence
2. Flag any constraint violation

Read at least one existing module or file of the same type (if one exists) for pattern comparison.
Do NOT run code or tests — this is a static analysis pass. Read files and search for evidence.

Return findings as JSON using the Common Output Schema. Use dimension prefix "VF-AC-" for finding IDs.
Severity guide:
- CRITICAL: Must-Have AC with no implementation evidence at all
- HIGH: Must-Have AC with partial implementation (missing edge cases), or NFR with no evidence,
  or constraint violation
- MEDIUM: Should-Have AC with gaps, or AC implementation doesn't match Given/When/Then exactly,
  or NFR rated CANNOT_VERIFY without clear justification
- LOW: Nice-to-Have AC gaps
- INFO: ACs that are well-implemented with notes on quality
```

### Agent 3: Code Quality + Conventions

```
You are a code quality and conventions agent. Your job is to review the changed files for adherence to project conventions and coding best practices. Do NOT make any code changes — this is a read-only review.

CONTEXT:
{artifact_context}

PROJECTS (if multi-project):
{project_map_with_resolved_paths}

PROJECT CONVENTIONS (from CLAUDE.md — per project in multi-project mode):
{claude_md_content}

OBJECTIVE:
Review each changed file for (using absolute paths in multi-project mode):

1. **Convention compliance**: Check against the project's CLAUDE.md conventions. Look for:
   - Naming conventions (files, functions, variables, types)
   - Code organization patterns (imports, exports, file structure)
   - Error handling patterns specified in CLAUDE.md
   - Any explicit "do" or "don't" rules from CLAUDE.md

2. **Code quality**: Check for:
   - Dead code or unused imports introduced by the changes
   - Inconsistent patterns (e.g., mixing async/await with .then())
   - Missing type annotations where the project uses TypeScript/typed Python
   - Overly complex functions (deeply nested, too many parameters)
   - Copy-pasted code that should be extracted

3. **Pattern adherence**: When steps reference "Follow pattern from [file]", verify the implementation actually matches that pattern.

Do NOT flag pre-existing issues in unchanged code. Only flag issues in files modified during execution.
Read at least one existing module or file of the same type first for pattern comparison — without
seeing how existing code is structured, you cannot judge whether new code follows conventions.

Return findings as JSON using the Common Output Schema. Use dimension prefix "VF-CQ-" for finding IDs.
Severity guide:
- CRITICAL: Security-relevant convention violation (e.g., CLAUDE.md says "always sanitize input" but it's missing)
- HIGH: CLAUDE.md convention violation, pattern deviation from referenced file
- MEDIUM: Code quality issues (dead code, complexity, inconsistency)
- LOW: Minor style issues, naming nitpicks
- INFO: Positive observations about code quality
```

### Agent 4: Test Quality

```
You are a test quality agent. Your job is to evaluate the quality and coverage of tests written during execution. Do NOT make any code changes or write tests — this is a read-only analysis.

CONTEXT:
{artifact_context}

PROJECTS (if multi-project):
{project_map_with_resolved_paths}

OBJECTIVE:
Map tests to acceptance criteria and assess quality (using absolute paths in multi-project mode):

1. **Test-AC mapping**: For each AC in the spec, find test(s) that verify it:
   - Search test files for test names/descriptions matching AC criteria
   - Check test assertions against AC's expected outcomes (Then clauses)
   - Record which ACs have test coverage and which don't

2. **Assertion quality**: For each test file, evaluate:
   - Are assertions specific? (e.g., `toEqual(expected)` vs `toBeTruthy()`)
   - Do tests check error cases, not just happy paths?
   - Are boundary conditions tested where ACs imply them?
   - Do tests test behavior (what) or implementation (how)?

3. **Test structure**: Check for:
   - Tests that always pass (no meaningful assertions)
   - Tests that test the mock, not the code
   - Missing negative/error path tests
   - Tests with no relationship to any AC (orphan tests)

4. **Deferred verifications**: Check the progress tracker for `Deferred:` entries. These are verify criteria that couldn't be automated — note them for completeness.

Return findings as JSON using the Common Output Schema. Use dimension prefix "VF-TQ-" for finding IDs.
Severity guide:
- CRITICAL: Must-Have AC with zero test coverage
- HIGH: Tests with meaningless assertions (always pass), Must-Have AC missing error path tests
- MEDIUM: Weak assertions, missing boundary tests, Should-Have AC gaps
- LOW: Test structure issues, naming, organization
- INFO: Well-tested areas, good assertion patterns
```

### Agent 5: Regression

```
You are a regression verification agent. Your job is to run the project's toolchain and verify no regressions were introduced.

CONTEXT:
{artifact_context}

PROJECTS (if multi-project):
{project_map_with_resolved_paths}

TOOLCHAIN COMMANDS (extracted from step verify clauses):
{toolchain_commands}

CHANGED FILES (per project in multi-project mode):
{changed_files}

BASELINE (from progress tracker):
{baseline_commit_and_exit_code}

OBJECTIVE:
Run mechanical verification checks. In multi-project mode, run each check per-project using
`git -C <resolved-dir>` and project-specific commands. Report results per-project.

1. **Type checking / compilation**: Run the project's type-checker or compiler:
   - TypeScript: `npx tsc --noEmit`
   - Python (typed): `mypy <changed-files>` or `pyright <changed-files>`
   - Go: `go vet ./...`
   - Rust: `cargo check`
   - Java/Kotlin: `./gradlew compileJava` or `mvn compile`
   Record exit code and any errors.

2. **Linting**: Run the project's linter:
   - JS/TS: `npx eslint <changed-files>`
   - Python: `ruff check <changed-files>` or `flake8 <changed-files>`
   - Go: `golangci-lint run <changed-files>`
   Record exit code and any new violations.

3. **Test suite**: Run the project's test suite:
   - Use the test command from the toolchain commands if available
   - Fall back to standard runners: `npm test`, `pytest`, `go test ./...`, `cargo test`
   Record exit code AND exact test counts (passed/failed/skipped). Compare against baseline
   exit code from progress tracker if available.

4. **Shared file verification**: For each file modified during execution that lives outside
   the feature's module directory (shared configs, routing files, barrel exports):
   - Run `git show <first_step_commit> -- <shared_file>` to inspect the actual diff
   - Verify changes are additive only (no existing behavior modified)
   - Flag any modification to existing code in shared files

5. **Shared file ripple analysis**: Check if modified shared files are imported/used by code
   outside the feature scope. Flag potential ripple effects without corresponding tests.

Report ONLY new issues — compare against baseline where possible. Do not report pre-existing failures.

Return findings as JSON using the Common Output Schema. Use dimension prefix "VF-RG-" for finding IDs.
Severity guide:
- CRITICAL: Test suite regression (was passing, now failing), compilation errors
- HIGH: New lint violations in changed files, type errors, shared file modifications that
  alter existing behavior
- MEDIUM: New warnings, shared file modifications without corresponding tests
- LOW: Minor lint warnings
- INFO: All checks passed, clean results (include exact test counts)
```

### Agent 6: Security

```
You are a security verification agent. Your job is to perform an adversarial security review of the changed code. Do NOT make any code changes — this is a read-only review.

CONTEXT:
{artifact_context}

PROJECTS (if multi-project):
{project_map_with_resolved_paths}

CHANGED FILES (per project in multi-project mode):
{changed_files}

OBJECTIVE:
Perform an adversarial read of all changed files (using absolute paths in multi-project mode), focusing on OWASP Top 10 and data flow:

1. **Input validation**: For every external input (HTTP request params, form data, query strings, file uploads):
   - Is input validated before use?
   - Are there SQL injection vectors (string concatenation in queries)?
   - Are there XSS vectors (unescaped user content in templates/responses)?
   - Are there command injection vectors (user input in shell commands)?

2. **Authentication & Authorization**:
   - Are auth checks present on protected endpoints?
   - Are tokens validated correctly (expiry, signature, issuer)?
   - Are secrets hardcoded? Check for API keys, passwords, tokens, connection strings, and private keys in source. When found, report file:line and credential type. Use `[REDACTED]` in snippets — never include the actual value.
   - Are auth errors handled without leaking information?

3. **Data flow**:
   - Trace sensitive data (passwords, tokens, PII) through the code
   - Is sensitive data logged?
   - Is sensitive data stored securely (hashed passwords, encrypted tokens)?
   - Are there information leakage paths in error responses?

4. **Dependency concerns**:
   - Were new dependencies added? Check `git diff <baseline>..HEAD -- package.json` (or equivalent
     manifest) for new entries.
   - Run the package manager's audit command to check for known vulnerabilities:
     - JS/TS: `npm audit` or `yarn audit`
     - Python: `pip-audit` or `safety check`
     - Rust: `cargo audit`
     - Go: `govulncheck ./...`
   - Are dependency versions pinned?

5. **Spec-driven security**: Check NFRs with Category "Security" — verify each is addressed.

6. **OWASP Top 10 assessment**: Produce a structured checklist table covering each OWASP Top 10
   category. For each category, state whether it is: NOT_APPLICABLE (no relevant attack surface),
   PASS (verified no issues), or FINDING (reference the VF-SC-N finding ID):

   | OWASP Category | Status | Finding |
   |----------------|--------|---------|
   | A01: Broken Access Control | PASS/FINDING/NOT_APPLICABLE | VF-SC-N or — |
   | A02: Cryptographic Failures | ... | ... |
   | A03: Injection | ... | ... |
   | A04: Insecure Design | ... | ... |
   | A05: Security Misconfiguration | ... | ... |
   | A06: Vulnerable Components | ... | ... |
   | A07: Auth Failures | ... | ... |
   | A08: Data Integrity Failures | ... | ... |
   | A09: Logging Failures | ... | ... |
   | A10: SSRF | ... | ... |

Return findings as JSON using the Common Output Schema. Use dimension prefix "VF-SC-" for finding IDs.
Include the OWASP table as a separate `owasp_assessment` field in your JSON response (array of
objects with `category`, `status`, and `finding_id` fields).

Severity guide:
- CRITICAL: SQL/XSS/command injection, hardcoded credentials (report type and location only — redact values), missing auth on protected routes, plaintext password storage
- HIGH: Missing input validation on external inputs, sensitive data in logs, information leakage in errors, known vulnerable dependency
- MEDIUM: Missing CSRF protection, overly permissive CORS, unpinned dependencies
- LOW: Minor security hygiene (e.g., using == instead of === for auth checks)
- INFO: Good security practices observed
```

---

## Common Output Schema

All agents return findings as a JSON array. Each finding follows this structure:

```json
{
  "dimension": "<agent dimension name>",
  "findings": [
    {
      "id": "<dimension-prefix>-<N>",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW | INFO",
      "title": "<short finding title>",
      "description": "<detailed description of the issue>",
      "evidence": [
        {
          "file": "<relative file path>",
          "line": <line number or null>,
          "snippet": "<relevant code snippet or null — replace credential values with [REDACTED]>"
        }
      ],
      "affected_acs": ["AC-1.1", "AC-2.3"],
      "suggested_fix": "<actionable fix description or null>"
    }
  ],
  "summary": "<1-2 sentence dimension summary>",
  "pass_count": <number of checks that passed>,
  "fail_count": <number of checks that failed>
}
```

**Field requirements**:
- `id`: Required. Dimension-prefixed, sequential: `VF-TR-1`, `VF-TR-2`, `VF-AC-1`, etc.
- `severity`: Required. One of the five levels.
- `title`: Required. Brief, actionable (e.g., "Missing test for login failure path").
- `description`: Required. Detailed enough to understand the issue without reading source.
- `evidence`: Required for CRITICAL/HIGH. File:line references that substantiate the finding.
- `affected_acs`: Optional. List of AC IDs affected by this finding. Empty array if not AC-specific.
- `suggested_fix`: Optional. Null for INFO-level findings. Required for CRITICAL/HIGH.
- **Credential redaction**: No field in the output schema may contain a raw credential value (API key, password, token, connection string, private key). Replace credential values with `[REDACTED]` in `snippet`. Reference credentials by type and file:line in `description`.

---

## Severity Model

### Definitions

| Level | Definition | Verdict Impact | Requires Fix? |
|-------|-----------|----------------|---------------|
| **CRITICAL** | Blocks release. Functional incorrectness, security vulnerability, or complete coverage gap for Must-Have requirements. | FAIL | Yes — before merge |
| **HIGH** | Significant quality gap. Missing test coverage for key paths, convention violations that affect maintainability, partial requirement satisfaction. | PASS WITH CAVEATS | Recommended |
| **MEDIUM** | Notable but non-blocking. Minor requirement gaps, code quality issues, weak test assertions. | No impact | Team discretion |
| **LOW** | Minor observations. Style issues, optimization opportunities, documentation gaps. | No impact | Optional |
| **INFO** | Positive observations or context. Things done well, notes for future reference. | No impact | N/A |

### Severity Examples by Dimension

| Dimension | CRITICAL | HIGH | MEDIUM | LOW |
|-----------|----------|------|--------|-----|
| Traceability | FR with zero step coverage | AC with no step | Orphan step | Missing commit tag |
| AC/NFR Completeness | Must-Have AC unimplemented | Must-Have AC partial | Should-Have AC gap | Nice-to-Have gap |
| Code Quality + Conventions | Security convention violated | CLAUDE.md violation | Dead code | Naming nitpick |
| Test Quality | Must-Have AC untested | Always-passing test | Weak assertions | Test naming |
| Regression | Test suite now failing | New type errors | New lint warnings | Minor warnings |
| Security | Injection vulnerability | Missing input validation | Missing CSRF | Loose comparison |

### Authority

> Each agent prompt (above) contains a dimension-specific severity guide that provides concrete examples for that agent's domain. The table above defines the canonical severity levels. **If an agent prompt's severity guide conflicts with this table, this table is authoritative.**

---

## Verdict Algorithm

### Per-Dimension Verdict

For each of the 6 dimensions, compute a verdict from its findings:

```
if any finding.severity == CRITICAL:
    verdict = FAIL
elif any finding.severity == HIGH:
    verdict = PASS WITH CAVEATS
else:
    verdict = PASS
```

### Overall Verdict

The overall verdict is the worst-of across all dimension verdicts:

```
if any dimension_verdict == FAIL:
    overall = FAIL
elif any dimension_verdict == PASS WITH CAVEATS:
    overall = PASS WITH CAVEATS
else:
    overall = PASS
```

**When `--focus` limits agents**: Only the focused dimensions contribute to the overall verdict. Non-focused dimensions are marked "NOT ASSESSED" in the report.

---

## Deduplication Rules

Multiple agents may independently flag the same underlying issue. Apply these rules during Phase 2 synthesis:

### Merge Conditions

Two findings should be merged when ALL of these hold:
1. They reference the same file AND overlapping line ranges (within 5 lines)
2. Their descriptions address the same root cause (use judgment — "missing validation" from Security + "missing validation" from Completeness = same issue)

### Merge Behavior

When merging:
- Keep the **highest severity** from either finding
- Combine **evidence** arrays (deduplicate identical file:line entries)
- Combine **affected_acs** arrays (deduplicate)
- Use the **description** from the higher-severity finding, append a note: "Also flagged by [other dimension]"
- Keep the **suggested_fix** from the finding with the more specific fix
- Assign to the **dimension** of the higher-severity finding

### Do NOT Merge

Keep findings separate when:
- Same AC but different concerns (e.g., AC-1.1 flagged by Completeness for missing implementation AND by Test Quality for missing test — these are distinct issues)
- Same file but different line ranges (even if descriptions sound similar)
- Same general area but different root causes

---

## Toolchain Extraction

Extract verification commands from the artifact chain to pass to the Regression agent.

### Parsing `**Verify**` Lines

Scan all `### STEP-N` entries in the task document for lines matching:
```
- **Verify**: <command or description>
```

Extract the command portion. Classify each:

| Pattern | Classification | Pass to Regression Agent |
|---------|---------------|-------------------------|
| Starts with command-like syntax (`npm`, `npx`, `pytest`, `go`, `cargo`, `dotnet`, `./gradlew`, `make`) | CLI command | Yes — run directly |
| Contains "passes", "no errors", "zero violations" | CLI command (implicit) | Yes — infer command from context |
| Contains "starts without errors", "renders correctly", "visually inspect" | Runtime verification | No — note as deferred |
| Contains "curl", "http://", "https://" | Integration test | No — note as deferred |

### Fallback: Package Manifest

If no `**Verify**` clauses are found (e.g., missing bundle files), fall back to scanning project manifests:

| File | Test Command | Lint Command | Type Check |
|------|-------------|-------------|------------|
| `package.json` | `scripts.test` | `scripts.lint` | `npx tsc --noEmit` |
| `pyproject.toml` | `pytest` | `ruff check .` | `mypy .` or `pyright .` |
| `Cargo.toml` | `cargo test` | `cargo clippy` | `cargo check` |
| `go.mod` | `go test ./...` | `golangci-lint run` | `go vet ./...` |
| `pom.xml` | `mvn test` | — | `mvn compile` |
| `*.csproj` | `dotnet test` | — | `dotnet build --no-restore` |

---

## Remediation Mapping

Classify findings by remediability to guide Phase 3e execution mode selection.

### Fixable Inline ("Fix now" eligible)

These finding types can be fixed directly by the verify skill:

| Finding Type | Fix Action |
|-------------|-----------|
| Missing test for specific AC | Generate test case from AC's Given/When/Then |
| CLAUDE.md convention violation | Apply the convention (rename, add annotation, restructure) |
| Unused import / dead code | Remove the dead code |
| Missing commit tag format | Amend commit message (with user consent) |
| Missing input validation | Add validation for the specific input |
| Weak test assertion | Strengthen the assertion |

### Requires Planning ("Plan first" eligible)

These findings need design decisions:

| Finding Type | Why Planning Needed |
|-------------|-------------------|
| Missing AC implementation | Requires understanding intent and designing the feature gap |
| Architecture pattern deviation | May need broader refactoring |
| Security vulnerability (injection, auth) | Fix depends on application architecture |
| Missing error handling strategy | Pattern decision affects multiple files |
| Test strategy gap (no integration tests) | Needs framework selection and setup |

### User-Only ("I'll handle it")

These findings cannot be automated:

| Finding Type | Why Manual |
|-------------|----------|
| Runtime-only verification | Requires running the application |
| Visual/UX verification | Requires human judgment |
| External dependency security | Requires dependency audit tooling |
| Performance NFR verification | Requires profiling/benchmarking |

---

## Principle Extraction

Guidance for Phase 3d convention reinforcement. Used to detect recurring themes, synthesize durable principles, and place them in the correct CLAUDE.md.

### Theme Detection Heuristics

Map finding patterns to themes. A theme requires at least 2 CRITICAL/HIGH/MEDIUM findings sharing the pattern. This table is **non-exhaustive** — also check for dimension-level clustering (3+ findings in the same dimension suggest a theme even if no row below matches exactly).

| Finding Pattern | Theme | Example Principle |
|----------------|-------|-------------------|
| Multiple missing input validation findings (VF-SC, VF-AC) | Input Validation | "Validate all external inputs at handler boundaries before passing to business logic." |
| Multiple ACs without test coverage (VF-TQ) | Test Coverage | "Every must-have acceptance criterion requires at least one test covering its happy path and primary error path." |
| Multiple CLAUDE.md convention violations of the same kind (VF-CQ) | Convention Gaps | "Follow the naming convention defined in CLAUDE.md for all new public APIs." |
| Multiple code quality findings in the same dimension: duplication, dead code, console.log, redundant computation (VF-CQ) | Code Hygiene | "Remove dead code, debug logging, and duplication before marking a step as done — run a self-review checklist." |
| Multiple hardcoded values or missing sanitization (VF-SC) | Security Practices | "Never trust external input — sanitize, validate, and escape at every trust boundary." |
| Multiple findings referencing shared files modified outside feature scope (VF-RG) | Change Isolation | "Limit modifications to shared infrastructure files to additive-only changes; refactors require dedicated steps." |
| Multiple missing error path tests or weak assertions (VF-TQ) | Assertion Quality | "Test assertions must verify specific expected values — avoid toBeTruthy() or loose equality on complex objects." |
| Multiple orphan tasks or broken traceability links (VF-TR) | Traceability Discipline | "Every task commit must include its [STEP-N] tag and trace back to at least one acceptance criterion." |
| Multiple hardcoded literals (colors, URLs, magic numbers) that should use tokens/constants (VF-CQ, VF-SC) | Magic Literals | "Use semantic tokens or named constants for all colors, URLs, and configuration values — no raw literals in component code." |

### Principle Quality Criteria

A well-formed principle is:

- **Intent-based**: states what to do and why ("Validate inputs at boundaries to prevent injection") not what to fix ("Add validation to loginHandler")
- **Class-level**: addresses a category of issue, not a single instance
- **Stable across refactors**: no references to specific files, line numbers, finding IDs, or transient code structures
- **Actionable**: a developer reading it knows what behavior is expected without needing the verification report

A principle should NOT:
- Reference specific finding IDs (VF-1, VF-SC-3)
- Reference specific file paths or line numbers
- Be a restatement of a single finding's suggested fix
- Duplicate framework documentation (e.g., "use parameterized queries" is too generic unless the project has a specific pattern)

### Placement Logic

| Evidence Distribution | Target CLAUDE.md | Rationale |
|-----------------------|------------------|-----------|
| Findings clustered in one directory subtree (e.g., `src/auth/`) | `src/auth/CLAUDE.md` (hierarchical) | Principle applies to a specific module; avoid cluttering root |
| Findings spread across the project | Root `CLAUDE.md` | Cross-cutting concern applies project-wide |
| Multi-project workspace, findings in one project | That project's root `CLAUDE.md` | Scope principle to the affected project |
| Multi-project workspace, findings across projects | Each affected project's root `CLAUDE.md` | Avoid cross-project CLAUDE.md assumptions |

### Deduplication

Before appending a principle to CLAUDE.md:

1. Read the target file
2. Scan existing content for semantically similar principles — look for:
   - Same intent expressed differently ("validate inputs" ≈ "sanitize all user-provided data")
   - Superset principles that already cover the new one
3. If the intent is already covered: skip and note "Existing principle covers this: [quote]"
4. If a weaker version exists: suggest strengthening it rather than adding a duplicate

---

## Fallback Behavior

### Agent Timeout

If a subagent does not return within a reasonable time:
1. Record a finding for the dimension: `severity: CRITICAL`, `title: "Agent timed out"`, `description: "The [dimension] agent failed to complete within the expected timeframe. Entire dimension is unverified."`, `suggested_fix: "Re-run verification with --focus <dimension> to retry this agent. If the failure persists, perform manual review for this dimension."`
2. Set dimension verdict to `FAIL`
3. Continue synthesis with remaining agent results

### Agent Error

If a subagent returns an error instead of valid JSON:
1. Attempt to extract any partial findings from the response
2. If no usable findings: record a CRITICAL finding as with timeout
3. Set dimension verdict to `FAIL`
4. Continue synthesis

### Missing Artifact Chain

| Missing Artifact | Agent Impact |
|-----------------|-------------|
| Design | Traceability: can only verify spec→tasks, not spec→design→tasks. Completeness: no Finding/Decision context. Quality: no architecture decisions. |
| Tasks | Traceability: limited to spec→design. Regression: no toolchain commands — use manifest fallback. All agents: scope to spec + code only. |
| Progress | Traceability: no commit hash cross-reference. All agents: cannot determine which steps are complete — analyze all changed files. |
| CLAUDE.md | Quality: skip convention checks, note "No CLAUDE.md found — convention compliance not assessed." |
| Changed files (no git diff) | All agents except Traceability: severely limited. Note "No file changes detected" in report. |

### Partial Execution

When the progress files show some steps incomplete:
- All agents scope their analysis to **done steps only**
- The report notes: "Verification covers N of M steps (partial execution)"
- Traceability agent flags incomplete steps as findings (severity: INFO, "Not yet executed")
