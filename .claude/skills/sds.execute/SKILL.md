---
name: sds.execute
description: |
  Execute implementation steps from task bundles using subagent dispatch with branch
  isolation and merge-back. Use when someone says "execute", "run the plan",
  "start execution", "execute the steps", "implement the plan", or "run the bundle".
---

# Step Execution

Execute task bundles by dispatching subagents that implement steps, verify correctness, and commit with traceability on an isolated branch. After each bundle completes, merge back to the user's branch with explicit consent. The orchestrator coordinates — it never implements code directly.

## Trigger

```bash
/sds.execute user-auth
/sds.execute user-auth --bundle 2
/sds.execute user-auth --step STEP-5
/sds.execute user-auth --parallelism 3
/sds.execute user-auth --dry-run
/sds.execute user-auth --mode team
/sds.execute
```

## Flags

| Flag | Description |
| --- | --- |
| First argument (slug) | Slug identifying the task set. Resolves to task data via detected backend: markdown reads `spec-driven/<slug>/tasks.md`, graph queries Bundle/Step nodes by slug. |
| `--bundle N` | Start execution from Bundle N. Prior bundles must be complete — stops with error if any are incomplete. |
| `--step STEP-N` | Execute only a specific step (for recovery after unblocking). Dependencies must be `done` — if not, warn and stop. |
| `--parallelism N` | Number of concurrent subagents for parallel bundles (default: 1). Even at 1, subagent dispatch is used — the orchestrator never implements directly. |
| `--mode [agent\|team]` | Execution mode. `agent` (default): subagent dispatch. `team`: human branch coordination. |
| `--dry-run` | Show execution plan without executing. |
| `--skip-review` | Skip the inline bundle quality check (Layer 4). Useful when running `/sds.verify` afterward or for fast iteration. |

Flag interactions:
- `--step` overrides `--bundle` (single-step execution)
- `--step` implies parallelism 1 (single-step dispatch)
- `--dry-run` overrides all execution flags (read-only). `--skip-review` has no effect with `--dry-run` — dry-run exits before review runs. Scope flags survive under `--dry-run`: `--dry-run --bundle N` shows the plan from bundle N onward only; `--dry-run --step STEP-N` shows the plan for the target step's bundle only, highlighting STEP-N as the execution target.
- `--parallelism N` is a no-op when all bundles are `Parallel: no` — sequential execution groups always use the persistent sequential worktree regardless of N
- `--parallelism` is ignored in team mode (parallel bundles are executed by human developers, not subagents)
- `--step` targeting a parallel bundle under team mode dispatches a subagent — `--step` execution always uses subagent dispatch regardless of mode
- `--bundle N` targeting a bundle in a parallel execution group under team mode sets `teamGroup` to `merging-G-N` (G = execution group index) in the sidecar, then enters the team mode resume flow (see § Team Mode — On Resume in Team Mode) — the orchestrator verifies all bundles in execution group G through N-1 are complete, then resumes from the merge of bundle N. `--bundle N` targeting a bundle in a sequential execution group behaves the same as agent mode.
- `--skip-review` disables Layer 4 only — regression gates (Layer 3) and per-step verify clauses (Layers 1-2) still run
- `--skip-review` is implicit for single-step bundles (bundles with only 1 STEP) and for `--step` execution (reviewing one step's diff against a full bundle's intents produces false positives)

## Output

- Commits land on branch: `spec-driven/<slug>/exec`
- Reads per-bundle progress from: `spec-driven/<slug>/progress-bundle-N.md`
- Reads step definitions from: `spec-driven/<slug>/bundle-N.md`
- Creates git commits with `[STEP-N]` traceability references
- Two output backends (detected in Phase 0):
  - **Markdown** (default): reads bundle-N.md, passes bundle file paths to subagents — [references/output-markdown.md](references/output-markdown.md)
  - **Graph**: reads Bundle/Step nodes, uses `sds context` for selective context assembly — [references/output-graph.md](references/output-graph.md)

---

## Tool Usage

**Structured input**: For all bounded-answer questions (merge decisions, mode confirmations, resume confirmations, checkpoint decisions, or any question where valid responses can be enumerated), call a blocking tool that presents selectable options and pauses execution until the user responds — see execution-guide.md § Structured Input Resolution for the platform-specific mechanism. Text output alone does not satisfy this requirement. Use conversational text only for genuinely open-ended follow-ups (e.g., "What should I do about this blocker?").

Never present bounded options as plain-text numbered or lettered lists — always use the interactive mechanism. Plain-text lists allow the model to continue without waiting for an actual user selection, defeating mandatory interaction gates.

**Progress milestones**: Emit status at key transitions. Phase 0 uses `[N/M]` numbered format. Phases 1-2 use label prefixes (`[Execute]`, `[Merge]`).

**Mandatory interaction gates** (never self-answered — self-answering skips user review of execution scope and merge decisions):
1. **Execution Plan Confirmation** (end of Phase 0): Present bundle execution order, mode, and parallelism. The user confirms before any code is written.
2. **Merge-Back Decision** (Phase 2, per bundle — including parallel bundles and team mode bundles): Present bundle results and merge options. The user controls what lands on their branch.

**Wait for user response**: When presenting structured input, wait for the actual response before proceeding. Generating or inferring a response corrupts execution — the user decides what code merges to their branch.

**Commit constraint**: NEVER run `git merge` or `git merge --squash` without receiving explicit user approval at GATE 2 — merging is irreversible and the user may want to inspect the execution branch first.

**Orchestrator constraint**: The orchestrator NEVER creates, modifies, or deletes implementation files directly — it dispatches subagents for all implementation work. The orchestrator's scope is limited to: reading task artifacts, creating/switching branches, dispatching subagents, presenting results, running regression gates, and executing merge-back. This separation ensures the orchestrator's context window is preserved for coordination across bundles.

---

## Phase 0: Context Gathering (Always Runs)

**Before starting**: Read this reference file — it contains verification tables, error protocols, and mode-specific orchestration:
- [references/execution-guide.md](references/execution-guide.md) — branch lifecycle, verification chain, error classification, retry/rollback, merge-back protocol, parallel execution, team mode, progress format, toolchain detection

**Scripts**: This skill ships Python helper scripts at `scripts/` relative to this SKILL.md. All script references use the pattern `python3 "<skill-directory>/scripts/X.py"` where `<skill-directory>` is the directory containing this SKILL.md.

> **Authority**: SKILL.md defines the execution protocol. execution-guide.md provides reference tables and algorithms. If they conflict, SKILL.md is authoritative.

**Backend detection** (silent, first step): Check if `sds` and `dolt` are available in PATH by running `which sds && which dolt`. If both available, use **graph backend**. Otherwise, use **markdown backend** (default). Remember for session. The backend-specific output reference file (output-markdown.md or output-graph.md) is loaded at Phase 1 dispatch — do not read it during Phase 0.

**Steps:**

Emit: `[1/6] Resolving task input...`

**Capture repo root**: `REPO_ROOT=$(git rev-parse --show-toplevel)`. All subsequent paths that reference the repo root use this variable.

**Directory bootstrap**: Ensure `spec-driven/.sessions/` exists: `mkdir -p spec-driven/.sessions/`. If mkdir fails, warn: "Session state cannot be persisted — resume will not be available." Proceed without creating the sidecar; omit all sidecar read/write operations for this session.

1. **Resolve task input**:
   - If slug provided: validate slug format — must match `[a-z0-9-]` only. If invalid, stop: "Invalid slug — slugs must be lowercase alphanumeric with hyphens only." Read task data via detected backend. Markdown: read `spec-driven/<slug>/tasks.md`. Graph: query Bundle/Step nodes by slug. If task data is missing, stop: "No tasks found for slug '[slug]'. Run `/task <slug>` to create them first."
   - If `--step STEP-N` provided: locate the step's bundle. If the step ID is not found in any bundle, stop: "STEP-N not found in any bundle. Run `--dry-run` to see available steps." If found and STEP-N status is already `done`, present: "STEP-N is already complete. Re-executing will create a duplicate commit." Structured input: "Re-execute anyway" / "Cancel". On "Cancel", stop. If found, verify dependencies are `done`. If dependencies are not `done`, stop: "STEP-N depends on STEP-X which is [status]. Resolve dependencies first."
   - If no slug provided: scan `spec-driven/` for `*/tasks.md` files. If exactly one: confirm selection — if the user declines, stop: "No task selected." If multiple: present picker. If the user cancels or dismisses without selecting: stop — "No task selected — provide a slug to target a specific task: `/sds.execute <slug>`." If none: stop with guidance: "No task files found. Run `/task` to create one."

   Verify `status: final` in tasks.md frontmatter. If not `final`, stop: "Tasks status is '[status]' — expected `final`. Run `/task <slug>` to finalize."

   Set `EXEC_BRANCH="spec-driven/<slug>/exec"`. Steps 2+ use this variable for branch operations.

2. **Session check**: Check for existing sidecar at `spec-driven/.sessions/<slug>.execute.json`.
   - **Not found**: create the sidecar with initial state (`slug`, `backend`, `currentBundle: null`, `teamGroup: null`). Continue to step 3.
   - **Found — stale**: if `currentBundle` is null and no progress files show any `done` or `in-progress` steps, delete the sidecar: "Stale session detected — starting fresh." Continue to step 3.
   - **Found — branch deleted**: validate `git rev-parse --verify "$EXEC_BRANCH" 2>/dev/null`. If the execution branch does not exist: "Previous session found but execution branch deleted. Starting fresh." Delete the sidecar, continue to step 3.
   - **Found — baselines missing**: if the execution branch exists but `baselines` is missing or empty in the sidecar, checkout the execution branch (`git checkout "$EXEC_BRANCH"`), re-run steps 8-9 before offering resume. The previous session was interrupted before baseline recording completed. If baseline recording fails again, proceed with `exitCode: null` per step 8's normal failure handling — do not block resume.
   - **Found — resumable**: execution branch exists and baselines present. If sidecar contains `mergeStrategyRepeat: "revoked"`, do not re-offer merge strategy repeat during this session. If a sequential worktree exists (`python3 "<skill-directory>/scripts/worktree.py" list --repo "$REPO_ROOT"` returns the `"sequential"` entry), verify its branch is at the current exec HEAD. If they differ, reset it before dispatching the next bundle: `python3 "<skill-directory>/scripts/worktree.py" reset --repo "$REPO_ROOT" --name "sequential" --ref "$EXEC_BRANCH"`. Present the visual progress map (see execution-guide.md § Resume Protocol). Structured input: "Resume from [STEP-N — title of next pending step]" / "Start fresh". Replace the bracketed portion with the actual step identifier and title from the progress map (e.g., "Resume from STEP-6 — Wire auth routes"). On "Start fresh": run `python3 "<skill-directory>/scripts/worktree.py" list --repo "$REPO_ROOT"`. If worktrees exist, run worktree cleanup (see execution-guide.md § Worktree Cleanup). Then delete the sidecar, run `python3 "<skill-directory>/scripts/exec_branch.py" delete --repo "$REPO_ROOT" --branch "spec-driven/<slug>/exec"`, and continue to step 3.

Emit: `[2/6] Reading bundle structure...`

3. **Read bundle structure**: Read all bundle files and progress files. Determine execution order from bundle headers. Identify parallel annotations (`Parallel: yes/no`). Read conflict analysis from tasks.md. If `spec-driven/<slug>/design.md` exists, read its frontmatter and extract the value of the `test_capabilities` YAML key (an array of strings, e.g., `["unit", "e2e"]`). Record for Layer 4 dispatch. If absent, the key is missing, or the value is not an array, record `test_capabilities: null`.

4. **Mode resolution**:
   - If `--mode team`: after reading bundle structure (step 3), check whether any bundles are annotated `Parallel: yes`. If none, emit: "No parallel bundles found — `--mode team` has no effect. Proceeding as agent mode." Set mode to agent and continue. If parallel bundles exist, check for `spec-driven/<slug>/team-instructions.md`. If missing, generate it from the bundle structure: for each parallel bundle, list the team branch name (`feature/<slug>/bundle-N`), the bundle's steps, and the expected output. Present the generated file for confirmation before proceeding.
   - If `--mode agent` (default): proceed.
   - Apply `--parallelism N` (default 1). Even at parallelism 1, subagent dispatch is used.

Emit: `[3/6] Resolving project configuration...`

5. **Multi-project resolution**: When the workspace includes multiple project directories, resolve logical project names to filesystem paths. Inherit `projects` from tasks.md frontmatter. For each project entry, resolve `name` to a workspace directory using these rules in order: (1) match `identity` field against normalized git remote URLs (`git -C "<dir>" remote get-url origin`, strip protocol/`.git`/trailing slashes, lowercase), (2) basename match (`basename "<dir>" == project.name`), (3) if no match, prompt the user. If the user cannot provide a valid path, mark the project's steps as `blocked` with "Project not available in workspace."

6. **Read CLAUDE.md from each resolved project directory** (not just the primary). Extract coding standards and constraints. In multi-project mode, skills must read these explicitly — the platform does not auto-load CLAUDE.md from additional directories.

**If `--dry-run`**: Emit: `[dry-run] Execution plan ready — skipping branch creation and baseline.` Present the execution plan (see execution-guide.md § Dry-Run Output Format). In team mode, include team-specific annotations per GATE 1 format (execution method and branch names per bundle). Exit — do not create the execution branch, record baselines, or construct the tech-stack lens.

Emit: `[4/6] Creating execution branch...`

7. **Create execution branch**:
   - Run: `python3 "<skill-directory>/scripts/exec_branch.py" create --repo "$REPO_ROOT" --branch "$EXEC_BRANCH"`
   - If status `"error"` (Detached HEAD): stop with the script's `message` field.
   - If status `"exists"` and no sidecar was found (prior session aborted): present "Execution branch exists from a prior session." Structured input: "Delete and start fresh" / "Keep and resume". On "Delete": run `python3 "<skill-directory>/scripts/exec_branch.py" delete --repo "$REPO_ROOT" --branch "$EXEC_BRANCH"`, then re-run create. On "Keep": run `python3 "<skill-directory>/scripts/exec_branch.py" validate --repo "$REPO_ROOT" --branch "$EXEC_BRANCH"`. If validate returns `"missing"` or `"error"`: stop with the script's `message` field.
   - If status `"exists"` and resuming with sidecar: run `python3 "<skill-directory>/scripts/exec_branch.py" validate --repo "$REPO_ROOT" --branch "$EXEC_BRANCH"`. If validate returns `"missing"` or `"error"`: stop with the script's `message` field.
   - Record `USER_BRANCH` from the script's `userBranch` JSON field.
   - Update the sidecar with `userBranch`, `execBranch`, and `artifactHome`. For single-project mode, set `artifactHome` to `$REPO_ROOT`. For multi-project mode, set `artifactHome` to the resolved directory of the project identified as `artifact_home` in tasks.md frontmatter (from step 5).

Emit: `[5/6] Recording baseline...`

8. **Record execution baseline** on the execution branch (created in step 7):

   **Single-project**: Run: `python3 "<skill-directory>/scripts/baseline.py" record --repo "$REPO_ROOT" --test-cmd "<detected-test-command>"` (omit `--test-cmd` if no test suite detected). The script records the HEAD hash, runs the test suite, and distinguishes launch failures from test failures. Write the script's `hash` and `exitCode` to sidecar: `baselines: { "default": { "hash": "<hash>", "exitCode": N } }`.

   **Multi-project**: For each resolved project, run: `python3 "<skill-directory>/scripts/baseline.py" record --repo "<resolved-dir>" --test-cmd "<project-test-command>"` (omit `--test-cmd` if no test suite detected for that project). Write per-project baselines to sidecar: `baselines: { "<project-name>": { "hash": "<hash>", "exitCode": N } }` — use the project `name` from the `projects` map as the key.

   Layer 3 skips regression for projects with `exitCode: null` baselines (see execution-guide.md § Verification Chain, "No test suite" row).

   On resume, read persisted values from sidecar instead of re-capturing.

9. **Tech-stack quality lens**: Read manifest files (see execution-guide.md § Toolchain Detection) and CLAUDE.md from each project. Construct a per-project directive:

   > Apply idiomatic best practices for **[detected stack]** when writing new code in **[project-name]**. Do not refactor existing code — only apply to code created or modified by the current step. When a best practice conflicts with an explicit instruction in CLAUDE.md or a step definition, the explicit instruction wins.

   Store as the tech-stack quality lens for this session. Pass to each subagent dispatch as input 9 (see Phase 1 § Per-Bundle Dispatch step 3).

Emit: `[6/6] Preparing execution plan...`

### GATE 1: Execution Plan Confirmation

Present the execution plan:
- Bundle execution order with parallel annotations
- Mode and parallelism setting
- In team mode: annotate each bundle with its execution method — "subagent" (sequential execution group) or "team hand-off" (parallel execution group). Include expected team branch names for hand-off bundles.
- Steps per bundle with current status (pending/done/blocked)
- Context payload size per bundle (graph backend only). The context payload is the data package passed to each subagent — a JSON object (graph backend) or bundle file path (markdown backend).

Structured input (blocking tool call per § Structured Input Resolution): "Execute" / "Adjust parallelism" / "Abort"

On "Adjust parallelism": prompt for new value. If the value is not a positive integer, re-prompt: "Parallelism must be a positive integer." Re-present the execution plan. Do not re-run Phase 0 steps — only the plan display changes.
On "Abort": checkout the user's branch (`git checkout "$USER_BRANCH"`). Check for new commits: `git log --oneline "$USER_BRANCH".."$EXEC_BRANCH"`. If empty, delete the execution branch (`git branch -d "$EXEC_BRANCH"`). If commits exist, inform: "Execution branch has commits — keeping for inspection." Delete the sidecar (`rm "spec-driven/.sessions/<slug>.execute.json"`), exit.

NEVER self-answer. The tool call blocks until the user responds — execution consent is the user authorizing code changes to their repository.

---

## Phase 1: Bundle Execution

For sequential execution (parallelism = 1), Phase 2 runs after each bundle. For parallel execution (parallelism > 1), all parallel bundles complete before merge-back begins. Then process **one bundle at a time** in bundle order — for each parallel bundle:

1. Run Layer 4 (Phase 1 step 6) in that bundle's worktree — MUST complete before merge. When parallelism > 1, Layer 4 can run across all worktrees concurrently before beginning the per-bundle merge sequence.
2. Merge that worktree branch to exec (worktree → exec, not exec → user branch)
3. Run that bundle's full Phase 2 verification chain (Layer 3 regression gate, Layer 3b bundle verify, GATE 2)
4. Only after GATE 2 completes for that bundle, process the next

Do not merge any worktree branch before Layer 4 completes for that bundle. Do not merge all worktree branches before running Phase 2 — each bundle must pass its verification chain and GATE 2 before the next bundle's merge changes the exec branch state. See execution-guide.md § Worktree Execution, step 2.

If `--step STEP-N` was provided, locate the step's bundle. Dispatch a subagent for that bundle with an additional instruction: "Execute only STEP-N — skip other steps in the bundle." After the single step completes, proceed directly to Phase 2 for that bundle. Do not execute subsequent bundles.

For each bundle in execution order, dispatch a subagent to execute its steps. If `--bundle N` was provided: verify N is within range (1 to total_bundles). If out of range, stop: "Bundle N not found. Available bundles: 1-M. Run `--dry-run` to see the execution plan." If valid, skip bundles before N — mark them as already complete if their progress files confirm all steps are `done`, otherwise: run `git checkout "$USER_BRANCH"`. If no new commits exist on the execution branch (`git log --oneline "$USER_BRANCH".."$EXEC_BRANCH"` is empty), delete it (`git branch -d "$EXEC_BRANCH"`). Delete the sidecar (`rm "spec-driven/.sessions/<slug>.execute.json"`). Stop: "Bundle N-1 has incomplete steps. Complete earlier bundles first or use `--step` for recovery."

**Load output backend reference** (first bundle only — point of action):
- Graph: [references/output-graph.md](references/output-graph.md)
- Markdown: [references/output-markdown.md](references/output-markdown.md)

### Execution Groups

Scan bundle headers in order and group contiguous bundles by `Parallel` annotation into an ordered execution group list. Each execution group is either `seq` (one or more `Parallel: no` bundles, executed in order) or `par` (one or more `Parallel: yes` bundles, dispatched concurrently per `--parallelism`). Number execution groups from 0.

All bundles in execution group G must complete before execution group G+1 begins.

### Per-Bundle Dispatch

Emit: `[Execute] Bundle N: [name] (M steps)`

For each bundle, update sidecar: set `currentBundle` to the bundle about to execute. Record the pre-bundle HEAD: `PRE_BUNDLE_HEAD=$(git rev-parse HEAD)`. This hash is used for file change statistics and reset targets. **For parallel bundles (parallelism > 1):** `PRE_BUNDLE_HEAD` is re-recorded at merge time (see execution-guide.md § Worktree Execution, step b). Then:

1. **Verify preconditions**: All bundles in the current execution group must complete before the next execution group begins.

2. **Assemble context**:
   - **Graph backend**: Run `sds context STEP-N --profile implement --format json --slug "<slug>" --project-root "<project-root>"` for each step. The context payload includes step details, decisions, standards, verify clauses, and constraints scoped to that step.
   - **Markdown backend**: Read `spec-driven/<slug>/bundle-N.md`. Pass the bundle file path as context.

3. **Dispatch subagent**: Dispatch a subagent with:
   - Dispatch profile: `implementation` — set the `model` parameter per execution-guide.md § Dispatch Profile Resolution
   - The [step-executor-instructions.md](references/step-executor-instructions.md) reference as the instruction set
   - Worktree directory (input 6): the absolute path to the worktree
   - Bundle file path: rewritten to resolve under the worktree directory (e.g., `<worktree>/spec-driven/<slug>/bundle-N.md`)
   - Progress file path: rewritten to resolve under the worktree directory (e.g., `<worktree>/spec-driven/<slug>/progress-bundle-N.md`)
   - Context payload: graph backend assembles a JSON object via `sds context`; markdown backend passes the bundle file path (same as above — listed separately because graph produces a distinct artifact)
   - Pre-detected toolchain commands
   - Resolved project map (multi-project mode): rewrite project paths to resolve under the worktree directory
   - Tech-stack quality lens
   - Pattern file paths: rewritten to resolve under the worktree directory
   - Artifact home path (multi-project mode): rewritten to the worktree directory
   - (When `--step` active) Single-step override: the STEP-N ID to execute
   - Baselines: the `baselines` object from the sidecar (e.g., `{ "default": { "exitCode": 0 } }`). Enables the subagent to distinguish pre-existing failures from regressions during verification.

   Do NOT pass the execution branch name to step-execution subagents — they work on worktree branches and have no need to know the exec branch name. Passing it causes the subagent to checkout exec inside the worktree, defeating isolation. This applies to all subagents dispatched to worktrees, including Layer 4 review agents and remediation executors — they commit fixes in the worktree and their work merges to exec naturally.

   **All paths passed to the subagent MUST resolve under the worktree directory.** The worktree is a full working copy — all tracked files exist there. Passing paths that resolve under the main repo causes the subagent to read/write outside the worktree.

   The subagent commits the progress file once after all steps complete — not in individual step commits. Commit hashes are recorded in the progress file via `commit_step.py` after each step's code commit.

   **Autonomous execution**: Dispatch the subagent with autonomous execution permissions — the subagent runs non-interactively and must be able to read, write, run commands, and commit without per-operation approval. It cannot pause for user input.

   **Dispatch for parallelism > 1**: Create per-bundle worktrees and dispatch subagents to work in them (execution-guide.md § Worktree Execution). Do not use platform isolation — the orchestrator manages worktrees directly using git commands. Pass the worktree directory as input 6 to the subagent (same as sequential mode).

   **Dispatch for parallelism = 1**: Create a persistent worktree for sequential execution (execution-guide.md § Worktree Execution). Dispatch each subagent to the same worktree directory. After each bundle completes and passes Layer 4 (step 6), merge to exec and reset the worktree branch for the next bundle. If the subagent dispatch returns no result (platform-level failure or timeout), check for uncommitted changes in the worktree (`git -C "$REPO_ROOT/.worktrees/sequential" status --porcelain`). If dirty, reset: `git -C "$REPO_ROOT/.worktrees/sequential" reset --hard HEAD`, then `git -C "$REPO_ROOT/.worktrees/sequential" clean -fd`. Then present recovery options: "Retry bundle" / "Skip bundle and continue" / "Abort execution" (see step 5 for full handling).

4. **Monitor progress**: For parallelism > 1, read per-bundle progress files (`progress-bundle-N.md`) at 30-second intervals. Display status updates (see execution-guide.md § Parallel Progress Display). If no progress update for 10 consecutive intervals (~5 minutes), treat the subagent as unresponsive — proceed to step 5 for recovery options.

5. **Wait for completion**: When the subagent returns its JSON result, read the updated progress file. If the subagent fails: (1) mark all bundle steps as `blocked`, (2) present retry/sequential/skip options. See execution-guide.md § Subagent Failure Handling for details.

   Emit: `[Review] Bundle N: inline quality check`

6. **Inline quality check (Layer 4)**: Runs in the worktree after subagent completion, before merge to exec. Check skip conditions first. If any match, skip and note the reason:
      - `--skip-review` flag is active → skip. Note: "Inline quality check skipped (--skip-review)."
      - Bundle has only 1 STEP → skip. Note: "Inline quality check skipped (single-step bundle)."
      - `--step STEP-N` execution is active → skip. Note: "Inline quality check skipped (single-step execution)."

      If no skip condition is met, dispatch two **separate** review subagents in parallel. When parallelism > 1, Layer 4 can run across all worktrees concurrently — the worktrees are independent. Each agent is its own subagent dispatch — do not combine the Code Quality Reviewer and Test Quality Reviewer into a single agent. The separation prevents circular validation where one agent reads both implementation and tests.

      **Subagent 1 — Code Quality Reviewer**:
      - Dispatch profile: `implementation` — set `model` per execution-guide.md § Dispatch Profile Resolution
      - Instruction set: the Code Quality Reviewer section of [review-agents.md](references/review-agents.md) (assessment criteria + output schema)
      - Bundle file path: `<worktree-dir>/spec-driven/<slug>/bundle-N.md`
      - Diff range: `git -C "<worktree-dir>" diff "$EXEC_BRANCH"..HEAD`
      - Output file path: `<worktree-dir>/spec-driven/<slug>/review-cqr-bundle-N.json`

      **Subagent 2 — Test Quality Reviewer**:
      - Dispatch profile: `implementation` — set `model` per execution-guide.md § Dispatch Profile Resolution
      - Instruction set: the Test Quality Reviewer section of [review-agents.md](references/review-agents.md) (assessment criteria + output schema)
      - Bundle file path: `<worktree-dir>/spec-driven/<slug>/bundle-N.md`
      - Test file paths: from `git -C "<worktree-dir>" diff "$EXEC_BRANCH"..HEAD --name-only` filtered to test file patterns
      - `test_capabilities`: the value recorded in Phase 0 step 3 (pass null if absent or not an array).
      - Output file path: `<worktree-dir>/spec-driven/<slug>/review-tqr-bundle-N.json`

      Launch both subagents in a single parallel dispatch. Each writes its full assessment to its output file and returns only `PASS` or `FLAG: <file path>`. **NEVER read the assessment files** — route based on the verdict line only. The orchestrator cannot evaluate, summarize, or editorialize findings. If any agent fails to return results, skip that agent: "Inline quality check skipped ([agent] failed: [reason])."

      **Verdict routing** (follow review-agents.md § Resolution Flow for full protocol):
      - **Both PASS**: Record pass. Proceed to GATE 2.
      - **Any FLAG**: Enter the resolution loop (review-agents.md § Resolution Flow). The loop dispatches the Judge; if substantive findings remain, it remediates and re-reviews — up to 5 remediation cycles. The orchestrator never reads assessment files; routing is verdict-based only. Remediation executor receives the worktree directory, pre-detected toolchain, and baselines — same dispatch pattern as step executors.

      Record the Layer 4 result (pass, advisory findings, remediation outcome, or skipped with reason) for presentation at GATE 2.

### Team Mode (Phase 1 variant)

For `--mode team`:

Flag overrides in team mode: when `--step STEP-N` is active, skip the team flow — dispatch a subagent for the single step regardless of mode (see Flag interactions). When `--bundle N` targets a bundle in a parallel execution group, the orchestrator sets `teamGroup` to `merging-G-N` (G = execution group index, N = bundle number) and enters the resume flow (see Flag interactions).

Process execution groups in order. For each **sequential execution group G**: update sidecar `teamGroup: "seq-G"`, execute bundles via subagent dispatch (same as agent mode). For each **parallel execution group G**:

1. Update sidecar: `teamGroup: "waiting-G"`. Read `spec-driven/<slug>/team-instructions.md`.
2. Present: "Hand off execution group G parallel bundles to your team. Each developer runs their assigned bundle independently."
3. Pause for team execution.
4. On resume: read per-bundle progress files for execution group G, verify all bundles are complete. If any are incomplete, present their progress status. Structured input: "Wait — re-present hand-off pause" / "Merge completed bundles only (skip incomplete)" / "Abort". On "Skip incomplete": mark incomplete bundle steps as `blocked` with note "Skipped — parallel execution incomplete."
5. For each team branch in execution group G, in bundle order:
   a. Update sidecar: `teamGroup: "merging-G-N"` (N = bundle number).
   b. Merge into the execution branch: `git merge "feature/<slug>/bundle-N" --no-ff -m "merge: Bundle N — [name] (team)"`. If conflicts arise, present conflicting files. Structured input: "Resolve manually" / "Skip bundle". On "Resolve manually": pause for resolution, then `git -c core.editor=true merge --continue`. On "Skip bundle": run `git merge --abort`, mark all steps in the skipped bundle as `blocked` with note "Skipped due to merge conflict", skip Phase 2 for this bundle.
   c. Run Phase 2 steps 2-8 for this bundle (skip step 1 — no subagent result for team-executed bundles). GATE 2 runs between steps 6 and 7. Steps: regression gate (Layer 3), bundle verification (Layer 3b), inline quality check (Layer 4 — team mode runs post-merge; see Phase 2 step 4), bundle summary, pre-merge conflict check, GATE 2, and merge-back.
6. All team branches in execution group G must be merged and approved before the next execution group begins. Update `teamGroup` to the next execution group's initial state before proceeding.

#### On Resume in Team Mode

Read `teamGroup` from the sidecar:
- `seq-G`: resume sequential dispatch from the first incomplete bundle in execution group G.
- `waiting-G`: re-present the hand-off pause for parallel execution group G.
- `merging-G-N`: resume from the merge of bundle N in execution group G. Verify all bundles in execution group G numbered less than N have been merged (`git merge-base --is-ancestor "feature/<slug>/bundle-M" "$EXEC_BRANCH"` for each M < N in execution group G). If any prior bundle is not merged, present the list. Structured input: "Merge missing bundles first" / "Skip missing and continue from N" / "Abort". On "Skip": mark missing bundle steps as `blocked` with note "Skipped — out-of-order resume." If bundle N is already merged, skip to Layer 3 + GATE 2. Otherwise, begin from the merge step.
- `null`: begin from the first execution group.

---

## Phase 2: Merge-Back (Per Bundle)

Phase 2 runs on the exec branch after the worktree→exec merge for each bundle. The entry sequence is:
1. Layer 4 ran in the worktree (Phase 1 step 6) — **before** the worktree→exec merge
2. Worktree branch merged to exec (execution-guide.md § Worktree Execution)
3. Phase 2 begins here — regression gate, bundle verify, GATE 2 (exec→user branch)

Use `PRE_BUNDLE_HEAD` (the exec HEAD captured immediately before the worktree merge):
- **Parallel bundles**: the value re-recorded at merge time (execution-guide.md § Worktree Execution step b)
- **Sequential bundles**: the value captured in Phase 1 § Per-Bundle Dispatch

Layer 4 results are presented at GATE 2 — do not re-run Layer 4 in Phase 2 for agent mode bundles.

Emit: `[Merge] Bundle N complete — preparing merge`

1. **Read subagent results**: Parse the JSON result and the updated `progress-bundle-N.md`. Cross-reference step statuses with commit hashes.

   Emit: `[Verify] Bundle N: running regression gate...`

2. **Run regression gate (Layer 3)**: Compare test results against the Phase 0 baseline. Skip regression for projects with `exitCode: null` baselines (no test suite detected).

   **Single-project**: Run: `python3 "<skill-directory>/scripts/baseline.py" compare --repo "$REPO_ROOT" --test-cmd "<detected-test-command>" --baseline-exit-code N`

   **Multi-project**: For each project: `python3 "<skill-directory>/scripts/baseline.py" compare --repo "<resolved-dir>" --test-cmd "<project-test-command>" --baseline-exit-code N`

   If `"regression": true`: report which steps are likely responsible (use the script's `recentCommits` field) and include in the GATE 2 presentation. If the baseline exit code was 0 and current is non-zero, prepend: "WARNING: Regression detected — merging will land failing code on your branch."

3. **Run bundle verification (Layer 3b — advisory)**: Read the `**Bundle Verify**:` block from the bundle file header. If present, execute the condition/action/outcome on the execution branch. Failure does not block — include the result (pass or fail with details) in the GATE 2 presentation. If the `**Bundle Verify**:` block is absent, include this note in the GATE 2 presentation: "⚠ No bundle verify clause found — regression gate only. The task output may predate bundle verify clause generation." See execution-guide.md § Verification Chain, Layer 3b for detail.

   Emit: `[Verify] Bundle N: bundle verification complete`

4. **Inline quality check (Layer 4)**: For agent mode bundles, Layer 4 ran in the worktree during Phase 1 step 6 — skip this step and present the recorded result at GATE 2. For team mode bundles (no worktree), run Layer 4 now on the exec branch. Check skip conditions: `--skip-review` flag is active → skip; bundle has only 1 STEP → skip. (`--step` execution always dispatches a subagent and bypasses team mode — this condition cannot be reached here.) If no skip condition met, dispatch the Code Quality Reviewer and Test Quality Reviewer on the exec branch:
      - Diff range: `git diff <PRE_BUNDLE_HEAD>..HEAD`
      - Assessment file paths: `spec-driven/<slug>/review-{cqr,tqr}-bundle-N.json`
      - Resolution flow: same as Phase 1 step 6, but remediation executor operates on the exec branch — pass the execution branch name for this dispatch only.

5. **Present bundle summary**: Include per-step status, commit hashes, verification results, file change stats, and regression gate result. See execution-guide.md § Bundle Completion Summary.

   Emit: `[Merge] Bundle N: pre-merge conflict check...`

6. **Pre-merge conflict check**: Run: `python3 "<skill-directory>/scripts/conflict_check.py" --repo "$REPO_ROOT" --ours "$USER_BRANCH" --theirs "$EXEC_BRANCH"`
   If status `"clean"`: proceed to GATE 2. If status `"unavailable"`: skip the pre-merge check and proceed to GATE 2 — conflicts will be detected during the actual merge. If status `"conflict"`: present the `conflictingFiles` list and offer:
   - **"Re-execute sequentially"**: (1) Run `python3 "<skill-directory>/scripts/worktree.py" remove --repo "$REPO_ROOT" --name "bundle-N"`. (2) Reset the bundle's progress file: set all step statuses to `pending`, clear commit hashes. (3) Reset the execution branch to the pre-bundle state (`git reset --hard "$PRE_BUNDLE_HEAD"`). (4) Re-execute the current bundle with parallelism 1 in the persistent sequential worktree (create it if it does not exist). (5) Re-run Phase 2 from step 2 (regression gate through pre-merge check).
   - **"Proceed anyway"**: Continue to GATE 2 — actual conflict resolution happens during the merge (see Merge conflict recovery below).
   - **"Skip conflict check"**: Proceed to GATE 2 without pre-resolution — conflicts will surface during the actual merge if the user chooses Merge or Squash.

### GATE 2: Merge-Back Decision

Structured input (blocking tool call per § Structured Input Resolution): "Merge (preserve commits)" / "Squash (single commit)" / "Abort (inspect branch first)"

Each script call returns structured JSON. Route on the `status` field — do not chain script calls without checking status between them.

For non-final bundles:
On "Merge":
Run: `python3 "<skill-directory>/scripts/merge.py" merge --repo "$REPO_ROOT" --source "$EXEC_BRANCH" --target "$USER_BRANCH" --message "merge: Bundle N — [name]"`
If `"conflict"`: enter **Merge conflict recovery** below. If `"ok"`: proceed.

On "Squash":
Run: `python3 "<skill-directory>/scripts/merge.py" squash --repo "$REPO_ROOT" --source "$EXEC_BRANCH" --target "$USER_BRANCH" --message "feat: Bundle N — [name]"`
If `"squash_conflict"`: enter **Squash conflict recovery** below. If `"ok"`: proceed to sync-base.
Run: `python3 "<skill-directory>/scripts/merge.py" sync-base --repo "$REPO_ROOT" --source "$EXEC_BRANCH" --target "$USER_BRANCH" --message "sync: advance merge base after Bundle N squash"`
If `"error"`: warn "Merge base sync failed — subsequent bundle merges may re-apply squashed commits." Update sidecar: `mergeStrategyRepeat: "revoked"`. If `"ok"`: proceed.

**Squash conflict recovery**: `git merge --squash` does not create `MERGE_HEAD` — there is no pending merge state, so `merge --continue` cannot be used. Instead: present the `conflictingFiles` from the script output. Structured input: "Resolve manually" / "Abort" — these are mutually exclusive, choose before attempting resolution. On "Resolve manually": pause for the user to resolve conflicts in the working tree. After the user confirms resolution, run `git add -A`, then `git commit -m "feat: Bundle N — [name]"`. Proceed to sync-base. On "Abort": run `python3 "<skill-directory>/scripts/merge.py" hard-reset --repo "$REPO_ROOT"` to discard all staged and working tree changes, then `git checkout "$EXEC_BRANCH"`, and re-present GATE 2 options.

For the final bundle:
On "Merge":
Run: `python3 "<skill-directory>/scripts/merge.py" merge --repo "$REPO_ROOT" --source "$EXEC_BRANCH" --target "$USER_BRANCH" --message "merge: Bundle N — [name]"`
If `"conflict"`: enter **Merge conflict recovery** below. If `"ok"`: proceed (script returns to exec branch).

On "Squash":
Run: `python3 "<skill-directory>/scripts/merge.py" squash --repo "$REPO_ROOT" --source "$EXEC_BRANCH" --target "$USER_BRANCH" --message "feat: Bundle N — [name]"`
If `"squash_conflict"`: enter **Squash conflict recovery** above. If `"ok"`: `git checkout "$EXEC_BRANCH"` (return to exec for progress commit — step 7). No merge-base sync needed for the final bundle.

**Merge conflict recovery (non-squash merges only)**: When `merge.py merge` returns `"conflict"` status, the working tree is in a conflicted state — do NOT abort. Present the `conflictingFiles` from the script output. Structured input: "Resolve manually" / "Abort". On "Resolve manually": pause for the user to resolve conflicts in the working tree. After the user confirms resolution, run `git -c core.editor=true merge --continue` to finalize the merge. On "Abort": run `python3 "<skill-directory>/scripts/merge.py" abort --repo "$REPO_ROOT"` to restore a clean state, then `git checkout "$EXEC_BRANCH"`, and re-present GATE 2 options.

On "Abort": pause. Present: "Inspect `spec-driven/<slug>/exec` and resume when ready." On resume after abort: re-read the progress file, re-run the regression gate (Layer 3), re-present the bundle summary and GATE 2 options.

NEVER self-answer. The tool call blocks until the user responds — merge decisions are irreversible.

**Merge strategy repeat**: After the GATE 2 merge command completes with exit code 0 for the first bundle, and only if more than one bundle remains pending, present before proceeding to the next bundle — Structured input: "Yes — repeat this strategy for remaining bundles" / "No — confirm each"

> **Merge-strategy-repeat scope**: Skips only the GATE 2 interaction prompt — never the verification chain. Phase 2 steps 1-6 (regression gate, bundle verify, Layer 4 result, bundle summary, pre-merge conflict check) run in full for every bundle regardless of this setting.

If yes, apply the same strategy (Merge or Squash) to remaining bundles without re-prompting at GATE 2. If the repeated strategy is "Squash", the `merge.py sync-base` call runs automatically after each squash.

Revoke merge strategy repeat if any subsequent bundle has conflicts (pause and present the conflicting files), a regression (new non-zero exit code — update sidecar: `mergeStrategyRepeat: "revoked"`, present the regression warning and GATE 2 options), or a merge-base sync failure after squash — when `merge.py sync-base` returns `"error"`, set sidecar `mergeStrategyRepeat: "revoked"` immediately (see On "Squash" above). Do not auto-merge failing code — the user's consent assumed passing gates.

7. **Update sidecar**: Record the completed bundle. Update `currentBundle` to the next pending bundle.

8. **Blocked steps**: If the bundle had blocked steps, present them with retry guidance: "STEP-N blocked: [reason]. To retry: `/sds.execute <slug> --step STEP-N`"

---

## Phase 3: Execution Complete

After all bundles complete (or at session end), checkout the user's branch: `git checkout "$USER_BRANCH"`. Then:

1. **Present final summary**:

   ```
   Execution Summary: <slug>

     [done] Bundle 1: Foundation          2/2  (2 commits)
     [done] Bundle 2: Core Implementation 3/3  (3 commits)
     [done] Bundle 3: Integration         2/2  (2 commits)
     [done] Bundle 4: Verification        1/1  (1 commit)

     Total: 8/8 steps complete | 8 commits | 5 files created, 2 modified
     All verifications passed.

   Run /sds.verify <slug> to validate acceptance criteria.
   ```

2. **Deferred verifications** (omit if none):

   ```
   Deferred Verifications (require runtime/manual testing):
     STEP-3: "clicking Run Side-by-Side Comparison renders..."
     STEP-7: "completing all tabs marks module as complete in LocalStorage"
   ```

3. **Blocked steps** (omit if none):

   ```
     [!] Bundle 3: Integration  1/2  (1 blocked)
       STEP-7 blocked: "Cannot find module './auth'" — 3 attempts exhausted

   To retry: /sds.execute <slug> --step STEP-7
   ```

4. **Branch cleanup**: Offer to delete the execution branch (see execution-guide.md § Branch Lifecycle).

5. **Delete sidecar**: Remove `spec-driven/.sessions/<slug>.execute.json`.

6. **Next steps**: "Run `/sds.verify <slug>` to validate acceptance criteria against the implementation."

---

## Error Recovery

Classify errors before deciding on recovery. See execution-guide.md § Error Classification Heuristics for the decision tree.

- **Ambiguous requirement**: escalate immediately, no retry
- **Build/type/syntax**: retry with fix (max 3 attempts)
- **Test failure**: retry with fix (max 3 attempts)
- **Transient**: blind retry with backoff (max 3 attempts)

Each retry starts from a clean rollback to `PRE_STEP_HEAD`. After 3 failures, execute the full rollback procedure (see execution-guide.md § Rollback Procedure; scope: current in-progress step only — never already-committed steps) — cascade-block transitive dependents, continue independent steps.

---

## Handling Unknowns

Each row has a distinct response — do not assume a uniform pattern across rows.

| Pattern | Detection | Response |
| --- | --- | --- |
| Missing bundle file | `bundle-N.md` does not exist | Stop: "Bundle file not found. Re-run `/task <slug>`." |
| Missing progress file | `progress-bundle-N.md` does not exist | Stop: "Progress file not found. Re-run `/task <slug>`." |
| Invalid step ID | `--step STEP-N` not found in any bundle | Stop: "STEP-N not found. Run `--dry-run` to see available steps." |
| Invalid bundle number | `--bundle N` where N < 1 or N > total_bundles | Stop: "Bundle N not found. Available bundles: 1-M. Run `--dry-run` to see the execution plan." |
| Missing pattern file | Step references a file that doesn't exist | Do not stop — record assumption in progress file Notes column, implement without pattern reference, flag in commit message |
| Ambiguous step | Step bullet is vague or could mean multiple changes | One clarifying question, then conservative interpretation |
| Merge conflict | Pre-merge check detects conflicts | Present conflicting files, offer manual resolution or sequential fallback |
| Subagent unresponsive | No progress update for 10 consecutive polling intervals (default: 5 minutes) | Present options: retry, sequential fallback, skip |
| Pre-existing test failures | Baseline exit code is non-zero | Note: "Pre-existing failures." Compare exit codes, not pass/fail counts. |
| Dependency cycle | STEP-A blocked by STEP-B, STEP-B blocked by STEP-A | Should not happen (validated during task decomposition). Escalate immediately. |
