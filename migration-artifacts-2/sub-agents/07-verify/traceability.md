# Sub-Agent: Verify — Traceability

You verify every FR in `domains/{{DOMAIN}}/spec.md` has implementation and test.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `domains/{{DOMAIN}}/verify-traceability.md`

---

## Context Budget

Read `spec.md` (FR list), then for each FR, run **bounded** grep against `{{OUTPUT_PATH}}/{{DOMAIN}}`. Do not load file contents; only filenames + line counts.

---

## Procedure

1. Extract every `FR-*` ID from `spec.md`.
2. For each FR, search code and tests:
   ```bash
   grep -rln "{FR-id-or-keyword}" "{{OUTPUT_PATH}}/{{DOMAIN}}" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" --include="*.java" 2>/dev/null
   ```
3. Cross-reference with `domains/{{DOMAIN}}/tasks.md` to confirm bundle-to-FR mapping.

---

## Finding Levels

- CRITICAL: FR has neither code nor test
- HIGH: FR has code but no test
- MEDIUM: FR has test but AC coverage incomplete
- LOW: minor edge case missing

---

## Output

```markdown
# Verify — Traceability — {{DOMAIN}}

| FR | Code? | Test? | Bundle | Status |
|----|-------|-------|--------|--------|
| FR-1.1 | yes (api/login.ts) | yes (login.test.ts) | BUNDLE-3 | PASS |
| FR-1.2 | yes | no | BUNDLE-3 | HIGH |
| FR-1.3 | no | no | (missing) | CRITICAL |

## Summary
- Total FRs: {N}
- PASS: {N}, CRITICAL: {N}, HIGH: {N}, MEDIUM: {N}, LOW: {N}

## Findings
{detail per finding, finding ID = TRACE-NNN}
```

---

## Completion

```
[VERIFY-TRACEABILITY: {{DOMAIN}}]
CRITICAL: {N}, HIGH: {N}, MEDIUM: {N}, LOW: {N}
File: domains/{{DOMAIN}}/verify-traceability.md
```
