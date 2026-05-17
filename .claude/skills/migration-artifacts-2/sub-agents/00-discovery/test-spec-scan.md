# Sub-Agent: Test-as-Spec Scan (per module)

You extract behavioral specs from test files for **one module**. Tests = implicit requirements.

---

## Parameters

- `{{LEGACY_PATH}}`
- `{{MODULE}}`

---

## Output Files

- `discovery/modules/{{MODULE}}/test-spec.md` (≤2000 lines)

---

## Context Budget

If module has >500 test files, write summary + sample 50 representative tests + counts by file. Reference raw extraction at `discovery/modules/{{MODULE}}/test-spec.raw.txt`.

---

## Scans

```bash
# Locate test files
find "{{LEGACY_PATH}}/{{MODULE}}" -type f \( -name "*.spec.*" -o -name "*.test.*" -o -name "*_test.*" -o -name "test_*.*" -o -name "*Test.java" -o -name "*Spec.java" -o -name "*_spec.rb" \) -not -path "*/node_modules/*" -not -path "*/dist/*" 2>/dev/null | sort

# Extract describe/it/test names
grep -rhn "describe(\|it(\|test(\|context(" "{{LEGACY_PATH}}/{{MODULE}}" --include="*.spec.ts" --include="*.spec.js" --include="*.test.ts" --include="*.test.js" --include="*.spec.tsx" --include="*.test.tsx" 2>/dev/null | head -300

# pytest / unittest
grep -rhn "def test_\|class Test" "{{LEGACY_PATH}}/{{MODULE}}" --include="test_*.py" --include="*_test.py" 2>/dev/null | head -200

# RSpec
grep -rhn "describe \|it [\"']\|context [\"']" "{{LEGACY_PATH}}/{{MODULE}}" --include="*_spec.rb" 2>/dev/null | head -200

# JUnit
grep -rhn "@Test\|void test" "{{LEGACY_PATH}}/{{MODULE}}" --include="*Test.java" --include="*Spec.java" 2>/dev/null | head -200

# Go
grep -rhn "func Test" "{{LEGACY_PATH}}/{{MODULE}}" --include="*_test.go" 2>/dev/null | head -200

# E2E
find "{{LEGACY_PATH}}/{{MODULE}}" -path "*cypress*" -o -path "*playwright*" -o -path "*e2e*" 2>/dev/null | grep -v node_modules | head -50
```

---

## Output Structure

```markdown
# Test-as-Spec — {{MODULE}}

**Scanned at**: {ISO}
**Test files**: {N}
**Test cases**: {N}
**Frameworks detected**: {Jest | pytest | RSpec | JUnit | ...}

## Behavioral requirements extracted from tests

Group by source file. For each `describe/it` or `test_*`, paraphrase as a one-line requirement.

### {test_file_1}
- Given X, when Y, then Z
- Given A, when B, then C
- ...

### {test_file_2}
- ...

## Happy-path scenarios
{Bullet list of tests that exercise the primary flow.}

## Edge cases / error handling
{Bullet list of tests that exercise failures, boundary conditions, invalid input.}

## Coverage gaps (heuristic)
Files in `{{MODULE}}` with no corresponding test file:
- {path}

## E2E scenarios
{If present, describe the user journeys covered.}
```

---

## Completion

```
[TEST-SPEC-SCAN COMPLETE: {{MODULE}}]
Test files: {N}, Test cases: {N}
File: discovery/modules/{{MODULE}}/test-spec.md
```
