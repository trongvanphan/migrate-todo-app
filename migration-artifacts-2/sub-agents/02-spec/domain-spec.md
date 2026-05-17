# Sub-Agent: Domain Spec

You write the hierarchical specification for **one domain**. Operates per domain in parallel with other domain-spec agents.

If the domain is large (>200K LOC, marked `feature_split: true` in state), you DO NOT write a single flat spec. Instead, emit a directive to schedule one `feature-spec.md` per feature.

---

## Parameters

- `{{DOMAIN}}` — domain name from `domains/_index.md`

---

## Output Files

Standard case:
- `domains/{{DOMAIN}}/spec.md` (≤2000 lines)
- `state/handoff/spec/{{DOMAIN}}.json`

Feature-split case:
- `domains/{{DOMAIN}}/features/_index.md` listing features
- Directive to dispatch `feature-spec.md` per feature

---

## Context Budget

Read only:
- `domains/{{DOMAIN}}/charter.md`
- `discovery/modules/{{MODULE}}/test-spec.md` for modules owned by this domain
- `discovery/modules/{{MODULE}}/api-routes.md` (headers only)
- `domains/_contracts.yaml` (filter to this domain's contracts)
- `discovery/git-findings/*.md` (sections referencing this domain's hot files)

Do not load full module code.

---

## Check Feature-Split Threshold

```
loc = state.domains[{{DOMAIN}}].loc
if loc > 200000 or state.domains[{{DOMAIN}}].feature_split:
    emit feature-split directive  → exit
else:
    proceed with single spec
```

---

## Spec Structure (single-spec case)

```markdown
# Spec — {{DOMAIN}}

**Owner**: {team}
**LOC (legacy)**: {N}
**FRs**: {N total}
**Contracts owned**: {N} (see domains/_contracts.yaml)

## Epics (EP-N)

### EP-1: {epic name}
Brief description.

#### FR-1.1: {feature title}
**Description**: ...
**Acceptance criteria**:
- AC-1.1.1: Given X, when Y, then Z
- AC-1.1.2: ...

**Source**: discovery/modules/{M}/test-spec.md (3 tests cover this), discovery/git-findings (1 bug fix Aug 2023)

#### FR-1.2: ...

### EP-2: ...

## Non-Functional Requirements

- **Availability**: 99.9% (matches contract SLA)
- **p95 latency**: per contract registry
- **Compliance**: {scope from parameters.COMPLIANCE_SCOPE}
- **Observability**: structured logs, traces, p95/p99 metrics
- **Audit**: every state transition logged with actor + timestamp

## Out of scope

- {explicit list of legacy features NOT being migrated, with reason}

## Open questions

- Q-1: ...

## Traceability

| FR | Legacy file(s) | Test source | Contract |
|----|---------------|-------------|----------|
| FR-1.1 | src/auth/login.ts | test/auth/login.spec.ts | auth.login |
```

---

## Feature-Split Directive (if loc > 200k)

Instead of `spec.md`, write `domains/{{DOMAIN}}/features/_index.md`:

```markdown
# Feature split — {{DOMAIN}}

This domain ({{LOC}} LOC) exceeds the 200K threshold. Decomposed into features:

| Feature | Suggested LOC | Source modules | Owner |
|---------|---------------|----------------|-------|
| sso | 40k | src/auth/sso/ | @alice |
| password | 35k | src/auth/password/ | @bob |
| mfa | 30k | src/auth/mfa/ | @alice |
| sessions | 20k | src/auth/sessions/ | @bob |

**Next**: scheduler will dispatch `02-spec/feature-spec.md` for each feature.
```

Update state: `domains[{{DOMAIN}}].features = [...]`.

---

## State Update

Append `"spec"` to `phases_complete` only after all domains have specs (handled by scheduler check).

For this domain: update `domains[{{DOMAIN}}].status = "spec"`.

Write `state/handoff/spec/{{DOMAIN}}.json` per `_shared/handoff-format.md`.

---

## Completion

```
[DOMAIN-SPEC COMPLETE: {{DOMAIN}}]
FRs: {N}
File: domains/{{DOMAIN}}/spec.md
Handoff: state/handoff/spec/{{DOMAIN}}.json
```

OR, if feature-split:

```
[DOMAIN-SPEC FEATURE-SPLIT: {{DOMAIN}}]
Features: {list}
File: domains/{{DOMAIN}}/features/_index.md
NEXT: schedule feature-spec.md per feature.
```
