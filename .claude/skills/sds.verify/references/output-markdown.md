# Output: Markdown Backend

Reads execution artifacts from `spec-driven/<slug>/` directory to build the verification context. No external dependencies. This is the default backend.

## Reading Execution Artifacts

### Task Structure

Read `spec-driven/<slug>/tasks.md`. Extract from the Traceability table:
- FR → AC → STEP → Slice → Bundle mappings
- MANUAL steps (identified by absence of FR/AC trace)

If `spec-driven/<slug>/tasks.md` does not exist, stop: "No task file found. Run `/task <slug>` to create one first."

### Bundle Files

Read `spec-driven/<slug>/bundle-N.md` for each bundle. Extract per step:
- **STEP-N identifier** and trace reference (`[FR-N -> AC-N.M]` or `MANUAL`)
- **Verify clauses** (condition/action/expected outcome)
- **File paths** with action (`create`/`modify`/`delete`)
- **Intent** and **Standards** blockquotes

### Progress Files

Read `spec-driven/<slug>/progress-bundle-N.md` for each bundle. Extract:
- Step Status table (step ID, status, commit hash, notes)
- Deferred verification entries (`Deferred: [criterion]` in Notes column)

### Spec and Design

Read `spec-driven/<slug>/spec.md` for FRs, ACs, NFRs, constraints, success metrics.
Read `spec-driven/<slug>/design.md` for Findings, Decisions, Standards.

If either is missing, note the gap — agents scope to available artifacts.

## Building Verification Context

Assemble the shared context package for all 6 verification agents:

1. **Spec content**: FRs, ACs, NFRs, constraints, success metrics
2. **Design content**: Findings, Decisions, Standards, File Inventory
3. **Task content**: STEP entries with verify clauses (from bundle files)
4. **Progress**: step statuses and commit hashes (from all progress-bundle-N.md files)
5. **Changed files**: `git log --oneline --grep="STEP-" <baseline>..HEAD` on the execution branch, then `git diff --name-only <baseline>..HEAD` for the file list. Filter out gitignored paths: run `git ls-files -i --exclude-standard` and remove matches. The filtered list is the canonical scope for all agents.
6. **CLAUDE.md**: conventions from each resolved project directory
7. **Toolchain commands**: extracted from verify clauses in bundle files

### Execution Branch

Read the execution branch name from the session sidecar (`execBranch` field) or derive from convention: `spec-driven/<slug>/exec`. Verify the branch exists before running git commands against it.

### Traceability Chain (Markdown)

Build the traceability matrix by cross-referencing:
- tasks.md Traceability table: FR → AC → STEP → Bundle
- progress-bundle-N.md: STEP → commit hash
- git log: commit hash → changed files

This produces the FR → AC → STEP → Commit → Code Evidence chain. Test Evidence requires the verification agents to locate test files.

## Writing the Report

Write `spec-driven/<slug>/verify-report.md` using the template from [assets/verify-template.md](../assets/verify-template.md). Before writing, confirm no finding field contains a raw credential value. Replace any unredacted credential with `[REDACTED]`.

## Dry-Run / Report-Only

For `--report-only`, skip Phase 3 (remediation). The report is still written.
