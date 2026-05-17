# Execution Guide

Detailed guidance for the execute skill. Referenced from [SKILL.md](../SKILL.md) for branch isolation, merge-back protocol, verification, error handling, retry logic, and mode-specific orchestration.

---

## Dispatch Profile Resolution

SKILL.md dispatch sites specify a profile name (e.g., `implementation`). Resolve each profile to a concrete `model` parameter on the subagent dispatch:

| Profile | Model Parameter |
|---------|----------------|
| `implementation` | `sonnet` |
| `exploration` | `haiku` |
| `orchestration` | No override — inherit session model |

Set the `model` parameter on every subagent dispatch to the value from this table. If the platform does not support per-subagent model selection, omit the parameter — the subagent inherits the session model.

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

## Branch Lifecycle

All execution commits land on an isolated branch, never on the user's working branch.

### Branch Creation

Create the execution branch from the user's current HEAD during Phase 0:

Run: `python3 "<skill-directory>/scripts/exec_branch.py" create --repo "$REPO_ROOT" --branch "spec-driven/<slug>/exec"`

If the branch already exists (resume scenario), validate and check it out:

Run: `python3 "<skill-directory>/scripts/exec_branch.py" validate --repo "$REPO_ROOT" --branch "spec-driven/<slug>/exec"`

### Branch Naming

- **Execution branch**: `spec-driven/<slug>/exec` — all step commits land here
- **Team mode branches**: `feature/<slug>/bundle-N` — one per parallel bundle, created by human developers

### Cleanup

After all bundles merge back to the user's branch, the execution branch is no longer needed. Offer cleanup:

"Execution branch `spec-driven/<slug>/exec` merged. Delete it?" Options: "Yes — delete" / "No — keep"

If yes: run `python3 "<skill-directory>/scripts/exec_branch.py" delete --repo "$REPO_ROOT" --branch "$EXEC_BRANCH"`

---

## Verification Chain

Five-layer architecture. Layers 1+2 run per-step (inside the subagent). Layer 4 runs per-bundle in the worktree after subagent execution completes, before merge to exec (Phase 1 step 6). Layers 3 and 3b run per-bundle on exec after merge. Layer 3b (bundle verification) is advisory — failure is presented at GATE 2 but does not block.

### Layer 1: Static Analysis (Per-Step)

Fast gate. Runs immediately after file changes, before Layer 2. Layer 1 commands (lint and type-check per manifest type) are defined in the step-executor-instructions reference — the subagent runs Layer 1 per-step; the orchestrator does not run Layer 1 directly.

**File scoping**: Scope to files modified by the current step. Derive from `git diff --name-only HEAD` after implementation, not declared paths.

**Lint ordering**: Run the linter before the type-checker (fail-fast).

If Layer 1 fails, classify the error (see § Error Classification) and enter the retry protocol. Do not proceed to Layer 2.

### Layer 2: Step-Specific Verification (Per-Step)

Runs only after Layer 1 passes. Executes the step's `**Verify**` clause (condition/action/expected outcome). This is the behavioral check.

When a verify clause cannot be satisfied via CLI (runtime-only, requires browser, requires deployed environment), log in the progress file Notes column: `Deferred: [criterion] — requires runtime verification`. Mark the step `done` (static checks passed). Never silently skip.

### Layer 3: Regression Gate (Per-Bundle)

Runs once per bundle in Phase 2 after merge to exec, before GATE 2 (the merge decision). Not per-step.

| Scenario | Command | Pass Criteria |
|---|---|---|
| Standard project | Project test runner (e.g., `npm test`, `pytest`, `cargo test`) | Exit code 0 |
| Pre-existing failures | Same test runner | Exit code matches baseline from Phase 0 |
| No test suite | Skip Layer 3 | Note: "No test suite detected — regression gate skipped" |

**Pre-existing failures**: Compare exit codes only. A worse exit code means a regression. Use `git log --oneline <baseline>..HEAD` to correlate regressions with step commits.

### Layer 3b: Bundle Verification (Per-Bundle)

Runs once after Layer 3, before GATE 2. Verifies the bundle's combined output achieves its slice goal.

Read the `**Bundle Verify**:` block from the bundle file header.

**If present**, execute on the merged execution branch:

1. Evaluate the **Given** condition.
2. Perform the **Action**.
3. Check the **Outcome**.

Pass criteria: the outcome matches. Include the result (pass or fail with details) in the GATE 2 presentation. Failure is advisory — the user decides whether to proceed, retry, or investigate.

**If absent**, include this note in the GATE 2 presentation: "⚠ No bundle verify clause found — regression gate only. The task output may predate bundle verify clause generation." Do not silently skip — the absence must be visible at GATE 2.

### Layer 4: Inline Quality Check (Per-Bundle)

Runs once per bundle in the worktree after subagent execution completes, before merge to exec (Phase 1 step 6). For team mode bundles (no worktree), runs post-merge on exec (Phase 2 step 4). Independently assesses whether code implements intents and tests cover verify clauses. Agent instruction templates are in the review-agents reference file.

**Diff range**: `git -C "<worktree-dir>" diff "$EXEC_BRANCH"..HEAD` (agent mode) or `git diff <PRE_BUNDLE_HEAD>..HEAD` (team mode). Captures all step commits in the bundle.

**Assessment files**: Written inside the worktree (`<worktree-dir>/spec-driven/<slug>/review-{cqr,tqr}-bundle-N.json`) for agent mode, or on exec for team mode. These are working artifacts consumed during Layer 4 — they do not persist after merge.

Skip conditions are defined in SKILL.md § Phase 1 step 6. If any match, skip and note the reason at GATE 2. If no skip condition is met, dispatch the Code Quality Reviewer and Test Quality Reviewer as two **separate** subagents in parallel — do not combine them into a single agent. Each agent writes its full assessment to a file and returns only `PASS` or `FLAG: <file path>`. The Code Quality Reviewer reads the bundle file and git diff — it does NOT read test files. The Test Quality Reviewer reads the bundle file and test files — it does NOT read implementation code. Combining them defeats this separation and allows circular validation (the AgentCoder anti-pattern).

**NEVER read the assessment files.** The orchestrator routes based on the verdict line only. It cannot evaluate, summarize, or editorialize findings — this prevents the orchestrator from self-answering resolution decisions that belong to the Judge or the user.

**Resolution**: Both PASS → no findings, record result for GATE 2. Any FLAG → dispatch Judge with both assessment file paths. The orchestrator does not read the files. Judge classifies findings and decides Proceed (advisory at GATE 2) or Remediate (dispatch remediation executor, then re-review). The resolution loop is bounded at 5 remediation cycles; after that the Judge decides "present_advisory" and all remaining findings are surfaced at GATE 2 for user review.

**Failure handling**: If any agent fails (timeout, error), skip the review for this bundle and note at GATE 2. Do not block the merge decision.

---

## Error Classification Heuristics

Classify the error before deciding on recovery.

```
STEP FAILS
│
├── Ambiguous requirement?
│   YES → ESCALATE immediately (no retry)
│         Mark step `blocked`, note: "Requires clarification: [details]"
│
├── Build / type / syntax error?
│   YES → RETRY WITH FIX (max 3 attempts)
│         Read error output → diagnose → targeted fix → re-verify
│
├── Test failure?
│   YES → RETRY WITH FIX (max 3 attempts)
│         Read failing test → diagnose → fix implementation → re-run
│
├── Transient error (network, timeout, flaky)?
│   YES → BLIND RETRY with 10s backoff (max 3 attempts)
│
└── After 3 failures on ANY type:
    → ROLLBACK (see § Rollback Procedure)
    → Mark step `blocked` with error reason
    → Cascade: mark steps with transitive dependency as `blocked`
      with "Blocked by STEP-N"
    → Steps with no dependency path remain `pending` and continue
    → ESCALATE with escalation message
```

**Classification hints**:

| Error Signal | Classification |
|---|---|
| "Cannot find module", "Type error", "Unexpected token" | Build/type/syntax |
| "Expected X but received Y", "assertion failed" | Test failure |
| "ECONNREFUSED", "timeout", "EAGAIN" | Transient |
| Spec contradiction, unclear requirement | Ambiguous |

---

## Retry Protocol

Three-attempt limit per step. Each attempt starts from a clean baseline.

- **Attempt 1**: Implement from `PRE_STEP_HEAD`. Run verification.
- **Attempt 2**: Reset: `git reset --hard "$PRE_STEP_HEAD"` + `git clean -fd -- "<step-file-paths>"`. Diagnose from attempt 1's error (captured before reset). Apply targeted fix. Re-verify.
- **Attempt 3**: Reset again. Try a different approach — alternative pattern, different API, simplified logic. Re-verify.

Capture error output and diagnostic context before each reset. The diagnosis from the previous attempt informs the next.

**Progress visibility**:

```
[2/4] STEP-4: Add JWT validation middleware
      Verified: static analysis FAILED (attempt 1/3)
      Diagnosing: TypeError — session.verify is not a function
      Resetting to PRE_STEP_HEAD...
      Retrying with session.get() pattern...
      Verified: static analysis passed (attempt 2/3)
[done] STEP-4: Add JWT validation middleware  (def5678)
```

---

## Rollback Procedure

Executed after exhausting retry attempts. Preserves the progress file across `git reset --hard`.

**Prerequisites** (captured in step 2 of the execution loop):
- `PRE_STEP_HEAD` — git hash before the step began
- Step file paths — declared `create`/`modify`/`delete` paths

**Steps (single-project)**:

**Prerequisite**: `artifact_home` is the absolute path of the project directory hosting `spec-driven/`, read from the sidecar `artifactHome` field (written at Phase 0 step 7). For single-project workspaces, this equals `$REPO_ROOT`.

1. Save progress file: `cp "<artifact_home>/spec-driven/<slug>/progress-bundle-N.md" "/tmp/progress-backup-<slug>-bundle-N.md"`
2. If backup fails (permissions, disk full), abort the rollback — the progress file is more valuable than a clean tree.
3. Reset: `git reset --hard "$PRE_STEP_HEAD"`
4. Clean untracked files: `git clean -fd -- "<step-file-paths>"` (quote each path; for multiple paths: `git clean -fd -- "path1" "path2"`)
5. Restore progress: `cp "/tmp/progress-backup-<slug>-bundle-N.md" "<artifact_home>/spec-driven/<slug>/progress-bundle-N.md"`
6. Update progress: mark step `blocked` with error reason. Cascade-block transitive dependents.

**Steps (multi-project)**: Per-project rollback:

1. Save progress file (same as single-project)
2. For each affected project:
   ```bash
   git -C "<resolved-dir>" reset --hard "${PRE_STEP_HEAD[project]}"
   git -C "<resolved-dir>" clean -fd -- "<path1>" "<path2>"  # (quote each path to handle spaces/special chars)
   ```
3. Restore and update progress

**Rules**:
1. Never rollback committed steps — only the current in-progress step.
2. Rollback is scoped to the execution branch. The user's original branch is unaffected.
3. Partial bundle completion: completed steps are preserved. Blocked steps remain for retry via `--step STEP-N`.

---

## Merge-Back Protocol

After each bundle's subagent completes, merge the execution branch changes back to the user's branch.

### Pre-Merge Steps

1. Pre-merge check: `python3 "<skill-directory>/scripts/conflict_check.py" --repo "$REPO_ROOT" --ours "$USER_BRANCH" --theirs "$EXEC_BRANCH"`

### Merge Options, Conflict Handling, and Merge Strategy Repeat

Merge commands, conflict handling, and merge strategy repeat flow are defined in SKILL.md GATE 2. Conflict presentation format:

```
Merge conflict for Bundle N:
  Conflicting: src/routes/index.ts, src/config/auth.ts
Options: 1) Resolve manually  2) Fall back to sequential re-execution for this bundle
```

### Post-Merge

After merge: the `merge.py merge` script returns to the exec branch automatically. After the final bundle merges, stay on the user's branch.

---

## Resume Protocol

Resume detection runs during Phase 0. Identifies where a previous session left off.

### Session Sidecar

Check for `spec-driven/.sessions/<slug>.execute.json`. If found and `currentBundle` is null and no progress files show any `done` or `in-progress` steps, treat as a fresh start — delete the stale sidecar and proceed from Phase 0 step 1. Otherwise, read:
- `backend` — detected backend (avoid re-detection)
- `userBranch` — the branch to merge back to
- `execBranch` — the execution branch name
- `artifactHome` — absolute path of the project directory hosting `spec-driven/`. For single-project: `$REPO_ROOT`. For multi-project: the resolved path of the project declared as `artifact_home` in tasks.md frontmatter. Required by the rollback procedure.
- `currentBundle` — the bundle in progress when interrupted
- `baselines` — per-project baseline hashes and exit codes. Single-project schema: `{ "default": { "hash": "<hash>", "exitCode": N } }`. Multi-project schema: `{ "<project-name>": { "hash": "<hash>", "exitCode": N } }` — key is the project `name` from the `projects` map.
- `mergeStrategyRepeat` — `"revoked"` if the user revoked auto-repeat during this session; absent or null otherwise. When present, do not re-offer merge strategy repeat for the remainder of the session.
- `teamGroup` — team mode execution group state (`null` if not team mode; one of `"seq-G"`, `"waiting-G"`, `"merging-G-N"` where G is the execution group index and N is the bundle number)

### Progress Cross-Reference

For each bundle, read `progress-bundle-N.md` and cross-reference with `git log --oneline --grep="STEP-"` on the execution branch:

- **`in-progress` with no matching commit**: Reset to `pending`. Note: "Previous session interrupted — will re-execute."
- **`in-progress` with a matching `[STEP-N]` commit**: Treat as `done` — record hash. Do not re-execute.
- **`done` with no matching commit**: Anomaly. Reset to `pending` with note: "Progress shows done but no commit found — will re-execute."

### Visual Progress Map

Present on every resume:

```
Resuming: spec-driven/<slug>

Progress: 5/8 steps complete
  [done] Bundle 1: Foundation          2/2
  [done] Bundle 2: Core Implementation 3/3
  [>>]   Bundle 3: Integration         0/2  <- you are here
  [ ]    Bundle 4: Verification        0/1

Last: STEP-5 — Create token model (ghi9012)
Next: STEP-6 — Wire auth routes
Blockers: none
```

For blocked bundles: `[!] Bundle 2: Core  2/3  <- STEP-4 blocked: "Type error in auth.ts"`

---

## Worktree Execution

The orchestrator manages worktrees via `scripts/worktree.py` — no platform-specific isolation features. Subagents never commit directly to the exec branch. The exec branch is a pure merge target.

**The orchestrator MUST keep the exec branch checked out in the main working tree while any subagent is executing in a worktree.** Git prevents the same branch from being checked out in multiple worktrees simultaneously — if the orchestrator holds exec, any subagent attempt to `git checkout exec` inside a worktree fails with `fatal: already checked out at`. The orchestrator may briefly switch to the user branch during GATE 2 merges (after the subagent has completed), but must return to exec before dispatching the next subagent or before worktree cleanup.

### Worktree Creation

All worktree commands use absolute paths — never relative. CWD is unreliable; relative paths create worktrees in the wrong location. Capture the repo root once before any worktree operation:

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
```

**Sequential (parallelism = 1)**: Create one persistent worktree before dispatching the first bundle:

Run: `python3 "<skill-directory>/scripts/worktree.py" create --repo "$REPO_ROOT" --name "sequential" --ref "$EXEC_BRANCH" --install-cmd "<lock-file-install-command>"`

The script creates the worktree, verifies it, and runs the install command (e.g., `npm ci`, not `npm install`) — worktrees need reproducible dependencies without modifying lock files. If status `"created_install_failed"`: report the install error. Structured input: "Retry install" / "Abort execution". On "Retry install": re-run `worktree.py create` (up to 2 additional attempts, 3 total). After 3 failures: stop — "Worktree install failed after 3 attempts. Fix the dependency install command and re-run." On "Abort": run `python3 "<skill-directory>/scripts/worktree.py" remove --repo "$REPO_ROOT" --name "sequential"` to clean up the partial worktree, then `git checkout "$USER_BRANCH"`, delete the sidecar, and exit. If status `"error"`: report and exit. Do not fall back to dispatching on the exec branch — subagents never commit directly to exec. The user must fix the git state (e.g., `git worktree prune`, remove stale `.worktrees/` directory) and re-run. If status `"exists"`: reuse the existing worktree. Reuse this worktree for all sequential bundles.

**Parallel (parallelism > 1)**: Pin a fork point at the start of each parallel execution group: `PARALLEL_FORK_POINT=$(git rev-parse HEAD)`. Then create all worktrees for that execution group before dispatching any subagent:

For each parallel bundle N:
Run: `python3 "<skill-directory>/scripts/worktree.py" create --repo "$REPO_ROOT" --name "bundle-N" --ref "$PARALLEL_FORK_POINT" --install-cmd "<install-command>"`

Resolve `<install-command>` from the Toolchain Detection table (§ Toolchain Detection).

All worktrees MUST be created (status `"created"` or `"exists"`), verified, and installed before any subagent is dispatched — parallel bundles branch from the same `PARALLEL_FORK_POINT`, and a missing worktree would cause that bundle's subagent to start from a diverged base, producing misaligned commits at merge time.

If any create call returns `"error"`: fall back to sequential execution for the entire parallel group. Warn: "Worktree creation failed for bundle N — falling back to sequential execution."

Emit: `[Worktree] Creating N worktrees from <fork-point>...`

### Resume and Existing Worktrees

On resume (Phase 0 step 2), detect existing worktrees: run `python3 "<skill-directory>/scripts/worktree.py" list --repo "$REPO_ROOT"`. If `worktrees` is non-empty, present: "Existing worktrees found." Structured input: "Reuse existing worktrees" / "Clean up and recreate". On "Clean up": run cleanup (see § Worktree Cleanup) before proceeding.

### Execution Flow

For each execution group in order:

1. **Sequential execution group**: dispatch bundles one at a time to the persistent sequential worktree. Sequential bundles run sequentially regardless of the parallelism setting.
2. **Parallel execution group (parallelism > 1)**: pin `PARALLEL_FORK_POINT=$(git rev-parse HEAD)`, create per-bundle worktrees from that fork point (§ Worktree Creation), dispatch one subagent per bundle. Do not use platform isolation — pass the worktree directory as input. Pass:
   - Worktree directory: absolute path (e.g., `<repo-root>/.worktrees/bundle-N`)
   - Bundle file path (absolute, under repo root — subagent reads via `git -C`)
   - Progress file path (absolute)
   - The step-executor-instructions reference as the instruction set
   - Pre-detected toolchain, resolved project map, tech-stack lens

   After all subagents complete, process results to the execution branch one bundle at a time, in bundle order. For each parallel bundle, follow these steps IN ORDER — do not advance to the next step until the current step completes:
   a. **Run Layer 4 (Phase 1 step 6) in this bundle's worktree** — Layer 4 MUST complete in the worktree before the worktree branch is merged to exec. Layer 4 across bundles can run concurrently (the worktrees are independent), but Layer 4 for THIS bundle must finish before step c below.
   b. Record `PRE_BUNDLE_HEAD=$(git -C "$REPO_ROOT" rev-parse HEAD)` — the exec branch HEAD immediately before this bundle's merge.
   c. Merge the worktree branch to exec: `git -C "$REPO_ROOT" merge "exec-bundle-N" --no-ff -m "merge: Bundle N — [name] (parallel)"`. If conflicts, present conflicting files with options: "Resolve manually" / "Re-execute bundle sequentially" / "Skip bundle".
   d. If the user skips a bundle: mark all steps in the skipped bundle as `blocked` with note "Skipped due to merge conflict." Skip Phase 2 for this bundle — do not run regression gate, inline quality check, or present GATE 2. Include the skipped bundle in the Phase 3 summary under Blocked steps: "Bundle N skipped due to merge conflict. To retry: `/sds.execute <slug> --bundle N`."
   e. Run Phase 2 steps 1-8 for this bundle: read subagent results, regression gate (Layer 3), bundle verification (Layer 3b), Layer 4 recorded result, bundle summary, pre-merge conflict check, and GATE 2 merge-back decision. GATE 2 fires for each parallel bundle after its verification chain completes. Use the `PRE_BUNDLE_HEAD` from step b.

   Clean up this group's parallel worktrees after the execution group completes (§ Worktree Cleanup — inter-group). The sequential worktree is preserved for reuse.
3. **Parallel execution group (parallelism = 1)**: dispatch each bundle to the persistent sequential worktree, one at a time. Merge-back and Phase 2 follow the sequential pattern.

**Sequential merge-back**: For each sequential bundle, follow this ordering:

1. Subagent completes
2. Run Layer 4 (Phase 1 step 6) in the worktree — MUST complete before merge
3. Verify exec is checked out in the main working tree: `git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD` must equal `$EXEC_BRANCH`
4. Merge the worktree branch to exec: `git -C "$REPO_ROOT" merge "exec-seq" --no-ff -m "merge: Bundle N — [name]"`
5. Run Phase 2 (regression gate, bundle verify, Layer 4 recorded result, bundle summary, pre-merge conflict check, GATE 2)
6. After GATE 2 completes, reset the worktree branch for the next bundle: `python3 "<skill-directory>/scripts/worktree.py" reset --repo "$REPO_ROOT" --name "sequential" --ref "$EXEC_BRANCH"`

Do not reset the worktree or start the next bundle until Phase 2 and GATE 2 complete for the current bundle.

### Parallel Bundle Invariant

Parallel bundles have no cross-dependencies (enforced during task decomposition). If a step in Bundle N depends on a step in Bundle M, they cannot be in the same parallel group.

### Parallel Progress Display

Monitor subagent progress by reading per-bundle progress files periodically:

```
Parallel execution in progress (Bundle 2, 3, 4)...
  Bundle 2: STEP-3 done, STEP-4 in-progress (2/4)
  Bundle 3: STEP-6 done (1/3)
  Bundle 4: STEP-8 pending (0/2)
```

### Subagent Failure Handling

**Timeout**: If a subagent's progress file shows no update for 10 consecutive polling intervals (5 minutes at default 30-second interval), treat the subagent as unresponsive.

**Detection**: A subagent has failed when:
- No progress file update within the timeout window, OR
- The subagent dispatch returns an error, OR
- The subagent's JSON output is absent or malformed

**Recovery**:
1. Mark all steps in the affected bundle as `blocked` with note: "Subagent unresponsive — no result received"
2. The worktree is left as-is (may contain partial work the user can inspect)
3. Present: "Bundle N subagent failed." Options: "Retry in worktree" / "Re-dispatch in sequential worktree" / "Skip bundle and continue"
4. On "Re-dispatch in sequential worktree": create the persistent sequential worktree if it does not already exist (`python3 "<skill-directory>/scripts/worktree.py" create --repo "$REPO_ROOT" --name "sequential" --ref "$EXEC_BRANCH"`). Reset it to the current exec state (`python3 "<skill-directory>/scripts/worktree.py" reset --repo "$REPO_ROOT" --name "sequential" --ref "$EXEC_BRANCH"`). Dispatch the bundle to the sequential worktree. Subagents never commit directly to exec — the exec branch is a pure merge target.

### Worktree Cleanup

**Inter-group cleanup**: After a parallel execution group completes (all bundles merged via Phase 2), remove only that group's parallel worktrees — not the sequential worktree. For each parallel bundle N in the completed group:

Run: `python3 "<skill-directory>/scripts/worktree.py" remove --repo "$REPO_ROOT" --name "bundle-N"`

If status `"partial"`: warn "Worktree bundle-N not fully cleaned — manual removal may be needed: `git worktree remove .worktrees/bundle-N --force`". A partial removal does not block the next group — the worktree directory is gone even if the branch lingers.

All removals must complete before creating or dispatching worktrees for the next execution group. Do not proceed to the next group while any removal is in progress.

**Final cleanup**: After all execution groups complete (or on abort), remove all remaining worktrees:

Emit: `[Worktree] Cleanup: removing N worktrees`

Run: `python3 "<skill-directory>/scripts/worktree.py" remove-all --repo "$REPO_ROOT"`

If status `"partial"`: warn for each failure in the `failures` list: "Worktree .worktrees/<name> not cleaned up — manual removal: `git worktree remove .worktrees/<name> --force`". Do not block execution completion on cleanup failure.

---

## Team Mode

Team mode coordinates human developers for parallel bundles.

### Branch Naming

`feature/<slug>/bundle-N` (e.g., `feature/user-auth/bundle-2`)

### Team Instructions

The execute skill generates `spec-driven/<slug>/team-instructions.md` during Phase 0 step 4 if `--mode team` is active and the file does not exist. The file contains per-bundle team branch names, step assignments, and expected outputs derived from the bundle structure.

### Execution Flow

Team mode execution flow is defined in SKILL.md § Team Mode (Phase 1 variant). This section covers branch naming conventions and team instructions format only.

---

## Commit Message Format

```
feat(scope): description [STEP-N]
```

- **Type**: `feat`, `fix`, `refactor`, `test`, `docs` — select by change nature
- **Scope**: module or area affected
- **`[STEP-N]`**: enables `git log --grep="STEP-4"` for lookup

**Examples**:

```
feat(auth): add login and logout endpoints [STEP-1]
fix(routes): correct mount path for auth router [STEP-6]
test(auth): add integration tests for auth flow [STEP-7]
```

---

## Bundle Completion Summary

Present after each bundle's subagent completes:

```
Bundle 2: Core Implementation — COMPLETE (3/3 steps)

  [done] STEP-3: Implement login/logout logic      (abc1234) verified: npm test passed
  [done] STEP-4: Add JWT validation middleware      (def5678) verified: tsc passed
  [done] STEP-5: Create token model                 (ghi9012) verified: tsc passed

  Files: 3 created, 1 modified (+247 lines)
  Verification: 3/3 passed | Regression gate: passed

  Next: Bundle 3 — Integration (2 steps)
```

For partial completion:

```
Bundle 2: Core Implementation — PARTIAL (2/3 steps, 1 blocked)

  [done] STEP-3: Implement login/logout logic      (abc1234) verified: npm test passed
  [!]    STEP-5: Create token model                 BLOCKED: "Module not found"

  Blocked steps require resolution before dependent bundles proceed.
```

---

## Escalation Message Template

```
## Blocked: STEP-3 — Implement login/logout logic

**Error:** TypeError: session.verify() is not a function (auth.ts:47)

**Attempts:**
1. Initial implementation using express-session → TypeError on verify()
2. Switched to session.get() → Same error, method missing
3. Checked express-session docs, tried v2 API → Module version mismatch

**Blocked cascade:** STEP-4, STEP-5 (transitive dependents)

**Suggested resolution:**
- Check express-session version: `npm ls express-session`
- The API may have changed between v1 and v2

**To retry:** `/sds.execute <slug> --step STEP-3`
```

Each attempt line must describe what was tried and what error resulted. No generic "retried."

---

## Toolchain Detection

Detect from manifest files. Use the detected toolchain for static analysis and testing throughout execution.

| Manifest | Toolchain | Static Analysis | Test Runner | Install Command |
|---|---|---|---|---|
| `package.json` | Node.js / TypeScript | `npx tsc --noEmit`, `npx eslint` | `npm test` | `npm ci` |
| `pyproject.toml` / `setup.py` | Python | `mypy`, `ruff check` | `pytest` | `pip install -e .` or `pip install -r requirements.txt` |
| `Cargo.toml` | Rust | `cargo check`, `cargo clippy` | `cargo test` | `cargo build` |
| `go.mod` | Go | `go vet ./...`, `golangci-lint` | `go test ./...` | `go mod download` |
| `pom.xml` | Java (Maven) | `mvn compile` | `mvn test` | `mvn dependency:resolve` |
| `build.gradle` | Java (Gradle) | `./gradlew compileJava` | `./gradlew test` | `./gradlew dependencies` |
| `*.csproj` / `*.sln` | C# / .NET | `dotnet build --no-restore` | `dotnet test` | `dotnet restore` |
| `Makefile` | Language-agnostic | `make lint` if `lint` target exists; `make check` or `make build` if `check`/`build` target exists; otherwise skip | `make test` | `make install` if target exists; otherwise skip |

When multiple manifest files exist, prefer the one closest to the project root. If ambiguous, check CLAUDE.md or README for the primary toolchain.

The Install Command column provides the default `--install-cmd` for worktree creation.

**Node.js with parallelism > 1**: npm's `node_modules` contains tens of thousands of files, making parallel worktree provisioning slow (~2 min per worktree). If the project uses npm (not pnpm) and parallelism > 1, recommend switching to pnpm before parallel execution: "This project uses npm. Parallel worktree provisioning with npm is slow due to node_modules file count. Consider switching to pnpm (`npm install -g pnpm && pnpm import && pnpm install`) for significantly faster parallel provisioning." Present as structured input: "Switch to pnpm" / "Continue with npm". On "Continue with npm": proceed — the install will be slow but correct.

---

## Dry-Run Output Format

`--dry-run` shows the execution plan without executing:

```
Dry run: spec-driven/<slug>

  [done] STEP-1: Set up project structure           (already complete: abc1234)
  [done] STEP-2: Create database schema             (already complete: def5678)
  [next] STEP-3: Implement login/logout logic
           Verify: npm test -- --testPathPattern=auth
  [next] STEP-4: Add JWT validation middleware
           Verify: npx tsc --noEmit
  ------- Bundle 2 regression gate: npm test -------
  [next] STEP-5: Wire auth routes
           Verify: curl localhost:3000/api/auth/health

  Pending: 3 steps | Completed: 2 steps | Blocked: 0
```

Does NOT preview file changes.

---

## Progress File Format

The task skill creates per-bundle progress files (`progress-bundle-N.md`). The execute skill reads and updates them throughout execution.

### Current State Block

```
- Stage: [skeleton | depth | integration]
- Last completed: STEP-N — [title], or — (not started)
- Next up: STEP-N — [title]
- Blockers: [none | description]
```

### Step Status Table

```
| Step | Status | Commit | Notes |
|------|--------|--------|-------|
```

Status values: `pending`, `in-progress`, `done`, `blocked`. Commit column: git short hash after completion (`abc1234`). Multi-project: `auth-service:abc1234, client-sdk:def5678`. Notes: `—` (none), `[description]` (blocker), `Deferred: [criterion]` (runtime verification).

### Session Log

Three-line template per session entry:

```
### [date] — [context]
- Completed: [step IDs and titles]
- Decisions: [any, or "none"]
- Next: STEP-N: [title]
```

---

## Authority

This file provides reference tables, templates, and detailed algorithms. [SKILL.md](../SKILL.md) defines the execution protocol. If they conflict, SKILL.md is authoritative.
