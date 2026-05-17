# Sub-Agent: Feature Spec

You write the spec for ONE feature within a feature-split domain. Same structure as `domain-spec.md` but scoped narrower.

Triggered by `domain-spec.md` when a domain exceeds 200K LOC.

---

## Parameters

- `{{DOMAIN}}`
- `{{FEATURE}}` — e.g., `sso`, `card-processing`, `returns`

---

## Output Files

- `domains/{{DOMAIN}}/features/{{FEATURE}}/spec.md` (≤1500 lines — features are smaller)
- `state/handoff/spec/{{DOMAIN}}__{{FEATURE}}.json`

---

## Context Budget

Read only:
- `domains/{{DOMAIN}}/charter.md`
- `domains/{{DOMAIN}}/features/_index.md` to know feature boundaries
- The specific module(s) for this feature (from feature `_index.md`)
- Relevant contracts from `domains/_contracts.yaml`

---

## Structure

```markdown
# Feature Spec — {{DOMAIN}} / {{FEATURE}}

**Parent domain**: {{DOMAIN}}
**Owner**: {assignee from features/_index.md}
**LOC (legacy)**: {N}
**Parent FRs covered**: EP-X.Y range

## Feature scope

One paragraph: what this feature does within the parent domain, and what it does NOT do.

## FRs

### FR-{{FEATURE}}-1: ...
**Acceptance criteria**:
- AC: Given X, when Y, then Z

### FR-{{FEATURE}}-2: ...

## Cross-feature contracts (intra-domain)

If this feature exposes anything to other features in the same domain, document here.

| Name | Kind | Consumers (features) |
|------|------|----------------------|

## Cross-domain contracts referenced

Pull from `domains/_contracts.yaml`. List only those this feature interacts with.

## Out of scope

- {explicit list}

## Traceability

| FR | Legacy file | Test | Contract |
```

---

## Rules

- Feature spec is independent: another team can implement this feature without reading other feature specs.
- If two features share business rules, define a shared sub-section in the parent domain's `charter.md`, not in either feature spec.
- A feature can be migrated in its own SDS sub-cycle (design, tasks, execute, verify scoped to feature).

---

## State Update

Set `domains[{{DOMAIN}}].features` to include status per feature:

```json
{
  "features_progress": {
    "sso": "spec",
    "password": "pending",
    ...
  }
}
```

(Add this structure to the domain's entry in state.)

---

## Completion

```
[FEATURE-SPEC COMPLETE: {{DOMAIN}}/{{FEATURE}}]
FRs: {N}
File: domains/{{DOMAIN}}/features/{{FEATURE}}/spec.md
```
