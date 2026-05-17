---
title: "Tasks: [Feature Name]"
slug: [spec-slug]
status: draft
design_source: spec-driven/[spec-slug]/design.md
design_hash: sha256:[hash]
spec_source: spec-driven/[spec-slug]/spec.md
spec_hash: sha256:[hash]
strategy: [walking-skeleton | max-parallelism | dependency-first]
total_steps: [N]
total_slices: [N]
total_bundles: [N]
validation: [subagent | fallback | skipped]
version: 2.0
date: [ISO date]
# Multi-project workspace support (optional — omit for single-project):
# projects:
#   - name: auth-service
#     identity: ghe.coxautoinc.com/org/auth-service
#   - name: client-sdk
#     identity: ghe.coxautoinc.com/org/client-sdk
# artifact_home: auth-service
---

# Tasks: [Feature Name]

> Design: [design source] | Spec: [spec source] | Strategy: [strategy] | Generated: [date] | Status: Draft

> Do not edit this document after finalization. Track execution in `spec-driven/<slug>/progress-bundle-N.md` files.

## Traceability

### Functional Requirements

| FR | AC | STEP | Slice | Bundle |
|----|-----|------|-------|--------|
| FR-1 | AC-1.1, AC-1.2 | STEP-1, STEP-2 | Slice 1 | Bundle 1 |
| FR-2 | AC-2.1 | STEP-3, STEP-4 | Slice 1 | Bundle 1, Bundle 2 |
| FR-3 | AC-3.1, AC-3.2 | STEP-5, STEP-6 | Slice 2 | Bundle 2 |
| — | — | STEP-7 | Slice 3 | Bundle 3 |

> STEP-7 uses MANUAL trace — see step definition for rationale.

### Non-Functional Requirements

| NFR | Disposition | STEP / Mechanism | Verification |
|-----|------------ |------------------|-------------|
| NFR-1 | Implemented | STEP-4 | Verify clause on STEP-4 checks response time |
| NFR-2 | Platform | Inherited via API Gateway timeout configuration | Manual: confirm timeout setting in deployment config |
| NFR-3 | Deferred | Out of scope for this iteration | — |

> **Disposition values**: `Implemented` (a STEP enforces it), `Platform` (inherited from infrastructure — cite the mechanism), `Deferred` (explicitly out of scope — state justification). An NFR with no row in this table is a gap, not a delegation.

<!-- ═══ tasks.md template ends here ═══ -->
<!-- ═══ bundle-N.md template begins below ═══ -->
<!-- In the output, STEP entries live in bundle-N.md files, NOT in tasks.md. -->
<!-- tasks.md contains only: frontmatter, traceability table, bundle headers (no STEPs), -->
<!-- conflict analysis, architecture decisions, and file structure description. -->

---

## Slice 1: Walking Skeleton (Stage: skeleton)

> Proves the architecture end-to-end with minimal implementation.

### Bundle 1: Foundation
> Stage: skeleton | Parallel: no | Files: src/services/auth.ts, src/routes/index.ts

<!-- Bundle-level verify uses multi-line bulleted format (Level/Given/Action/Outcome on separate lines) -->
**Bundle Verify**: The auth skeleton responds to requests end-to-end.
- **Level**: integration
- **Given**: Application server running with skeleton routes registered
- **Action**: Send GET request to /api/auth
- **Outcome**: Returns HTTP response (not connection refused) — route is wired

> **Context**
>
> **Applicable ACs**
> - **AC-1.1**: Given: Valid user credentials / When: User submits login form / Then: System returns a signed JWT access token
> - **AC-1.2**: Given: Auth service running / When: Auth routes are registered / Then: /api/auth endpoint responds (not connection refused)
>
> **Architecture Decisions**
> - **AD-2: Short-lived JWTs with opaque refresh tokens** — Decision: Access tokens expire in 15 minutes; refresh tokens are opaque server-side references. Rationale: F-3 confirms existing 15-minute expiry pattern; longer expiry breaks revocation model since JWTs cannot be individually invalidated.
>
> **Findings**
> - **F-3: Existing auth uses JWT with 15-minute expiry** — Token generation must match this pattern; a longer expiry breaks the security model.
>
> **Standards**
> - **S-1**: Use parameterized configuration from environment variables, not hardcoded values (Domain: security | File Type: .ts)
> - **S-3**: Use functional components with hooks, not class components (Domain: style | File Type: .tsx)
>
> **Constraints**
> - Must use existing JWT_SECRET from environment, not hardcoded values (Category: security | Source: codebase)

#### STEP-1: Create AuthService skeleton
[FR-1 -> AC-1.1] | create `src/services/auth.ts` | Effort: S

> **Intent**: Access token generation must use the existing JWT secret from env, not a hardcoded value. A hardcoded secret passes all tests but breaks in production where the env var is rotated monthly.
> **Standards**: S-1 (parameterized config), S-3 (functional components)
<!-- Omit Intent if structural (use "N/A — structural step"). Omit Standards if none match. -->

- Create `AuthService` class with `login()` and `logout()` method stubs
- Export typed interfaces `AuthRequest` and `AuthResponse`
- Follow pattern from `src/services/user.ts`

<!-- STEP-level verify uses pipe-delimited format: Level: X | Given: Y | Action: Z | Outcome: W -->
**Verify**:
- Level: unit | Given: JWT_SECRET env var set to "test-secret" | Action: call `AuthService.login()` with valid credentials | Outcome: returned token decodes with "test-secret", not any hardcoded value

> Depends on: — | Enables: STEP-2, STEP-3 | Parallel with: —

#### STEP-2: Mount auth routes
[FR-1 -> AC-1.2] | modify `src/routes/index.ts` | Effort: XS

> **Intent**: N/A — structural step

- Import `AuthService` from `src/services/auth.ts`
- Mount auth router at `/api/auth`

**Verify**:
- Level: integration | Given: server started | Action: `GET /api/auth` | Outcome: returns 404 (no handler yet) rather than connection refused (route exists)

> Depends on: STEP-1 | Enables: STEP-4 | Parallel with: —

---

## Slice 2: Core Implementation (Stage: depth)

> Fleshes out the business logic for each feature area.

### Bundle 2: Auth Logic
> Stage: depth | Parallel: yes (file-disjoint) | Files: src/services/auth.ts, src/middleware/auth.ts, src/models/token.ts
<!-- Multi-project: use project-qualified paths — e.g., auth-service::src/services/auth.ts -->

**Bundle Verify**: The auth business logic produces correct output for representative inputs.
- **Level**: unit
- **Given**: AuthService instantiated with test JWT secret
- **Action**: Call login() with valid credentials, then call logout() with returned token
- **Outcome**: Login returns valid JWT; after logout, token is revoked (isRevoked returns true)

<!-- Context preamble for this bundle scoped to its STEPs — see Bundle 1 for full example -->

#### STEP-3: Implement login and logout logic
[FR-1 -> AC-1.1, AC-1.3] | modify `src/services/auth.ts` | Effort: M

> **Intent**: Login must use bcrypt comparison, not plaintext. The existing user table stores bcrypt hashes — a plaintext comparison will always fail, producing a confusing "invalid credentials" error on valid passwords.

- Implement `login()` with bcrypt password comparison and JWT token generation
- Implement `logout()` with token invalidation via deny-list
- Handle error codes: 401 (invalid credentials), 403 (account locked), 500 (server error)
- Follow error-handling pattern from `src/services/user.ts`

**Verify**:
- Level: unit | Given: user with bcrypt-hashed password in DB | Action: call `login()` with correct plaintext password | Outcome: returns valid JWT (not 401)
- Level: unit | Given: locked account | Action: call `login()` | Outcome: returns 403 (not 401)

> Depends on: STEP-1 | Enables: STEP-6 | Parallel with: STEP-4, STEP-5

#### STEP-4: Add JWT validation middleware
[FR-2 -> AC-2.1] | create `src/middleware/auth.ts` | Effort: S

> **Intent**: Token validation must check expiry AND signature. Checking only the signature allows expired tokens through — the 15-minute expiry window is a security boundary.

- Create `requireAuth` middleware that validates Bearer tokens from `Authorization` header
- Attach decoded payload to `req.user`
- Return 401 for missing tokens, 403 for expired or invalid tokens
- Follow pattern from `src/middleware/rateLimit.ts`

**Verify**:
- Level: integration | Given: expired JWT (created 16 minutes ago) | Action: request with Bearer token | Outcome: 403 response (not 200)
- Level: integration | Given: valid JWT | Action: request with Bearer token | Outcome: 200, `req.user` populated

> Depends on: STEP-1 | Enables: STEP-6 | Parallel with: STEP-3, STEP-5

#### STEP-5: Create token model
[FR-2 -> AC-2.1] | create `src/models/token.ts` | Effort: XS

> **Intent**: N/A — structural step

- Define `TokenRecord` interface with `jti`, `userId`, `expiresAt`, `revokedAt` fields
- Export `TokenStore` class with `revoke()` and `isRevoked()` methods (in-memory for now)

**Verify**:
- Level: unit | Given: token revoked via `revoke(jti)` | Action: call `isRevoked(jti)` | Outcome: returns true

> Depends on: — | Enables: STEP-3 | Parallel with: STEP-3, STEP-4

---

## Slice 3: Integration (Stage: integration)

> Wires components together and runs end-to-end verification.

### Bundle 3: Wire and Verify
> Stage: integration | Parallel: no | Files: src/routes/auth.ts, src/routes/index.ts

<!-- Bundle-level verify uses multi-line bulleted format (Level/Given/Action/Outcome on separate lines) -->
**Bundle Verify**: The full auth flow works end-to-end across all wired components.
- **Level**: integration
- **Given**: Application server running with auth service, middleware, and routes wired
- **Action**: POST /login with valid credentials, then GET /protected with returned token
- **Outcome**: Login returns JWT, protected endpoint returns 200 with user context

#### STEP-6: Wire auth routes to service and middleware
[FR-3 -> AC-3.1] | create `src/routes/auth.ts` | Effort: S

> **Intent**: The login endpoint must validate the request body before calling AuthService — passing raw user input to bcrypt.compare with a missing password field causes an unhandled TypeError, not a 400 response.

- Implement `POST /login` handler: validate body, call `AuthService.login()`, return token
- Implement `POST /logout` handler: call `AuthService.logout()`, return 204
- Apply `requireAuth` middleware to protected routes
- Follow pattern from `src/routes/user.ts`

**Verify**:
- Level: integration | Given: POST /login with empty body | Action: send request | Outcome: 400 response with validation message (not 500 TypeError)
- Level: integration | Given: POST /login with valid credentials | Action: send request | Outcome: 200 with JWT in response body

> Depends on: STEP-3, STEP-4 | Enables: STEP-7 | Parallel with: —

#### STEP-7: Full integration test
MANUAL -> End-to-end verification across all auth components

> **Intent**: The test suite must exercise the full auth flow (register -> login -> access protected resource -> logout -> verify token rejected) as a single integration test. Unit tests on individual components miss interaction bugs at the middleware/route/service boundaries.

- Run full test suite, verify zero regressions
- Run type-check across all modified files

**Verify**:
- Level: integration | Given: clean database | Action: run full auth integration test | Outcome: all assertions pass, including post-logout token rejection

> Depends on: STEP-6 | Enables: — | Parallel with: —

<!-- ═══ bundle-N.md template ends here ═══ -->
<!-- ═══ Shared reference sections below (apply to both tasks.md and bundle-N.md) ═══ -->

---

## Conflict Analysis

> Note: Covers explicitly declared file paths only. Implicit touches (barrel files, shared configs, type re-exports) may require manual sequencing during execution.

| Hot File | Touched By | Strategy |
|----------|------------|----------|
| src/routes/index.ts | STEP-2 (Bundle 1), STEP-6 (Bundle 3) | Sequential (Bundle 1 before Bundle 3) |
| src/services/auth.ts | STEP-1 (Bundle 1), STEP-3 (Bundle 2) | Sequential (Bundle 1 before Bundle 2) |

---

## Architecture Decisions

See: spec-driven/[spec-slug]/design.md

---

## File Structure

`tasks.md` is always an index-only document (bundle headers only, no STEP entries). All STEP detail lives in the bundle files:

    spec-driven/<slug>/tasks.md       — Index file: frontmatter, traceability, conflict analysis,
                                        architecture decisions, and bundle list (headers only)
    spec-driven/<slug>/bundle-1.md    — All STEP entries for Bundle 1 (self-contained)
    spec-driven/<slug>/bundle-2.md    — All STEP entries for Bundle 2 (self-contained)
    ...

The index file is the orchestration document. Each bundle file is a self-contained execution
unit designed to be loaded into a single agent context without the rest of the document.
Bundle files include their own bundle header and all STEP entries for that bundle only.

---

## Progress Tracker (Bundle-Specific)

Progress is always tracked per-bundle. Each bundle gets its own progress file:

    spec-driven/<slug>/progress-bundle-1.md
    spec-driven/<slug>/progress-bundle-2.md
    ...

See [task-guide.md](../references/task-guide.md) for the progress tracker format, session log template,
and consolidation rules for agent/team modes.

### progress-bundle-N.md Template

```markdown
# Progress: Bundle N — [Bundle Name]

> Tasks: spec-driven/[slug]/tasks.md | Bundle: N | Started: [date] | Last Updated: [date]

Progress: 0/[M] steps complete

## Current State

- Stage: [skeleton | depth | integration]
- Last completed: STEP-N — [brief title], or — (not started)
- Next up: STEP-N — [brief title]
- Blockers: [none | description]

## Step Status

| Step | Status | Commit | Notes |
|------|--------|--------|-------|
| STEP-1 | pending | — | — |
| STEP-2 | pending | — | — |

## Session Log

### [date] — [context]
- Completed: [step IDs and brief titles, or "none"]
- Decisions: [any decisions made, or "none"]
- Next: STEP-N: [brief title]
```

**Status values**: `pending`, `in-progress`, `done`, `blocked`.
**Commit column**: Populated by the executor with git commit short hash after each step completes.
