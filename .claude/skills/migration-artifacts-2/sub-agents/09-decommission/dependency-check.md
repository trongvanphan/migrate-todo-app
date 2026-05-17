# Sub-Agent: Decommission — Dependency Check

Gate 2. Confirm no other code in the repo imports / calls into legacy `{{DOMAIN}}` code.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `decommission/{{DOMAIN}}/no-deps.md`

---

## Context Budget

See `sub-agents/_shared/context-budget-rules.md`. Read only the inputs explicitly listed in Parameters; do not load full discovery dumps.

---

## Procedure

1. Locate legacy `{{DOMAIN}}` source root (from `domains/{{DOMAIN}}/charter.md`).
2. Compute the list of public symbols / module paths exported by that code.
3. Grep the rest of the codebase for imports of those paths:

```bash
LEGACY_DOMAIN_PATH="src/legacy/{{DOMAIN}}"

# TypeScript / JavaScript
grep -rn "from ['\"].*${LEGACY_DOMAIN_PATH}\|require(['\"].*${LEGACY_DOMAIN_PATH}" . \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --exclude-dir=node_modules --exclude-dir=.git 2>/dev/null \
  | grep -v "${LEGACY_DOMAIN_PATH}"   # exclude in-domain imports

# Python
grep -rn "from .*${LEGACY_DOMAIN_PATH}.*import\|import .*${LEGACY_DOMAIN_PATH}" . --include="*.py" 2>/dev/null

# Java
grep -rn "import com\.legacy\.{{DOMAIN}}\." . --include="*.java" 2>/dev/null

# Go
grep -rn "import.*\"[^\"]*legacy/{{DOMAIN}}\"" . --include="*.go" 2>/dev/null

# Any HTTP/RPC callers calling internal legacy paths
grep -rn "legacy.*{{DOMAIN}}\|legacy-{{DOMAIN}}" . --exclude-dir=node_modules 2>/dev/null | head -50
```

4. Must return **zero** results (excluding in-domain imports + comments).

5. Also check infrastructure: any cron job, Lambda, or scheduled task still invoking legacy `{{DOMAIN}}`?
   - Search Terraform / CDK / Helm: `grep -rn "legacy-{{DOMAIN}}" infra/ 2>/dev/null`

---

## Output

```markdown
# Decommission Gate 2 — Dependency Check — {{DOMAIN}}

## Code imports
{N} hits (all in-domain / acceptable)

## Infrastructure references
{N} hits

## Verdict
PASS | HOLD

## Remaining references (if HOLD)
| File | Line | Snippet | Owner to remove |
```

---

## State Update

```json
{
  "domains[{{DOMAIN}}].decommission_gate_2_deps": {
    "verified_at": "{ISO}",
    "imports_remaining": 0,
    "infra_references_remaining": 0,
    "result": "pass"
  }
}
```

---

## Completion

```
[DECOMMISSION-DEP-CHECK: {{DOMAIN}}]
Result: PASS | HOLD
File: decommission/{{DOMAIN}}/no-deps.md
```
