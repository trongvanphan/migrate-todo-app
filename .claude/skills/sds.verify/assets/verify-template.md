---
title: "Verification Report: [Feature Name]"
spec_source: spec-driven/[spec-slug]/spec.md
spec_hash: sha256:[hash]
design_source: spec-driven/[spec-slug]/design.md
design_hash: sha256:[hash]
task_source: spec-driven/[spec-slug]/tasks.md
task_hash: sha256:[hash]
progress_sources: spec-driven/[spec-slug]/progress-bundle-*.md
status: [PASS | PASS WITH CAVEATS | FAIL]
date: [ISO date]
agents_run: [traceability, completeness, quality, testing, regression, security] # matches --focus flag values
total_findings: [N]
critical_count: [N]
high_count: [N]
medium_count: [N]
low_count: [N]
info_count: [N]
---

<!-- SECURITY: This report must not contain raw credential values (API keys, passwords, tokens, connection strings, private keys). All credential references use [REDACTED] with file:line pointers. If you see an unredacted credential in any field, replace it with [REDACTED] before writing. -->

# Verification Report: [Feature Name]

> Spec: [spec source] | Date: [date] | Overall Verdict: **[PASS | PASS WITH CAVEATS | FAIL]**

## Summary

[2-3 paragraph executive overview: what was verified, key findings, overall quality assessment.
Include: number of FRs verified, number of ACs checked, number of tasks assessed,
test suite status, and the most significant findings if any.]

---

## Dimension Verdicts

| # | Dimension | Verdict | Findings | Notes |
|---|-----------|---------|----------|-------|
| 1 | Traceability | [PASS / PASS WITH CAVEATS / FAIL / NOT ASSESSED] | [N findings] | [Brief note] |
| 2 | AC/NFR Completeness | [PASS / PASS WITH CAVEATS / FAIL / NOT ASSESSED] | [N findings] | [Brief note] |
| 3 | Code Quality + Conventions | [PASS / PASS WITH CAVEATS / FAIL / NOT ASSESSED] | [N findings] | [Brief note] |
| 4 | Test Quality | [PASS / PASS WITH CAVEATS / FAIL / NOT ASSESSED] | [N findings] | [Brief note] |
| 5 | Regression | [PASS / PASS WITH CAVEATS / FAIL / NOT ASSESSED] | [N findings] | [Brief note] |
| 6 | Security | [PASS / PASS WITH CAVEATS / FAIL / NOT ASSESSED] | [N findings] | [Brief note] |

---

## Findings

<!-- Group findings by severity. Omit empty severity groups entirely. -->

### CRITICAL

<!-- Omit this section if no CRITICAL findings -->

#### VF-[N]: [Finding Title]
- **Dimension**: [Traceability | AC/NFR Completeness | Code Quality + Conventions | Test Quality | Regression | Security]
- **Evidence**: [`file:line`] — [brief evidence description]
- **Affected ACs**: [AC-1.1, AC-2.3]
- **Suggested Fix**: [Actionable fix description]

---

### HIGH

<!-- Omit this section if no HIGH findings -->

#### VF-[N]: [Finding Title]
- **Dimension**: [Traceability | AC/NFR Completeness | Code Quality + Conventions | Test Quality | Regression | Security]
- **Evidence**: [`file:line`] — [brief evidence description]
- **Affected ACs**: [AC IDs or "—"]
- **Suggested Fix**: [Actionable fix description]

---

### MEDIUM

<!-- Omit this section if no MEDIUM findings -->

#### VF-[N]: [Finding Title]
- **Dimension**: [Traceability | AC/NFR Completeness | Code Quality + Conventions | Test Quality | Regression | Security]
- **Evidence**: [`file:line`] — [brief evidence description]
- **Affected ACs**: [AC IDs or "—"]
- **Suggested Fix**: [Actionable fix description]

---

### LOW / INFO

<!-- Combine LOW and INFO into one section for brevity. Omit if none. LOW/INFO findings use abbreviated table format — full details available in dimension agent outputs. -->

| ID | Severity | Dimension | Title | Evidence |
|----|----------|-----------|-------|----------|
| VF-[N] | LOW | [dimension] | [title] | [`file:line`] |
| VF-[N] | INFO | [dimension] | [title] | [note] |

---

## Finding Cross-Reference

<!-- Maps flat report IDs (VF-N) to original dimension-prefixed IDs (VF-XX-N). Omit if no renumbering occurred. -->

| Report ID | Original ID | Dimension |
|-----------|-------------|-----------|
| VF-1 | [VF-XX-N] | [dimension] |

---

## Traceability Matrix

| FR | AC | STEP | Commit | Code Evidence | Test Evidence |
|----|-----|------|--------|---------------|---------------|
| FR-1 | AC-1.1 | STEP-1 | [hash] | [`file:line`] | [`test-file:line`] |
| FR-1 | AC-1.2 | STEP-2 | [hash] | [`file:line`] | [`test-file:line`] |
| FR-2 | AC-2.1 | STEP-3 | [hash] | [`file:line`] | [MISSING] |
| FR-3 | AC-3.1 | STEP-6 | [hash] | [`file:line`] | [`test-file:line`] |

> Gaps in this matrix are reflected as findings above. [MISSING] entries correspond to specific VF-IDs.

<!-- Multi-project: In multi-project mode, the Commit column records per-project hashes
     (e.g., "auth-service:abc1234, client-sdk:def5678") and Code/Test Evidence columns
     include project-qualified paths (e.g., "auth-service::src/auth.ts:42"). -->

---

## Toolchain Results

<!-- Single-project: one table. Multi-project: one table per project, labeled. -->

| Check | Command | Exit Code | Result | Notes |
|-------|---------|-----------|--------|-------|
| Type Check | `npx tsc --noEmit` | 0 | PASS | — |
| Lint | `npx eslint src/` | 0 | PASS | — |
| Test Suite | `npm test` | 0 | PASS | 42 tests, 0 failures |
| Dep Audit | `npm audit` | 0 | PASS | 0 vulnerabilities |
| [Additional] | [command] | [code] | [PASS/FAIL] | [notes] |

> Baseline exit code from execution: [N]. Current exit code: [N]. Regression: [Yes/No].

<!-- Multi-project: repeat the table per project:
### auth-service
| Check | Command | Exit Code | Result | Notes |
...
> Baseline: auth-service:abc1234 (exit code: 0). Current: 0. Regression: No.

### client-sdk
| Check | Command | Exit Code | Result | Notes |
...
-->

---

## OWASP Top 10 Assessment

<!-- Include when Security agent was run. Omit if security was not in --focus scope. -->

| OWASP Category | Status | Finding |
|----------------|--------|---------|
| A01: Broken Access Control | [PASS / FINDING / NOT_APPLICABLE] | [VF-N or —] |
| A02: Cryptographic Failures | | |
| A03: Injection | | |
| A04: Insecure Design | | |
| A05: Security Misconfiguration | | |
| A06: Vulnerable Components | | |
| A07: Auth Failures | | |
| A08: Data Integrity Failures | | |
| A09: Logging Failures | | |
| A10: SSRF | | |

---

## Success Criteria

<!-- Include when the spec has a ## Success Metrics section. Omit entirely if no success metrics defined. -->

| Metric | Target | Evidence | Status |
|--------|--------|----------|--------|
| [Metric 1] | [target from spec] | [code/test evidence or "Requires post-launch measurement"] | [MET / NOT_MET / CANNOT_VERIFY] |

---

## Remediation Log

<!-- Populated during Phase 3e if remediation was performed. Omit entirely if --report-only or no remediation. Full remediation brief is at spec-driven/<slug>/remediation.md -->

| VF-ID | Action Taken | Result | Re-verified |
|-------|-------------|--------|-------------|
| VF-1 | Added test for AC-2.1 login failure path | Test passes | Yes — Test Quality PASS |
| VF-2 | Added JSDoc to public API methods | Convention met | Yes — Code Quality PASS |

---

## Convention Principles Added

<!-- Populated during Phase 3d if principles were accepted. Omit entirely if skipped. -->

<!-- Source Findings lists the VF-IDs that evidenced the theme. These are report metadata, not part of the principle text. -->

| Principle | Target File | Theme | Source Findings |
|-----------|-------------|-------|-------------|
| [Principle text] | [path/to/CLAUDE.md] | [Theme name] | [VF-1, VF-3] |

---

## Deferred Verifications

<!-- Only include if the progress tracker has Deferred: entries. Omit entirely if none. -->

| Task | Criterion | Reason |
|------|-----------|--------|
| STEP-3 | "clicking Run Side-by-Side Comparison renders..." | Requires runtime verification |
| STEP-7 | "completing all tabs marks module as complete" | Requires browser interaction |

---

## Verification Metadata

- **Agents dispatched**: [list of agents run]
- **Execution scope**: [N of M tasks verified (complete/partial)]
- **Artifact chain**: [complete/partial — note gaps]
- **Baseline commit**: [hash from progress tracker]
- **Verification commit range**: [baseline..HEAD]
