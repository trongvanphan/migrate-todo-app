# Intent Quality Guide

Guidance for writing step-level intent blocks. Referenced from [SKILL.md](../SKILL.md) for intent generation during Phase 1 decomposition.

---

## Purpose

Intent carries the business context that would otherwise be lost at the design-to-execution boundary. Good intent names the specific domain value, boundary condition, or logic path that creates semantic risk. Bad intent restates the step title without adding information.

Intent is NOT NULL in the step schema. Every STEP must have an intent block. Structural steps use `N/A — structural step` (see Edge Cases below).

---

## Good vs Bad Intent Examples

### Example 1: Timezone Conversion

- **Bad**: "This step implements date display for events."
- **Good**: "Events stored in UTC must render in the user's local timezone. An event at `2024-01-15T23:30:00Z` displays as January 16th for UTC+1 users — naive date formatting without timezone conversion will show the wrong date."

### Example 2: Permission Hierarchy

- **Bad**: "This step checks user permissions."
- **Good**: "Admin users inherit all member permissions implicitly — the role check must walk the hierarchy, not just match the literal role string. A direct `role === 'admin'` check will fail for endpoints that require 'member' access."

### Example 3: Currency Rounding

- **Bad**: "This step calculates order totals."
- **Good**: "Line item prices must be summed as integer cents, then converted to dollars for display. Summing floating-point dollar amounts accumulates IEEE 754 rounding errors — a 3-item order of $1.10 each may display as $3.30000000000000004."

### Example 4: Pagination Boundary

- **Bad**: "This step adds pagination to the list endpoint."
- **Good**: "Page N must start at offset `(N-1) * pageSize`, not `N * pageSize`. An off-by-one in the offset calculation causes the last item on page N to repeat as the first item on page N+1 — or one item to be skipped entirely."

---

## Deriving Intent from Design Artifacts

The task skill has structured design output as input. Use these artifacts to surface risks that would otherwise require deep codebase knowledge:

| Design Artifact | What It Reveals | Intent Signal |
|---|---|---|
| **Findings (F-N)** | Codebase patterns, existing behavior, technical constraints | Name the existing pattern that must be respected or the constraint that could be violated |
| **Decisions (AD-N)** | Chosen approaches with rationale and rejected alternatives | Name why the rejected alternative is wrong — the risk of accidentally implementing it |
| **Standards (S-N)** | Coding conventions, security rules, compliance requirements | Name the standard that applies and what violating it looks like |
| **Constraints** | Hard boundaries from the codebase or business domain | Name the boundary and the failure mode if crossed |
| **Risks** | Identified technical risks with impact and probability | Name the risk and the specific condition that triggers it |

**Example**: Finding F-3 says "The existing auth module uses JWT with 15-minute expiry." Decision AD-2 chose "short-lived JWTs + opaque refresh tokens" over "long-lived JWTs." Intent for the token generation STEP: "Access tokens must expire in 15 minutes (matching F-3's existing pattern). A longer expiry breaks the security model — revocation depends on short token lifetimes since JWTs cannot be individually invalidated."

---

## Heuristics for Identifying Non-Obvious Aspects

When generating intent, scan the step's implementation context for these risk signals:

| Signal | What to Name in Intent |
|---|---|
| **Boundary conditions** | The specific boundary value and what happens on each side |
| **Multi-path logic** | The specific paths and what distinguishes them |
| **Domain semantics** | The domain term and its non-obvious meaning |
| **Integration contracts** | The specific API constraint or assumption |
| **Data shape assumptions** | The column, field, or type that could be misinterpreted |
| **Ordering dependencies** | The sequence that must be preserved and why |
| **Non-functional constraints** | Reliability, consistency, or failure-handling requirements and what violating them looks like |

---

## Anti-Pattern: Title Restatement

Intent that restates the step title without adding information provides no value to downstream execution.

| Step Title | Bad Intent (title restatement) | Good Intent (adds information) |
|---|---|---|
| "Add input validation" | "This step adds validation to user inputs." | "Email validation must reject `+` aliases per the tenant's SSO policy — standard RFC 5321 validation will incorrectly accept them." |
| "Create error handling" | "This step creates error handling for the service." | "The upstream API returns 200 with an error body (not 4xx/5xx) for business rule violations. HTTP status-based error handling will miss these — parse the response body's `status` field." |

---

## Edge Cases

### Structural Steps

Purely structural steps (config, wiring, route registration, boilerplate scaffolding) may not have non-obvious implementation aspects. For these:

- Use: `> **Intent**: N/A — structural step`

Do not fabricate domain context for structural steps — forced intent on trivial steps dilutes the signal for steps where intent matters.

### MANUAL Steps

Infrastructure steps (CI, docs, deployment) that use the MANUAL trace convention still require intent. The intent should name what the infrastructure step enables and the risk of getting it wrong:

- **Good**: "CI must run the full test suite on PR branches before merge — without this gate, broken code can reach the main branch."
- **Bad**: "This step sets up CI."
