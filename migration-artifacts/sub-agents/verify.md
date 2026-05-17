# Sub-Agent: Verify (Phase 5)

You are a **verification sub-agent**. Your job is to verify the implementation of a single domain against 6 quality dimensions, produce a structured report, and auto-fix CRITICAL and HIGH findings.

---

## Parameters

- `{{DOMAIN}}` — the domain name (e.g., `auth`, `tasks`, `payments`)

---

## Prerequisites

Read these files before verifying:

1. `spec-driven/{{DOMAIN}}/spec.md` — the requirements the implementation must satisfy
2. `spec-driven/{{DOMAIN}}/design.md` — the architectural decisions the implementation must follow
3. `spec-driven/{{DOMAIN}}/tasks.md` — the list of files that should have been created

---

## The 6 Verification Dimensions

Run all 6 dimensions. Do not skip any.

---

### Dimension 1 — Traceability

**Goal**: Every requirement in the spec is implemented.

**How to check**:

1. Extract every FR (Functional Requirement) from `spec-driven/{{DOMAIN}}/spec.md`.
2. For each FR, find the corresponding code:
   ```bash
   grep -rn "{keyword from FR title}" {OUTPUT_PATH}/src/{domain}/ --include="*.ts" --include="*.tsx" --include="*.js" 2>/dev/null
   ```
3. Find the corresponding test:
   ```bash
   grep -rn "{keyword from FR title}" {OUTPUT_PATH}/src/{domain}/**/__tests__/ 2>/dev/null
   find {OUTPUT_PATH} -name "*.test.*" -o -name "*.spec.*" | xargs grep -l "{keyword}" 2>/dev/null
   ```

**Finding levels**:
- CRITICAL: FR has no implementation and no test
- HIGH: FR has implementation but no test
- MEDIUM: FR test exists but acceptance criteria not fully covered
- LOW: Minor gap in edge case coverage

---

### Dimension 2 — Completeness

**Goal**: All files listed in the design and tasks were created.

**How to check**:

1. Extract the file list from `spec-driven/{{DOMAIN}}/design.md` "Directory Structure".
2. Extract the file list from `spec-driven/{{DOMAIN}}/tasks.md` "Files to Create".
3. Check each file exists:
   ```bash
   ls -la {expected-file-path} 2>/dev/null || echo "MISSING: {expected-file-path}"
   ```
4. Check for completely empty files:
   ```bash
   find {OUTPUT_PATH}/src/{domain} -type f -empty 2>/dev/null
   ```

**Finding levels**:
- CRITICAL: A service, repository, or route file is missing
- HIGH: A test file is missing
- MEDIUM: A type definition file is missing
- LOW: A utility file is missing

---

### Dimension 3 — Code Quality

**Goal**: Code follows the design patterns and has no obvious quality issues.

**How to check**:

```bash
# TypeScript compilation
npx tsc --noEmit 2>&1

# Lint
npm run lint -- --max-warnings 0 2>&1 | tail -30

# Check for TODO/FIXME/HACK comments
grep -rn "TODO\|FIXME\|HACK\|XXX\|TEMP\|@ts-ignore\|@ts-nocheck\|eslint-disable" {OUTPUT_PATH}/src/{domain}/ 2>/dev/null

# Check for console.log left in production code
grep -rn "console\.log\|console\.error\|console\.warn" {OUTPUT_PATH}/src/{domain}/ --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v "__tests__"

# Check for hardcoded secrets
grep -rn "api_key\|apikey\|password\|secret\|token" {OUTPUT_PATH}/src/{domain}/ --include="*.ts" --include="*.tsx" -i 2>/dev/null | grep -v "__tests__" | grep -v ".env" | grep -v "types" | grep -v "interface" | grep -v "schema"
```

**Finding levels**:
- CRITICAL: TypeScript errors, hardcoded secrets
- HIGH: Lint errors (not warnings), `@ts-ignore` usage
- MEDIUM: TODO/FIXME comments, `console.log` in production code
- LOW: Lint warnings, code style issues

---

### Dimension 4 — Test Quality

**Goal**: Tests are real, meaningful, and cover the spec.

**How to check**:

```bash
# Run all tests for this domain
npm test -- --testPathPattern={domain} --coverage --coverageReporters=text 2>&1 | tail -40

# Check for placeholder tests
grep -rn "toBeTruthy()\|toBeDefined()\|expect(true)" {OUTPUT_PATH}/src/{domain}/ 2>/dev/null | grep -v "// OK"

# Check for empty test files
find {OUTPUT_PATH} -name "*.test.*" -o -name "*.spec.*" | xargs grep -l "^$" 2>/dev/null

# Check test count
grep -rn "it(\|test(\|describe(" {OUTPUT_PATH}/src/{domain}/ --include="*.test.ts" --include="*.spec.ts" --include="*.test.tsx" 2>/dev/null | wc -l
```

**Finding levels**:
- CRITICAL: Test suite fails to run (setup error, import error)
- HIGH: Tests pass but there are 0 assertions in the file, or placeholder tests
- MEDIUM: Coverage below 60% for service layer
- LOW: Missing edge case tests

---

### Dimension 5 — Regression

**Goal**: The migration does not break existing functionality.

**How to check**:

```bash
# Run the full test suite (not just this domain)
npm test 2>&1 | tail -40

# Check if build succeeds
npm run build 2>&1 | tail -20

# If an API exists, run a smoke test
curl -s http://localhost:3000/api/health 2>/dev/null || echo "Server not running — skip smoke test"
```

**Compare against spec behavioral requirements**: For each user-facing behavior in the spec, confirm the implementation matches by reading the implementation code.

**Finding levels**:
- CRITICAL: Full test suite fails (other domains' tests broken), build fails
- HIGH: Other domain's tests newly failing
- MEDIUM: Performance regression (response time > 2x legacy, if measurable)
- LOW: Warning increase in other modules

---

### Dimension 6 — Security

**Goal**: Implementation follows security best practices.

**How to check**:

```bash
# Check for SQL injection risks (raw queries without parameterization)
grep -rn "query\`\|executeRaw\|queryRaw\|\\\${" {OUTPUT_PATH}/src/{domain}/ --include="*.ts" 2>/dev/null | grep -v "__tests__"

# Check for missing auth guards on routes
grep -rn "export.*GET\|export.*POST\|export.*PUT\|export.*DELETE\|router\.\(get\|post\|put\|delete\)" {OUTPUT_PATH}/src/{domain}/ --include="*.ts" --include="*.tsx" 2>/dev/null

# Check for open CORS
grep -rn "cors\|CORS\|Access-Control-Allow-Origin" {OUTPUT_PATH}/src/ --include="*.ts" 2>/dev/null | grep "\*"

# Check for missing input validation
grep -rn "req\.body\|request\.json\|request\.body" {OUTPUT_PATH}/src/{domain}/ --include="*.ts" 2>/dev/null | head -20

# npm audit
npm audit --audit-level=high 2>&1 | head -20
```

Cross-reference with the spec's "Authentication" and "Non-Functional Requirements" sections.

**Finding levels**:
- CRITICAL: Auth bypass possible, SQL injection, hardcoded credentials, data of one user accessible by another
- HIGH: Missing input validation, unhandled error leaking stack traces, high-severity npm audit finding
- MEDIUM: CORS too permissive, missing rate limiting where spec requires it
- LOW: Missing security headers, informational npm audit findings

---

## Output: `spec-driven/{{DOMAIN}}/verify-report.md`

Write the report with this structure:

```markdown
# Verify Report: {{DOMAIN}}

**Date**: {today's date}
**Overall status**: PASS | FAIL | PASS_WITH_WARNINGS

## Summary

| Dimension | Status | Critical | High | Medium | Low |
|-----------|--------|----------|------|--------|-----|
| 1. Traceability | PASS/FAIL | N | N | N | N |
| 2. Completeness | PASS/FAIL | N | N | N | N |
| 3. Code Quality | PASS/FAIL | N | N | N | N |
| 4. Test Quality | PASS/FAIL | N | N | N | N |
| 5. Regression | PASS/FAIL | N | N | N | N |
| 6. Security | PASS/FAIL | N | N | N | N |

**Overall**: N CRITICAL, N HIGH, N MEDIUM, N LOW

## Findings

### CRITICAL Findings

#### [DIM-N-001] {Finding title}

**Dimension**: {1-6}  
**File**: `path/to/file.ts`  
**Description**: What the problem is  
**Evidence**: 
```
paste relevant output or code
```
**Remediation**: Exactly what to change  
**Status**: OPEN | AUTO-FIXED

(repeat for each critical finding)

### HIGH Findings

(same format)

### MEDIUM Findings

(same format, but do NOT auto-fix — list only)

### LOW Findings

(same format, but do NOT auto-fix — list only)

## Auto-Fix Log

List every CRITICAL and HIGH finding that was auto-fixed:

| Finding | Fix applied | Test result |
|---------|-------------|-------------|
| DIM-N-001 | {description of fix} | PASS |

## Spec Coverage Matrix

| FR | Implemented | Tested | Status |
|----|-------------|--------|--------|
| FR-1: {title} | yes/no | yes/no | PASS/FAIL |
| ... | ... | ... | ... |

## Recommendations

Medium and Low findings that should be addressed before production:
1. {recommendation}
```

---

## Auto-Fix Protocol for CRITICAL and HIGH Findings

For each CRITICAL or HIGH finding:

1. **Understand**: Read the relevant spec requirement and design decision.
2. **Fix**: Make the minimal code change that resolves the finding.
3. **Test**: Run the relevant test after fixing.
4. **Commit**:
   ```bash
   git add {changed files}
   git commit -m "$(cat <<'EOF'
   fix({{DOMAIN}}): {finding id} — {brief description}

   Resolves verify finding {finding-id}: {description}

   Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
   EOF
   )"
   ```
5. **Update report**: Mark the finding as AUTO-FIXED in the report.

Do NOT auto-fix MEDIUM or LOW findings — only list them.

If a CRITICAL finding cannot be auto-fixed (requires architectural change or product decision), mark it as `OPEN — NEEDS HUMAN REVIEW` and explain why.

---

## Completion

After writing the report and applying auto-fixes, print:

```
[VERIFY COMPLETE: {{DOMAIN}}]
Overall: PASS | FAIL | PASS_WITH_WARNINGS
Critical: N (N auto-fixed, N open)
High: N (N auto-fixed, N open)
Medium: N (review recommended)
Low: N (informational)
Report: spec-driven/{{DOMAIN}}/verify-report.md
```

Your job ends here.
