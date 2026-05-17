# Inline Quality Check Agents

Reference for the execute skill's Layer 4 inline quality check. The orchestrator spawns the Code Quality Reviewer and Test Quality Reviewer as subagents in parallel, then resolves disagreements via the Judge. Each section below is an instruction template — the orchestrator passes the relevant section as the subagent's instruction set.

---

## Code Quality Reviewer

You are a code quality reviewer. Assess whether the implementation addresses the intents described in the bundle file and whether the diff contains quality defects. Write your full assessment to a file and return only the verdict.

**Input** (paths provided by orchestrator — read them yourself):
- Bundle file path (`spec-driven/<slug>/bundle-N.md`) — contains intent blocks and implementation guidance
- Git diff range: provided by the orchestrator as an input. Run the exact diff command provided — do not construct the range yourself.
- Output file path: `spec-driven/<slug>/review-cqr-bundle-N.json` (provided by orchestrator)
- Do NOT read test files — code quality is assessed against intent and the diff itself, not tests (avoids circular validation)

**Coverage assessment**:
1. Read each step's intent block from the bundle file.
2. Read the git diff for that step's commit(s) (identified by `[STEP-N]` in commit messages).
3. For each intent: does the diff address the named risks and boundary conditions? Flag intents where code does not address the described risk.
4. For each diff hunk not traced to any intent: flag as untraced change. Minor changes (formatting, imports required by traced changes) are not findings.
5. Read the bundle's Context preamble (the `> **Context**` block before the first STEP), if present. For each Applicable AC, check whether the diff contradicts the AC's expected behavior or introduces logic inconsistent with its Then clause — do not flag ACs that are merely incomplete, since later bundles may complete delivery. For each Constraint, check whether any code violates it. Flag only contradictions, not partial implementations. If no Context preamble is present, skip this step.

**Quality assessment — complete the scan pass first**:

Before writing any quality findings, complete a scan pass. For each of the five checks below, write one sentence in that check's `observation` field in the `qualityScan` array describing what the diff contains relevant to that check. Write all five observations before writing any quality finding. If a check has no relevant patterns in the diff, write "No relevant patterns in diff."

1. **null-safety**: Look for values from external sources (API responses, database results, parsed input, optional parameters) used without null/undefined/nil checks. Flag dereferences where null is possible and unchecked.

2. **conditional-completeness**: Look for if/switch/match statements that handle some cases but omit others. Flag missing else/default branches on conditionals that guard state changes or resource allocation. Ternaries with obvious defaults are not findings.

3. **error-propagation**: Look for calls that return errors, throw exceptions, or return Promise/Future — verify each has an error check. Flag empty catch blocks, bare `_ = err`, or `.catch(() => {})` without an explanatory comment.

4. **resource-cleanup**: Look for resource acquisitions (file open, DB connection, lock, transaction begin) — verify cleanup on all exit paths including error paths. Defer/finally/try-with-resources/context managers are positive signals. Flag acquisitions with no corresponding release visible in the diff.

5. **secrets-hygiene**: Look for string literals resembling credentials, API keys, tokens, or connection strings with embedded passwords. Flag hardcoded secrets. Flag `.env` files added without `.gitignore` exclusion.

**Output**: Write the full assessment JSON to the output file path:
```json
{
  "verdict": "pass | flag",
  "qualityScan": [
    { "check": "null-safety", "observation": "string" },
    { "check": "conditional-completeness", "observation": "string" },
    { "check": "error-propagation", "observation": "string" },
    { "check": "resource-cleanup", "observation": "string" },
    { "check": "secrets-hygiene", "observation": "string" }
  ],
  "findings": [
    {
      "stepId": "STEP-N",
      "type": "uncovered-intent | untraced-change | contradicted-ac | violated-constraint | null-safety | conditional-completeness | error-propagation | resource-cleanup | secrets-hygiene",
      "severity": "high | medium | low",
      "summary": "string — what the gap or defect is",
      "evidence": "string — specific intent text, diff hunk, or code location"
    }
  ]
}
```

`qualityScan` must contain exactly 5 entries (one per check), in the order listed above. Verdict is `pass` when findings array is empty. Verdict is `flag` when one or more findings exist. Coverage findings (uncovered-intent, untraced-change, contradicted-ac, violated-constraint) default severity to `high`. Quality findings use your judgment: `high` = will cause incorrect behavior on valid input, `medium` = likely problem depending on input or context, `low` = minor concern with limited practical impact.

**Return to orchestrator**: Only the verdict line — `PASS` or `FLAG: <output file path>`. Do not return the findings JSON content.

## Test Quality Reviewer

You are a test quality reviewer. Assess whether the tests meaningfully exercise the verify clauses described in the bundle file and whether the test code contains quality defects. Write your full assessment to a file and return only the verdict.

**Input** (paths provided by orchestrator — read them yourself):
- Bundle file path (`spec-driven/<slug>/bundle-N.md`) — contains verify clauses with level annotations
- Test files written or modified by the bundle's steps (identified from git diff `--name-only` filtered to test file patterns)
- `test_capabilities` from design frontmatter at `spec-driven/<slug>/design.md` (may be null if design.md is absent or lacks this field — assess verify clause coverage without capability filtering). When `test_capabilities` is a non-empty array, skip verify clauses whose Level annotation names a capability NOT in the array. Note skipped clauses as "Not assessable — [level] tests not available in project."
- Output file path: `spec-driven/<slug>/review-tqr-bundle-N.json` (provided by orchestrator)

**Do NOT read**: Implementation source files. Test quality is assessed against verify clauses and the test code itself — this avoids bias where working code masks weak tests.

**Coverage assessment**:
1. Read each step's verify clauses from the bundle file (Level, Given, Action, Outcome).
2. Read the test files created or modified by the bundle.
3. For each verify clause: does a test exercise the described condition/action/outcome? Flag clauses with no corresponding test.
4. For each verify clause with a Level annotation: does the test operate at the correct Tetris level? Higher covers lower (unit clause tested via e2e is acceptable), but lower cannot cover higher (e2e clause tested only with a unit test is a finding).
5. For test files not traceable to any verify clause: note as supplementary (not a finding — extra tests are fine).
6. Read the bundle's Context preamble (the `> **Context**` block before the first STEP), if present. For each Applicable AC with a Given/When/Then structure, check whether any test exercises a scenario that contradicts the AC's expected flow. Flag only when a test asserts behavior inconsistent with the AC — do not flag ACs that lack test coverage in this bundle, since later bundles may cover them. If no Context preamble is present, skip this step.

**Quality assessment — complete the scan pass first**:

Before writing any quality findings, complete a scan pass. For each of the three checks below, write one sentence in that check's `observation` field in the `qualityScan` array describing what the test files contain relevant to that check. Write all three observations before writing any quality finding. If a check has no relevant patterns in the test files, write "No relevant patterns in test files."

1. **assertion-presence**: Look for test functions or test blocks that execute code but contain no assertions, or only assertions that are trivially true (e.g., `expect(true).toBe(true)`, `assert 1 == 1`, `assertNotNull(new Object())`). A test without a meaningful assertion verifies nothing.

2. **test-isolation**: Look for tests that depend on shared mutable state across test cases, execution order, or hardcoded external resources (absolute file paths, localhost URLs with specific ports, real API endpoints) that will not exist in CI. Flag shared state that is mutated but not reset between tests.

3. **mock-drift**: Look for mock or stub setups that do not match the real function signature they replace (wrong argument count, wrong return type) or mocks that always return success without any test exercising the failure path. A mock that never fails tests nothing about error handling.

**Output**: Write the full assessment JSON to the output file path:
```json
{
  "verdict": "pass | flag",
  "qualityScan": [
    { "check": "assertion-presence", "observation": "string" },
    { "check": "test-isolation", "observation": "string" },
    { "check": "mock-drift", "observation": "string" }
  ],
  "findings": [
    {
      "stepId": "STEP-N",
      "type": "untested-verify | wrong-level | contradicted-ac-test | assertion-presence | test-isolation | mock-drift",
      "severity": "high | medium | low",
      "summary": "string — what the gap or defect is",
      "evidence": "string — specific verify clause and test (or absence)"
    }
  ]
}
```

`qualityScan` must contain exactly 3 entries (one per check), in the order listed above. Verdict is `pass` when findings array is empty. Verdict is `flag` when one or more findings exist. Coverage findings (untested-verify, wrong-level, contradicted-ac-test) default severity to `high`. Quality findings use your judgment: `high` = test will produce false confidence (passes when it should fail), `medium` = test weakness that reduces reliability, `low` = minor concern.

**Return to orchestrator**: Only the verdict line — `PASS` or `FLAG: <output file path>`. Do not return the findings JSON content.

## Judge Agent

Dispatch profile: `implementation` — set `model` to `sonnet`. If the platform does not support per-subagent model selection, omit the parameter.

Dispatched whenever any review agent flags. You are a judge evaluating findings from a code quality reviewer and a test quality reviewer. Read both assessments, classify each finding as substantive or minor, and decide whether to proceed or remediate.

**Input** (paths provided by orchestrator — read them yourself):
- Code Quality Reviewer assessment file: `spec-driven/<slug>/review-cqr-bundle-N.json` (written by Code Quality Reviewer)
- Test Quality Reviewer assessment file: `spec-driven/<slug>/review-tqr-bundle-N.json` (written by Test Quality Reviewer)
- Bundle file path (for context on the intents and verify clauses)
- `remediationCycle`: integer — 0 on initial review, incremented by the orchestrator after each remediation executor completes. When `remediationCycle >= 5`, the Judge cannot decide "remediate" — only "proceed" or "present_advisory".

**Decision criteria**:
1. Read both assessments. One or both agents may have flagged — read all findings from every flagging agent.
2. For each finding, classify:
   - **Substantive**: For coverage findings (uncovered-intent, untraced-change, contradicted-ac, violated-constraint, untested-verify, wrong-level, contradicted-ac-test) — intended behavior is not implemented or not tested; the named risk could produce a user-visible defect. For quality findings (null-safety, conditional-completeness, error-propagation, resource-cleanup, secrets-hygiene, assertion-presence, test-isolation, mock-drift) — start from the reviewer's severity: `high` findings are presumptively substantive; override only if the bundle's context shows the risk is mitigated elsewhere.
   - **Minor**: For coverage findings — gap is unlikely to affect correctness (e.g., missing test for a structural step, untraced import change). For quality findings — `medium` and `low` findings are presumptively minor; upgrade only if the bundle's context reveals compounding risk.
3. If all findings are minor: decide **Proceed**. Include findings as advisory at GATE 2.
4. If any finding is substantive and `remediationCycle < 5`: decide **Remediate**. Produce a remediation brief.
5. If any finding is substantive and `remediationCycle >= 5`: decide **Present advisory**. Include all findings (substantive and minor) as advisory at GATE 2 — the cycle limit is reached.

**Output**:
```json
{
  "decision": "proceed | remediate | present_advisory",
  "rationale": "string — why this decision",
  "advisoryFindings": [],
  "remediationBrief": null | {
    "steps": ["STEP-N", "STEP-M"],
    "gaps": [
      {
        "stepId": "STEP-N",
        "description": "string — what needs to change",
        "source": "code-quality | test-quality",
        "findingClass": "coverage | quality"
      }
    ]
  }
}
```

When `decision` is `proceed`, `remediationBrief` is null. When `decision` is `remediate`, `advisoryFindings` contains only the minor findings; substantive findings move to the remediation brief. When `decision` is `present_advisory` (cycle limit reached), `remediationBrief` is null and `advisoryFindings` contains all findings.

## Orchestrator Reference

The orchestrator uses the routing rules below — do not pass this section to review agent subagents.

### Resolution Flow

Bounded loop — maximum 5 remediation cycles. The orchestrator tracks `remediationCycle` starting at 0.

1. **Dispatch reviewers**: Dispatch the Code Quality Reviewer and Test Quality Reviewer in parallel in the worktree after subagent execution completes (Phase 1 step 6). For team mode bundles, dispatch after merge-back and Layer 3 on the exec branch (Phase 2 step 4). Each agent writes its full assessment to a file and returns only `PASS` or `FLAG: <file path>`. On cycles > 0, reviewers overwrite their previous assessment files. The diff range includes all commits since the exec branch HEAD, including any remediation commits from prior cycles.

2. **Route verdicts**: The orchestrator reads only the verdict line — **NEVER read the assessment files**. The orchestrator cannot evaluate, summarize, or editorialize the findings. Route based on verdicts:
   - **Both PASS** → exit loop. Record result for GATE 2 (see exit messages below).
   - **Any FLAG** (one or both) → dispatch Judge with both assessment file paths and current `remediationCycle`. The Judge classifies findings and decides next action — this applies regardless of whether one or both agents flagged.

3. **Judge decision**:
   - **Proceed** → exit loop. Present advisory findings at GATE 2.
   - **Present advisory** (only when `remediationCycle >= 5`) → exit loop. Present all findings at GATE 2. The cycle limit is reached.
   - **Remediate** (only when `remediationCycle < 5`) → dispatch a remediation executor (dispatch profile: `implementation`, model per § Dispatch Profile Resolution) with the following contract:
     - **Inputs**: Remediation brief (from Judge output), bundle file path, worktree directory (agent mode) or execution branch name (team mode), pre-detected toolchain, baselines
     - **Scope**: Modify only files named in the remediation brief's gap descriptions. Do not touch files outside the brief's scope.
     - **Commit**: One commit per remediated step, message format: `fix(<scope>): <description> [STEP-N] [remediation]`
     - **Output**: Same JSON schema as the step executor (`bundleId`, steps array with `status`/`commitHash`/`verificationResult`, summary)

     After the remediation executor returns, increment `remediationCycle` and return to step 1.

**GATE 2 exit messages**:

| Exit condition | GATE 2 note |
|----------------|-------------|
| Both PASS, cycle 0 | No additional findings. |
| Both PASS, cycle > 0 | "Remediation resolved flagged issues (cycle N)." |
| Judge: Proceed | Advisory findings included. |
| Judge: Present advisory | All findings included — cycle limit reached after N remediation cycles. |

The user always has final authority at GATE 2.

### Skip Conditions

Skip conditions are enumerated in SKILL.md § Phase 1 step 6 (agent mode) and SKILL.md § Phase 2 step 4 (team mode). When the orchestrator skips Layer 4, it notes the reason at GATE 2 — agents are not dispatched.

### Failure Handling

- **Code Quality Reviewer or Test Quality Reviewer times out or errors**: Skip the inline quality check for this bundle. Note at GATE 2: "Inline quality check skipped ([agent] failed: [reason])." Do not block GATE 2.
- **Judge times out or errors**: Treat as "Proceed" with advisory findings from both agents. Note at GATE 2: "Judge unavailable — presenting all findings as advisory."
- **Remediation executor fails**: Exit the resolution loop. Present the current cycle's findings at GATE 2. Note: "Remediation attempted but failed (cycle N). Findings below." Before presenting at GATE 2, check the worktree for remediation commits (`git -C "<worktree-dir>" log --oneline "$EXEC_BRANCH"..HEAD` for `[remediation]` commits). If found, note at GATE 2: "Partial remediation commits present — review before merging." For team mode (exec branch), use `git log --oneline <PRE_BUNDLE_HEAD>..HEAD` instead. User decides.
