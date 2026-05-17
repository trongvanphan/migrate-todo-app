# Junior Dev Prompts — Large App Migration (with Discovery)

Use these prompts when migrating a large legacy app (100K+ LOC).
For small apps, use `junior-prompts.md` instead.

Run each prompt in order. Each one is self-contained — Claude will not ask questions.

---

## Prompt 0 — Discovery

Run this first, before writing any spec. Point it at your legacy codebase.

```
Perform a systematic discovery analysis of the legacy codebase at [PATH_TO_LEGACY_APP].
Produce all five discovery artifacts below. Do not write any spec, design, or code yet —
discovery only.

Output directory: discovery/

---

ARTIFACT 1 — code-map.md
Analyze the codebase structure:
- Count LOC per top-level module/package (use find + wc -l)
- Identify external system integrations (grep for database clients, HTTP clients,
  message queue clients, third-party SDK imports)
- Identify high-churn files: git log --format=format: --name-only | sort | uniq -c | sort -rn | head 50
- List all environment variables or config keys referenced in code
- Draw a text dependency diagram showing which modules import which
Format: markdown table + ASCII diagram

---

ARTIFACT 2 — api-routes.md
Enumerate every API endpoint in the codebase:
- Grep for route definitions appropriate to the framework
  (e.g. @GetMapping, router.get, @app.get, path(, urlpatterns, etc.)
- Group by domain/prefix (e.g. /auth/*, /orders/*, /users/*)
- For each route: method, path, handler file+line, brief description inferred from code
- Flag any routes that appear undocumented (no comments, unusual naming)
Format: grouped markdown table

---

ARTIFACT 3 — db-schema.md
Extract the full database schema:
- Find all ORM models, migration files, or SQL schema files
- For each table: columns, types, constraints, indexes, foreign keys
- Draw entity-relationship text diagram for tables with FK relationships
- Identify state machine columns (status, state, type enums) — list all possible values
- Flag tables with high FK fan-out (many things depend on them)
Format: markdown table per table + ASCII ER diagram

---

ARTIFACT 4 — test-as-spec.md
Extract requirements from the existing test suite:
- Find all test files (*.spec.ts, *.test.ts, *_test.py, *Test.java, *Spec.rb, etc.)
- Extract every test name/description
- Convert each test name to an implied requirement:
  "should reject empty title" → AC: Given empty input, When submitted, Then rejected with error
- Group by domain (auth, orders, catalog, etc.)
- Flag test names that reveal non-obvious business rules (time limits, permission checks,
  state transition guards, rate limits, validation edge cases)
Format: grouped markdown, original test name + implied AC

---

ARTIFACT 5 — git-log-findings.md
Mine git history for hidden requirements:
- Run: git log --oneline --all | grep -iE "fix|bug|edge|case|handle|when|should|must|cannot|prevent|validate|restrict|limit|expire" | head 200
- For each relevant commit: hash, message, implied requirement
- Group by domain
- Flag commits that reveal: time-based rules, rate limits, ownership checks,
  state guards, validation edge cases, permission boundaries
Format: grouped markdown table

---

SUMMARY SECTION in code-map.md:
After all five artifacts, add a "Feature Coverage Estimate" section:
- Estimated number of distinct features found
- Estimated number of FRs this will produce
- Top 3 domains by LOC
- Top 3 domains by API route count
- Recommended migration order (leaf domains first)
- Any surprises or red flags found during discovery

Do not stop to ask questions. If a file or directory cannot be found, note it and continue.
```

---

## Prompt 0.5 — Domain Decomposition

Run after Prompt 0. Feed it the discovery artifacts.

```
Using the discovery artifacts in discovery/, decompose the legacy codebase into
independently migratable domains. Do not write any spec or code yet.

Output: discovery/domain-map.md

---

STEP 1 — Identify bounded contexts
Based on api-routes.md and db-schema.md:
- Group related routes + tables into candidate domains
- A domain is a set of routes + tables that are cohesive in purpose and
  have minimal dependencies on other groups
- Name each domain using business language (not technical: "Auth" not "UserServiceModule")
- List the routes and tables that belong to each domain

---

STEP 2 — Draw the context map
For each domain, identify:
- Inbound contracts: endpoints this domain exposes that OTHER domains call
- Outbound calls: endpoints/data this domain reads from OTHER domains
- Shared tables (if any): tables accessed by more than one domain — flag these as risks

Draw an ASCII context map:
- Box per domain
- Arrows showing dependencies (Domain A → Domain B means A calls B)
- Label arrows with the contract (e.g. "GET /auth/me")

---

STEP 3 — Determine migration order
Rules:
1. Domains with no outbound dependencies → migrate first
2. Domains that others depend on → migrate before those dependents
3. Auth domain → always migrate early (everything depends on it)
4. Payments/financial domains → migrate last (highest risk)

Output a numbered migration order with justification for each position.

---

STEP 4 — Risk assessment per domain
For each domain, rate:
- Size: LOC + route count
- Coupling: number of inbound + outbound contracts
- Churn: from git-log-findings.md — high churn = more hidden behavior
- Criticality: what breaks if this domain has a bug (low/medium/high/critical)

Format: markdown table with columns: Domain | Size | Coupling | Churn | Criticality | Migration Order

---

STEP 5 — Strangler Fig plan
For each domain in migration order, define:
- What feature flag / routing key will control traffic split
- What the rollback mechanism is (feature flag off → legacy)
- What % traffic ramp schedule looks like (1% → 10% → 50% → 99% → 100%)
- What API diff check confirms behavioral parity before each ramp step

Do not ask questions. Use the discovery artifacts to make decisions.
```

---

## Prompt 1 — Spec (per domain)

Run once per domain. Replace {DOMAIN} and {DOMAIN_PATH}.

```
Write a specification for the {DOMAIN} domain of the legacy app migration.

Source artifacts:
- Discovery: discovery/
- Domain map: discovery/domain-map.md
- Legacy code: [PATH_TO_LEGACY_APP]/{DOMAIN_PATH}

Output: spec-driven/{DOMAIN}/spec.md

---

Use the SDS spec format with these pre-answered decisions:
- Do not ask elicitation questions — write the spec directly using discovery artifacts
- FR hierarchy: Epic → Feature → Story (not a flat list)
- ACs in Given/When/Then format
- Include edge cases found in test-as-spec.md and git-log-findings.md
- Include state machine FRs for any status/state enum columns found in db-schema.md
- Include authorization FRs for any ownership or role checks found in tests or git log

Required sections:
1. Functional Requirements (hierarchical: EP → FR → AC)
2. Non-Functional Requirements
3. Out of Scope (what is explicitly NOT being migrated in this domain)
4. Inbound contracts this domain must honor (from domain-map.md)
5. Outbound contracts this domain calls (from domain-map.md)
6. Data model: target schema for this domain's tables
7. API surface: every endpoint this domain will expose

Coverage check before finishing:
- Every route in api-routes.md for this domain → at least one FR
- Every table in db-schema.md for this domain → at least one FR
- Every non-obvious AC in test-as-spec.md for this domain → explicitly included
- Every time-based, rate-limit, or ownership rule in git-log-findings.md → included

Do not ask questions. Make decisions based on the discovery artifacts.
If something is ambiguous, note it as an OPEN QUESTION at the end of the spec
but still write a best-guess FR for it so execution can proceed.
```

---

## Prompt 2 — Design (per domain)

Run after Prompt 1 for each domain.

```
Create an architectural design for the {DOMAIN} domain.

Input: spec-driven/{DOMAIN}/spec.md
Output: spec-driven/{DOMAIN}/design.md

---

Pre-made technology decisions (do not research alternatives):
[PASTE YOUR TECH STACK DECISIONS HERE — e.g.]
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Frontend: Next.js 14 + NextAuth v5 + TanStack Query v5
- Auth: JWT with 30-day expiry
- API style: REST with JSON
- Test strategy: pytest (backend), jest + next/jest (frontend)

Critical design rules:
1. Document INBOUND contracts first — endpoints other domains call from this domain.
   These must not change signature. If a change is needed, version the endpoint.
2. Document OUTBOUND calls — what this domain calls from other domains.
   These must match what those domains expose (verified against their design.md).
3. For state machine columns: document all valid transitions and what rejects invalid ones.
4. For ownership checks: document the combined-filter pattern
   (never sequential existence-check → authorization-check, always one query → 404).

Required sections:
1. Architecture Decisions (AD-1...AD-N) with Context/Decision/Rationale
2. Contract Registry:
   - Inbound contracts (what I expose to other domains)
   - Outbound contracts (what I call from other domains)
3. File inventory (every file to be created, mapped to FRs)
4. Data model changes from legacy (schema diff)
5. State machines (if any status columns exist)
6. Security model (ownership, roles, what returns 404 vs 403)

Do not ask questions. Use the spec and tech decisions above.
```

---

## Prompt 3 — Tasks (per domain)

Run after Prompt 2 for each domain.

```
Decompose the {DOMAIN} domain design into executable implementation steps.

Input:
- spec-driven/{DOMAIN}/spec.md
- spec-driven/{DOMAIN}/design.md

Output:
- spec-driven/{DOMAIN}/tasks.md
- spec-driven/{DOMAIN}/bundle-*.md (one file per bundle)

---

Use the SDS task format with:
- Strategy: Walking Skeleton
- Bundle pattern: infrastructure first → API endpoints → UI → tests → integration
- Each STEP must include: trace (FR→AC), intent, implementation guidance, verify clause
- Test strategy: test-after (dedicated test STEP at end of each backend and frontend bundle)

Contract compliance rule:
For every inbound contract listed in design.md, there must be a STEP that:
1. Implements the endpoint
2. Has a verify clause confirming the contract signature is met exactly

Do not ask questions. Generate all bundles end-to-end.
```

---

## Prompt 4 — Execute (per domain)

Run after Prompt 3. This writes the actual code.

```
Execute the implementation plan for the {DOMAIN} domain.

Input:
- spec-driven/{DOMAIN}/tasks.md
- spec-driven/{DOMAIN}/bundle-*.md

Output code directory: [YOUR_OUTPUT_PATH]/{domain}/

---

Execute all bundles in order. Do not stop between bundles.
Commit after each bundle: git commit -m "[DOMAIN][STEP-N] description"

Critical implementation rules:
1. Ownership checks: single combined filter(resource.id == id, resource.owner_id == current_user.id)
   → always 404, never 403 (prevents resource enumeration)
2. JWT exchange (if NextAuth): in jwt() callback with trigger === 'signIn' && account guard
3. Jest config: use next/jest (SWC) — do NOT create .babelrc
4. Inbound contracts: implement EXACTLY as specified in design.md — no signature changes
5. State machine: reject invalid transitions at the service layer, not just the DB constraint
6. Never commit .env files — add to .gitignore before first commit

After all bundles complete:
- Run all tests and report counts
- Run TypeScript check (if applicable): npx tsc --noEmit
- Run production build (if applicable): npm run build
- Report any failures with root cause

Do not ask questions. Fix any compilation or test errors automatically.
```

---

## Prompt 5 — Verify (per domain)

Run after Prompt 4.

```
Verify the {DOMAIN} domain implementation against its specification.

Input:
- spec-driven/{DOMAIN}/spec.md
- spec-driven/{DOMAIN}/design.md
- spec-driven/{DOMAIN}/tasks.md
- Implemented code at [YOUR_OUTPUT_PATH]/{domain}/

Output: spec-driven/{DOMAIN}/verify-report.md

---

Run all 6 verification dimensions in parallel:

1. TRACEABILITY — every FR → at least one STEP → at least one commit
2. COMPLETENESS — every inbound contract in design.md is implemented with correct signature
3. CODE QUALITY — no obvious code smells, no commented-out code, no TODO in production paths
4. TEST QUALITY — every state machine transition tested, ownership tested,
   validation edge cases tested, JWT expiry tested
5. REGRESSION — all tests pass, build succeeds, TypeScript 0 errors
6. SECURITY — .env not in git, no 403 where 404 is correct, no secrets hardcoded,
   input validation at boundaries, no SQL injection vectors

For any CRITICAL or HIGH finding: fix it automatically without asking.
Re-verify the fixed dimension after fixing.

Final output: verify-report.md with overall verdict (PASS / PASS WITH CAVEATS / FAIL).
```

---

## Prompt 6 — API Diff Setup

Run this once after all domains are deployed alongside the legacy system.

```
Set up API diff testing to verify behavioral parity between the legacy system and
the new system.

Legacy system base URL: [LEGACY_URL]
New system base URL: [NEW_URL]
Output: tools/api-diff/

---

Create a test harness that:
1. Takes a list of API calls (method, path, headers, body)
2. Sends each call to BOTH legacy and new system
3. Compares responses:
   - Status code must match
   - Response body: compare semantically (ignore field ordering, ignore generated IDs,
     ignore timestamps, compare structure and business values)
4. Reports diffs as: MATCH | BODY_DIFF | STATUS_DIFF | ERROR
5. Saves a diff report to api-diff-report.json

Create a seed request file api-diff-requests.json with test cases covering:
- One request per endpoint in api-routes.md
- Happy path + at least one error case per endpoint
- Authenticated requests (include a test JWT in headers)
- Filtered/paginated list requests

The harness should be runnable as:
  node tools/api-diff/run.js

Do not ask questions. Generate the harness and seed requests end-to-end.
```

---

## Execution Order Summary

```
For each legacy app being migrated:

  Prompt 0      →  Discovery (run once for the whole app)
  Prompt 0.5    →  Domain decomposition (run once)

  Then for each domain in migration order:
  Prompt 1      →  Spec
  Prompt 2      →  Design
  Prompt 3      →  Tasks
  Prompt 4      →  Execute
  Prompt 5      →  Verify

  After all domains:
  Prompt 6      →  API diff setup (run once)

Total prompts for N domains: 2 + (5 × N) + 1
Example: 4 domains = 2 + 20 + 1 = 23 prompts
```

---

## When to Run Domains in Parallel

If you have multiple developers or multiple Claude Code sessions:

```
Session 1: Prompt 0 → Prompt 0.5 (shared, run first)

Then in parallel:
  Session 2: Domain A — Prompts 1→5
  Session 3: Domain B — Prompts 1→5   ← only if B does not depend on A
  Session 4: Domain C — Prompts 1→5   ← only if C does not depend on A or B

Wait for all parallel sessions to complete Prompt 5 before running Prompt 6.
```

Never run a domain's Prompt 4 (execute) before the domains it depends on have
completed Prompt 5 (verify). Dependency order from Prompt 0.5 is mandatory.
