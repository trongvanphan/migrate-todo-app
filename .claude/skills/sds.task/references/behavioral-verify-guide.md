# Behavioral Verify Guide

Guidance for generating behavioral verify clauses. Referenced from [SKILL.md](../SKILL.md) for verify clause generation during Phase 1 STEP decomposition.

---

## Schema Mapping

Each verify clause maps to the `verify_clause` table schema:

| Verify Component | Schema Field | Description |
|---|---|---|
| **Level** | `level` | The verification level (unit, integration, e2e, or inspection) |
| **Given** | `condition_text` | The risky condition being tested |
| **Action** | `action` | The code path under test |
| **Outcome** | `expected_outcome` | The correct result |

Every verify clause must have all four components.

---

## Behavioral vs Structural Distinction

**Structural** verification checks that code exists and compiles. **Behavioral** verification checks that code produces the correct outcome under specific conditions.

| Structural (insufficient) | Behavioral (required) |
|---|---|
| "compiles" | "given a UTC event at 23:30, a UTC+1 user sees the next day's date in the UI" |
| "test passes" | "mock 3 consecutive failures, then succeed — assert exactly 4 attempts and exponential backoff intervals" |
| "assertNotNull" | "given an admin user, the member-only endpoint returns 200 (not 403)" |
| "works correctly" | "given 3 line items of $1.10, the order total displays as $3.30, not $3.30000000000000004" |

The key test: **does the verify clause catch a semantically wrong implementation that still compiles?** If "compiles" would pass for both the correct and incorrect version, the verify clause is structural.

---

## Behavioral vs Structural Example Pairs

### Example 1: Retry Logic

- **Structural**: "Test passes" / "assertNotNull on retry result"
- **Behavioral**: "Mock the upstream API to fail 3 times then succeed. Assert: exactly 4 attempts were made, backoff intervals increase exponentially, and after retry exhaustion (mock 4+ failures), the error message includes the attempt count and last error."

### Example 2: Currency Rounding

- **Structural**: "Calculation compiles" / "Result is not null"
- **Behavioral**: "Given 3 line items priced at $1.10 each: verify the order total is $3.30 (summed as integer cents 110+110+110=330, then converted), not $3.30000000000000004 (summed as floating-point dollars)."

### Example 3: Permission Hierarchy

- **Structural**: "Function returns a value" / "No exceptions thrown"
- **Behavioral**: "Given an admin user accessing a member-only endpoint: verify the response is 200 (permission inherited). Given a guest user accessing the same endpoint: verify the response is 403."

### Example 4: Pagination Boundary

- **Structural**: "Pagination works" / "No type errors"
- **Behavioral**: "Given 25 items with pageSize=10: verify page 3 returns items 21-25 (5 items), page 2's last item does not repeat as page 3's first item, and page 4 returns an empty list."

---

## Anti-Patterns

These verify clauses provide no semantic protection. Do not use them as the sole criterion for Must-Have FR tasks:

- "test passes" — which test? what does it assert?
- "assertNotNull" — null-safety says nothing about correctness
- "works correctly" — unfalsifiable
- "compiles" — type-correct code can be semantically wrong
- "no errors" — absence of errors is not presence of correctness
- "runs successfully" — success at what?

---

## Derivation Heuristic

Use this sequence to derive behavioral verify clauses from a STEP's context:

1. **Read the intent block** — it names semantic risks (e.g., "off-by-one in pagination offset skips items")
2. **Supplement from design artifacts** — if intent alone is insufficient, check the STEP's linked Findings (F-N) and Decisions (AD-N) for additional risk signals. A Finding about existing retry behavior may reveal edge cases the intent doesn't name explicitly.
3. **Identify all risky conditions** — the specific inputs or states that trigger each semantic risk. Intent blocks often name multiple risks (e.g., both "correct offset calculation" and "graceful error on out-of-bounds page"). List each one.
3b. **Select verification level** (Tetris Principle — test at the lowest effective level):

   For each risky condition, determine the lowest verification level that can meaningfully exercise it:

   - **Unit**: The condition involves a single function, algorithm, or data transformation with no external dependencies. Example: "pagination offset calculation returns correct range."
   - **Integration**: The condition crosses a component boundary — database query, API call, service interaction, middleware chain. Example: "API endpoint returns paginated results from the database."
   - **E2E**: The condition requires a full user flow across multiple components or services. Example: "user navigates from login through dashboard to paginated list."
   - **Inspection**: The condition can only be verified by checking state — file existence, config value, environment variable, deployment status. Example: "CI pipeline config includes the new test stage."

   Record the level on each verify clause. When the design's `test_capabilities` shows null at the selected level, check whether the design includes a recommendation for that gap. If it does, note the gap and reference the recommendation. If it does not, escalate to the next available level.
4. **Construct a verify clause for each risk** — set up the risky condition, execute the code path, and check the expected outcome:
   - **Level** (`level`): [unit | integration | e2e | inspection] (selected in step 3b)
   - **Given** (`condition_text`): [the risky condition] (e.g., "25 items, pageSize=10, requesting page 2")
   - **Action** (`action`): [the code path under test] (e.g., "call the paginated list endpoint")
   - **Outcome** (`expected_outcome`): [the correct result] (e.g., "returns items 11-20, no overlap with page 1")

Render each step-level verify clause in pipe-delimited format: `- Level: X | Given: Y | Action: Z | Outcome: W`. This is the canonical rendering for STEP-level clauses. Bundle-level verify clauses use the multi-line bulleted format defined in task-guide.md.

Every verify clause must have all four parts. When the intent names multiple risks, generate a verify clause for each — do not cherry-pick the most easily testable risk and skip the others.

---

## Graceful Degradation Without Intent

When a STEP has a structural intent (`N/A — structural step`), derive behavioral verify clauses from the implementation guidance bullets alone:

1. Read the implementation bullets for action verbs and domain nouns
2. Identify the most complex logic path described (the likeliest source of semantic error)
3. Construct a condition → action → outcome criterion targeting that path

The result will have reduced domain specificity (no named boundary conditions or risk signals), but it is still behavioral — it tests a specific condition and checks a specific outcome, not just "compiles" or "passes."

**Example**: Implementation bullet says "Handle error codes: 401 (invalid credentials), 403 (account locked)." Without intent, derive: "Given invalid credentials, the service returns 401. Given a locked account, the service returns 403 (not 401)." This is less specific than intent-derived criteria but still behavioral.
