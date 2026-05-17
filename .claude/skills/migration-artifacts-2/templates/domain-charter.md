# Domain Charter — {{DOMAIN}}

**One-pager.** Filled in by `01-decompose/domain-decompose.md`. Reviewed by tech lead and domain expert before Phase 02.

---

## Purpose

One sentence: what business capability does this domain own?

> _Example_: Owns user identity, authentication, and session lifecycle for all customer-facing applications.

---

## Scope

**In scope** (this domain owns):
- Capability A
- Capability B

**Out of scope** (other domains own):
- Capability X — owned by `{other-domain}`

---

## Size

| Metric | Value |
|--------|-------|
| Legacy LOC | {N} |
| Files | {N} |
| Source modules | {paths} |
| DB schema prefix(es) | {prefixes} |
| Test count | {N} |
| Hot files (top 5) | {paths} |

---

## Contracts (preview — finalized in `_contracts.yaml`)

**Inbound** (owned by this domain, consumed by others):
- {name} v{version} → consumed by {domains}

**Outbound** (consumed by this domain, owned by others):
- {name} v{version} ← owned by {domain}

---

## Data ownership

| Entity | Tables | Volume | PII? |
|--------|--------|--------|------|

---

## Team ownership

- **Primary team**: {team} (owner per `_codeowners.md`)
- **Lead engineer(s)**: @{handle}
- **Backup team**: {team}
- **Slack**: #{channel}
- **PagerDuty**: {schedule URL}

---

## Dependencies

**Depends on**:
- {domain} — for {reason}

**Required by**:
- {domain} — for {reason}

---

## Risk score: LOW | MEDIUM | HIGH

**Justification**:
- {bullet}
- {bullet}

Risk signals considered: hot files, bug-fix density (from `git-log-findings`), test coverage gaps, complexity, regulatory scope.

---

## Migration approach

- **Wave**: {N} (per `_migration-order.md`)
- **Strategy**: strangler-fig with progressive canary
- **Estimated duration**: {weeks}
- **Sub-domain decomposition needed**: yes / no (if yes, see `features/_index.md`)

---

## Success criteria

- 100% of legacy traffic routed to new
- Zero API-diff unexplained for 7 days
- Verify report: zero CRITICAL findings
- Performance within 10% of legacy baseline
- Compliance controls (per scope) green

---

## Open questions

- Q-1:
