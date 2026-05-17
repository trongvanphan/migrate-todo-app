# Output: Markdown Backend

Reads task artifacts from `spec-driven/<slug>/` directory. Writes progress updates to per-bundle progress files. No external dependencies. This is the default backend.

## Reading Inputs

### Bundle Structure

Read `spec-driven/<slug>/tasks.md`. Extract from frontmatter:
- `slug` — project identifier
- `strategy` — decomposition strategy used
- `total_steps`, `total_bundles` — execution scope
- `status` — must be `final` (if `draft`, stop: "Tasks are still in draft. Run `/task <slug>` to finalize.")
- `projects` — multi-project workspace map (if present)
- `artifact_home` — which project hosts `spec-driven/`

From the document body, extract bundle headers for execution ordering. The `Parallel:` annotation on each bundle header determines execution mode.

If `spec-driven/<slug>/tasks.md` does not exist, stop with guidance: "No task file found at `spec-driven/<slug>/tasks.md`. Run `/task <slug>` to create one first."

### Bundle Files

Read `spec-driven/<slug>/bundle-N.md` for each bundle. Each bundle file is self-contained: bundle header metadata + all STEP entries. Extract per step:
- **STEP-N identifier** and trace reference (`[FR-N -> AC-N.M]` or `MANUAL`)
- **File paths** with action (`create`/`modify`/`delete`) and optional project qualifier
- **Effort** estimate (XS/S/M/L)
- **Intent** and **Standards** blockquotes
- **Sub-steps** (implementation bullets)
- **Verify** clauses (condition/action/expected outcome)
- **Dependencies** (`Depends on` / `Enables` / `Parallel with`)
- **Pattern reference** (existing file to follow)

If a bundle file does not exist, stop with guidance: "Bundle file `spec-driven/<slug>/bundle-N.md` not found. Re-run `/task <slug>` to regenerate."

### Progress Files

Read `spec-driven/<slug>/progress-bundle-N.md` for each bundle. Extract:
- Step Status table (step ID, status, commit hash, notes)
- Current State block (last completed, next up, blockers)
- Session Log entries

If a progress file is unexpectedly absent during execution (after the orchestrator has confirmed it exists), record all steps in the affected bundle as `blocked` in the output JSON with note "Progress file missing — cannot record state" and surface the error. Do not stop silently.

### Conflict Analysis

Read the Conflict Analysis table from `tasks.md`. Hot files (touched by multiple steps across bundles) inform execution sequencing.

## Assembling Subagent Context

For each bundle dispatch, assemble the context payload from markdown sources:

1. Read `spec-driven/<slug>/bundle-N.md` — the self-contained step definitions
2. Read `spec-driven/<slug>/progress-bundle-N.md` — current status
3. Extract pattern file paths from step definitions — pass as paths, not content
4. Include pre-detected toolchain commands
5. Include resolved project map (multi-project mode)
6. Include tech-stack quality lens (per-project directives)

Pass the bundle file path to the subagent. The subagent reads the file independently — do not embed bundle content in the subagent prompt. This reduces orchestrator token usage and prevents content drift.

## Writing Progress Updates

The orchestrator updates progress files at bundle boundaries only. Subagents update their own `progress-bundle-N.md` during execution.

### After Bundle Completion

Read the subagent's updated `progress-bundle-N.md`. Present the bundle summary to the user including:
- Per-step status, commit hashes, and verification results
- File change statistics (`git diff --stat` between pre-bundle HEAD and current HEAD)
- Regression gate result (Layer 3)

### Session Log Entry

Append to the bundle's progress file after merge-back:

```
### [date] — Bundle N merged
- Completed: STEP-3: Implement login, STEP-4: Add middleware, STEP-5: Create model
- Decisions: none
- Next: Bundle M
```

## Resume Detection

Cross-reference progress files with `git log --oneline --grep="STEP-"` on the execution branch:

- **`in-progress` with no matching commit**: Reset to `pending`. Note: "Previous session interrupted — will re-execute STEP-N."
- **`in-progress` with a matching `[STEP-N]` commit**: Treat as `done` — record the commit hash. Do not re-execute.
- **`done` with no matching commit**: Anomaly. Reset to `pending` with note: "Progress file shows done but no commit found — will re-execute."

## Dry-Run Output

For `--dry-run`, read all bundle and progress files. Present:
- Execution order (bundle sequence with parallel annotations)
- Per-step status (done/pending/blocked)
- Verification commands per step
- Regression gate commands per bundle

Do not preview file changes. Do not execute any steps.
