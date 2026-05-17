# Sub-Agent: Verify — Code Quality

You verify code in `{{OUTPUT_PATH}}/{{DOMAIN}}` is clean: typechecks, lints, has no obvious smells.

---

## Parameters

- `{{DOMAIN}}`
- `{{OUTPUT_PATH}}` — path to the new app code (e.g. `apps/new`)

---

## Output Files

- `domains/{{DOMAIN}}/verify-code-quality.md`

---

## Context Budget

See `sub-agents/_shared/context-budget-rules.md`. Read only the inputs explicitly listed in Parameters; do not load full discovery dumps.

---

## Checks

```bash
# Type / compile
npx tsc --noEmit -p tsconfig.json 2>&1 | head -50
# or: go build ./{{DOMAIN}}/...; ./mvnw -pl {{DOMAIN}} compile; python -m mypy {{DOMAIN}}

# Lint with zero-warning policy
npm run lint -- {{OUTPUT_PATH}}/{{DOMAIN}} --max-warnings 0 2>&1 | tail -30

# Complexity (cyclomatic) — fail any function over 15
npx eslint --rule 'complexity: ["error", 15]' {{OUTPUT_PATH}}/{{DOMAIN}} 2>&1 | head -30

# Dead code (unused exports)
npx ts-prune {{OUTPUT_PATH}}/{{DOMAIN}} 2>&1 | head -30

# Smells
grep -rn "TODO\|FIXME\|HACK\|XXX\|@ts-ignore\|@ts-nocheck\|eslint-disable" {{OUTPUT_PATH}}/{{DOMAIN}} 2>/dev/null | grep -v __tests__ | head -20

# Console / print leftover
grep -rn "console\.\(log\|error\|warn\)" {{OUTPUT_PATH}}/{{DOMAIN}} --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v __tests__ | head -10

# Hardcoded secrets / keys
grep -rinE "(api[_-]?key|password|secret|token|bearer)\s*[:=]\s*['\"][^'\"]{8,}" {{OUTPUT_PATH}}/{{DOMAIN}} --include="*.ts" --include="*.py" --include="*.go" 2>/dev/null | grep -v __tests__ | grep -v "\.env" | head -10
```

---

## Finding Levels

- CRITICAL: compile/type errors, hardcoded secrets, eval/exec on user input
- HIGH: lint errors, `@ts-ignore` in production code, function complexity > 20
- MEDIUM: TODO/FIXME, console.log in prod, function complexity 15-20
- LOW: lint warnings, dead-code exports

---

## Output

```markdown
# Verify — Code Quality — {{DOMAIN}}

## Typecheck: PASS | FAIL
{summary; first 10 errors if FAIL}

## Lint: PASS | FAIL
{summary; first 10 issues if FAIL}

## Complexity offenders
| File | Function | Cyclomatic |

## Smell counts
| Smell | Count |
|-------|-------|
| TODO/FIXME | N |
| @ts-ignore | N |
| console.log | N |
| hardcoded-secret-suspect | N |

## Findings (CQ-NNN)
```

---

## Completion

```
[VERIFY-CODE-QUALITY: {{DOMAIN}}]
File: domains/{{DOMAIN}}/verify-code-quality.md
```
