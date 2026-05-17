# Sub-Agent: Verify — Test Quality

You verify tests are real, meaningful, and run.

---

## Parameters

- `{{DOMAIN}}`
- `{{OUTPUT_PATH}}` — path to the new app code (e.g. `apps/new`)

---

## Output Files

- `domains/{{DOMAIN}}/verify-test-quality.md`

---

## Context Budget

See `sub-agents/_shared/context-budget-rules.md`. Read only the inputs explicitly listed in Parameters; do not load full discovery dumps.

---

## Checks

```bash
# Run all tests for domain
npm test -- --testPathPattern={{DOMAIN}} --coverage --coverageReporters=text --coverageReporters=json-summary 2>&1 | tail -80

# Placeholder tests
grep -rn "toBeTruthy()\|toBeDefined()\|expect(true)\|assert True$" {{OUTPUT_PATH}}/{{DOMAIN}} 2>/dev/null

# Empty test files
find {{OUTPUT_PATH}}/{{DOMAIN}} \( -name "*.test.*" -o -name "*.spec.*" \) -empty 2>/dev/null

# Test count
grep -rn "it(\|test(\|describe(\|def test_" {{OUTPUT_PATH}}/{{DOMAIN}} 2>/dev/null | wc -l

# Skipped tests
grep -rn "it\.skip\|describe\.skip\|xit\|xtest\|@pytest\.mark\.skip" {{OUTPUT_PATH}}/{{DOMAIN}} 2>/dev/null

# Test ownership: each test file should test exactly one source file
ls {{OUTPUT_PATH}}/{{DOMAIN}} | grep -v __tests__ | while read f; do
  base="${f%.*}"
  test -f {{OUTPUT_PATH}}/{{DOMAIN}}/__tests__/${base}.test.ts || echo "MISSING TEST: $f"
done
```

---

## Coverage thresholds (per service-tier file)

- Services / business logic: ≥ 80% line + branch
- Repositories: ≥ 70%
- Handlers: ≥ 60% (integration tests cover the rest)
- Utilities: ≥ 90%

---

## State machines

If the domain has state transitions (per `design.md`), there must be a state-transition test matrix. Look for tests that exhaustively cover `from_state × event → to_state`.

---

## Finding Levels

- CRITICAL: test suite fails to run, 0 tests, or every test is a placeholder
- HIGH: coverage below threshold for services
- MEDIUM: skipped tests, placeholder assertions in non-trivial tests, missing state-machine coverage
- LOW: missing edge-case tests

---

## Output

```markdown
# Verify — Test Quality — {{DOMAIN}}

## Suite: PASS | FAIL
- Tests: {N} passing, {N} failing, {N} skipped
- Coverage (lines): {X}% (services: {Y}%, repos: {Z}%, handlers: {W}%)

## Test ownership map
| Source | Test file | Status |

## State machines
| FSM | Transitions covered | Total | % |

## Placeholders / skipped
{list}

## Findings (TQ-NNN)
```

---

## Completion

```
[VERIFY-TEST-QUALITY: {{DOMAIN}}]
File: domains/{{DOMAIN}}/verify-test-quality.md
```
