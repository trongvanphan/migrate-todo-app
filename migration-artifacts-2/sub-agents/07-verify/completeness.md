# Sub-Agent: Verify — Completeness

You verify every file in `design.md` and every contract in `_contracts.yaml` is implemented.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `domains/{{DOMAIN}}/verify-completeness.md`

---

## Context Budget

See `sub-agents/_shared/context-budget-rules.md`. Read only the inputs explicitly listed in Parameters; do not load full discovery dumps.

---

## Procedure

1. Extract every file path from `domains/{{DOMAIN}}/design.md` "Directory structure" + `tasks.md` "Files to create".
2. For each, verify existence and non-empty:
   ```bash
   test -s "{path}" && echo OK || echo MISSING/EMPTY: {path}
   ```
3. Extract every owned contract from `_contracts.yaml`. For each, verify handler exists at expected path per design.
4. Run framework-specific endpoint discovery and confirm every contract endpoint is registered:
   ```bash
   # examples
   curl -s http://localhost:3000/api/__routes 2>/dev/null  # if route inspector exposed
   ```

---

## Finding Levels

- CRITICAL: handler / service / repository missing for a documented contract
- HIGH: test file missing
- MEDIUM: type definition missing
- LOW: utility / doc file missing

---

## Output

```markdown
# Verify — Completeness — {{DOMAIN}}

## Files
| Expected path | Exists | Size | Status |
|---------------|--------|------|--------|

## Contracts implemented
| Contract | Handler path | Status |

## Summary
- Files expected: {N}, missing: {N}, empty: {N}
- Contracts expected: {N}, implemented: {N}, missing: {N}

## Findings (COMPL-NNN)
```

---

## Completion

```
[VERIFY-COMPLETENESS: {{DOMAIN}}]
Missing files: {N}, missing contracts: {N}
File: domains/{{DOMAIN}}/verify-completeness.md
```
