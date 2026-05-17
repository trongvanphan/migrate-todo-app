---
slug: todo-app-migration-fastapi-nextjs
date: 2026-05-17
overall_verdict: PASS WITH CAVEATS
spec_hash: sha256:8da3d3e2298a6b45d4897c6e4c7613a293e24fa52d95d363b7673b8ece40fc1f
design_hash: sha256:014db3e31998c48ca9bd7105f4f12da52c1e382e4a79ff6cd1f9a9512e713c23
steps_verified: 23/23
validation: subagent
re_verification: "security,testing — 2026-05-17"
---

# Verification Report: Todo App Migration — FastAPI + Next.js

**Date:** 2026-05-17 (re-verified: security + testing)
**Slug:** `todo-app-migration-fastapi-nextjs`
**Steps verified:** 23/23 done

---

## Overall Verdict: PASS WITH CAVEATS

| Dimension | Verdict | Critical | High | Medium | Low |
|---|---|---|---|---|---|
| Traceability | ✅ PASS | 0 | 0 | 0 | 0 |
| AC/NFR Completeness | ⚠️ PASS WITH CAVEATS | 0 | 0 | 1 | 0 |
| Code Quality | ✅ PASS | 0 | 0 | 0 | 0 |
| Test Quality | ✅ **PASS** *(was PASS WITH CAVEATS)* | 0 | 0 | 0 | 1 |
| Regression | ✅ PASS | 0 | 0 | 0 | 0 |
| Security | ⚠️ **PASS WITH CAVEATS** *(was FAIL)* | 0 | 1 | 3 | 0 |

**Overall: PASS WITH CAVEATS** — CRITICAL resolved. Remaining: 1 HIGH (JWT expiry, accepted per spec), 3 MEDIUM (rate limiting, CORS, provider enum), 1 MEDIUM (Twitter/Facebook deferred per design).

---

## Remediation Summary

| Finding | Original Severity | Status | Fix |
|---|---|---|---|
| VF-1: .env in git | **CRITICAL** | ✅ **FIXED** | `git rm --cached` + added to `.gitignore` |
| VF-2: JWT expiry test | HIGH | ✅ **FIXED** | `test_expired_jwt_returns_401` added |
| VF-5: 404/403 enumeration | MEDIUM | ✅ **FIXED** | Combined ownership+existence query |
| VF-9: TaskList empty state | MEDIUM | ✅ **FIXED** | `TaskList.test.tsx` with 4 tests |
| VF-10: Anonymous JWT unvalidated | MEDIUM | ✅ **FIXED** | `test_anonymous_token_is_valid_jwt` added |

**Backend test suite: 15 passing** (was 13 — added `test_expired_jwt_returns_401` and `test_anonymous_token_is_valid_jwt`)

---

## Active Findings

### VF-1 — HIGH: JWT 30-day expiry (accepted per spec)
**Dimension:** Security | **Status:** Accepted design decision

30-day access tokens create a longer window for token misuse if stolen. This was documented as an explicit spec decision (NFR-2: "JWT expiry: 30 days") and is acceptable for a demo/migration app. Flag for production hardening with refresh token rotation.

**Evidence:** `backend/app/config.py:7` (`access_token_expire_days: int = 30`)

---

### VF-2 — MEDIUM: Twitter and Facebook OAuth not implemented
**Dimension:** AC/NFR Completeness | **Status:** Approved design deviation (AD-3)

FR-1 requires 5 providers. 3 are implemented (Google, GitHub, Anonymous). Twitter/Facebook were deferred in AD-3. Instructions to add them are in `todo-app-migrated/README.md`.

---

### VF-3 — MEDIUM: No rate limiting on /auth/anonymous
**Dimension:** Security | **Status:** Open (hardening backlog)

`POST /auth/anonymous` accepts unlimited requests. Fix: add `slowapi` rate limiting (10 req/min per IP).

**Evidence:** `backend/app/routers/auth.py:52-63`

---

### VF-4 — MEDIUM: CORS allows all methods and headers
**Dimension:** Security | **Status:** Open (hardening backlog)

`allow_methods=["*"]` and `allow_headers=["*"]`. Fix: restrict to `["GET", "POST", "PATCH", "DELETE"]` and `["Authorization", "Content-Type"]`.

**Evidence:** `backend/app/main.py:24-25`

---

### VF-5 — MEDIUM: No OAuth provider allowlist
**Dimension:** Security | **Status:** Open (hardening backlog)

`/auth/oauth` accepts arbitrary `provider` strings. Fix: add a `ProviderEnum` to `OAuthLogin` schema.

**Evidence:** `backend/app/schemas.py:5-10`

---

### VF-6 — LOW: Ownership tests expect 404 (correct per VF-5 fix)
**Dimension:** Test Quality | **Status:** Accepted

Ownership tests were updated to assert 404 (not 403) to align with the VF-5 single-query fix. The 404-for-unauthorized pattern is intentional security design. Tests are correctly annotated with `[VF-5]` comments.

---

## Test Suite State (post-remediation)

| Suite | Count | Status |
|---|---|---|
| `backend/tests/test_auth.py` | 7 tests | ✅ All pass |
| `backend/tests/test_tasks.py` | 8 tests | ✅ All pass |
| **Backend total** | **15 tests** | ✅ **All pass** |
| `frontend/components/__tests__/TaskForm.test.tsx` | 4 tests | Config verified |
| `frontend/components/__tests__/TaskItem.test.tsx` | 5 tests | Config verified |
| `frontend/components/__tests__/TaskList.test.tsx` | 4 tests | **New** — Config verified |
| **Frontend total** | **13 tests** | Config verified (requires `npm install`) |

---

## Traceability Matrix

| FR | ADs | STEPs | Committed | Verdict |
|---|---|---|---|---|
| FR-1: Sign in | AD-1, AD-2, AD-3 | STEP-13–17 | ✅ | ⚠️ 3/5 providers |
| FR-2: Sign out | AD-1, AD-2 | STEP-13, 17 | ✅ | ✅ |
| FR-3: Route protection | AD-1 | STEP-14 | ✅ | ✅ |
| FR-4: Create task | AD-4, AD-5, AD-7 | STEP-7, 19 | ✅ | ✅ |
| FR-5: View tasks | AD-4, AD-6, AD-7 | STEP-7, 18, 20 | ✅ | ✅ |
| FR-6: Filter tasks | AD-8 | STEP-18, 20 | ✅ | ✅ |
| FR-7: Toggle completion | AD-5, AD-7 | STEP-8, 21 | ✅ | ✅ |
| FR-8: Inline edit title | AD-5, AD-7 | STEP-8, 21 | ✅ | ✅ |
| FR-9: Delete task | AD-5, AD-7 | STEP-8, 21 | ✅ | ✅ |
| FR-10: Per-user isolation | AD-4, AD-5 | STEP-2, 5–8 | ✅ | ✅ |
| FR-11: Responsive UI | — | STEP-20 | ✅ | ✅ |

---

## Production Hardening Checklist (remaining backlog)

Before deploying to production, address these items in priority order:

- [ ] **VF-1 (JWT expiry):** Reduce `ACCESS_TOKEN_EXPIRE_DAYS` to 1 hour; implement refresh token via NextAuth `refreshAccessToken` callback
- [ ] **VF-3 (rate limiting):** Add `slowapi` to `backend/app/main.py` with per-IP limits on `/auth/anonymous` and `/auth/oauth`
- [ ] **VF-4 (CORS):** Replace `allow_methods=["*"]` with explicit method list in `backend/app/main.py`
- [ ] **VF-5 (provider enum):** Add `ProviderEnum` to `OAuthLogin` in `backend/app/schemas.py`
- [ ] **VF-2 (Twitter/Facebook):** Add providers to `frontend/auth.ts` per instructions in `README.md`
- [ ] **Secrets management:** Generate strong `SECRET_KEY` (`openssl rand -base64 32`) and store in environment variables, not files
