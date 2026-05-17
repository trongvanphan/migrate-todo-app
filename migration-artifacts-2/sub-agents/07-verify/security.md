# Sub-Agent: Verify — Security

You verify the implementation against the security requirements in `spec.md` + `design.md`.

---

## Parameters

- `{{DOMAIN}}`
- `{{OUTPUT_PATH}}` — path to the new app code (e.g. `apps/new`)

---

## Output Files

- `domains/{{DOMAIN}}/verify-security.md`

---

## Context Budget

See `sub-agents/_shared/context-budget-rules.md`. Read only the inputs explicitly listed in Parameters; do not load full discovery dumps.

---

## Checks

```bash
# Auth guards on every route
grep -rn "export.*\(GET\|POST\|PUT\|PATCH\|DELETE\)\|router\.\(get\|post\|put\|patch\|delete\)\|@\(Get\|Post\|Put\|Delete\)Mapping" {{OUTPUT_PATH}}/{{DOMAIN}} 2>/dev/null
# Then for each handler, look for auth middleware

# SQL injection risk: raw queries with string concat
grep -rnE "\\\$\{[^}]+\}.*FROM|query\s*\+\s*" {{OUTPUT_PATH}}/{{DOMAIN}} --include="*.ts" --include="*.py" --include="*.go" 2>/dev/null | grep -v __tests__

# Hardcoded secrets
grep -rinE "(api[_-]?key|password|secret|token|bearer)\s*[:=]\s*['\"][^'\"]{8,}" {{OUTPUT_PATH}}/{{DOMAIN}} 2>/dev/null | grep -v __tests__ | grep -v "\.env\.example"

# 403 vs 404 leakage
# (resource-not-found should be 404 for unauth users to avoid revealing existence)
grep -rn "throw.*Forbidden\|status.*403" {{OUTPUT_PATH}}/{{DOMAIN}} 2>/dev/null

# Open CORS
grep -rn "Access-Control-Allow-Origin.*\*\|cors.*origin.*\*" {{OUTPUT_PATH}} --include="*.ts" 2>/dev/null

# Missing input validation
grep -rn "req\.body\|request\.json()\|request\.body" {{OUTPUT_PATH}}/{{DOMAIN}} 2>/dev/null | head -20
# Cross-check: is there a Zod/Pydantic/JSR-303 validator before this is used?

# Dependency vulnerabilities
npm audit --audit-level=high --omit=dev 2>&1 | head -30

# Authn at handler boundary — every route handler must call requireAuth() or similar
# (project-specific; encode the rule per stack)
```

---

## Cross-domain isolation

Ensure one user's data cannot be accessed by another:
- Search for ID-based queries that don't include the actor user_id:
  ```bash
  grep -rn "findById\|findOne.*id:" {{OUTPUT_PATH}}/{{DOMAIN}} 2>/dev/null
  ```
- Each should include `userId` filter or be explicitly an admin path.

---

## Finding Levels

- CRITICAL: auth bypass, SQL injection, hardcoded secret, cross-tenant data leak
- HIGH: missing input validation, unhandled exception leaks stack, high-severity CVE
- MEDIUM: 403 instead of 404 leaks resource existence, permissive CORS
- LOW: missing security headers, informational CVE

---

## Output

```markdown
# Verify — Security — {{DOMAIN}}

## Auth coverage
| Route | Auth required? | Implementation |

## Input validation
| Handler | Validator | Coverage |

## Findings (SEC-NNN)
```

---

## Completion

```
[VERIFY-SECURITY: {{DOMAIN}}]
File: domains/{{DOMAIN}}/verify-security.md
```
