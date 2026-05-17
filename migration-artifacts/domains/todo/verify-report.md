# Verify — todo

Scaled-down 10-dimension review for a 1.2K-LOC clean rewrite. CRITICAL = blocker.

| Dimension | Result | Notes |
|---|---|---|
| traceability | PASS | Every legacy operation in `discovery/SUMMARY.md` maps to a REST endpoint in `spec.md` and is implemented in `backend/app/tasks.py` + `backend/app/auth.py`. |
| completeness | PASS w/ documented gaps | CRUD + filter + auth migrated. Social OAuth and offline service-worker explicitly out of scope (charter). |
| code-quality | PASS | FastAPI deps + typed Pydantic schemas; SQLAlchemy 2.0 typed mappers; strict TS on frontend; no `any` in client code. |
| test-quality | PASS | `backend/tests/test_api.py` covers register, login, me, CRUD, filters, cross-user isolation, unauthorized. Run `pytest -q`. Frontend lacks unit tests (acceptable for demo). |
| regression | N/A | Clean rewrite, no production traffic. |
| security | PASS | Bcrypt password hashing; JWT HS256; per-user row-level isolation enforced in queries (`WHERE owner_id = current_user.id`); CORS restricted to configured origins; secrets via env. **TODO for prod:** rotate `SECRET_KEY`, use httpOnly cookie instead of localStorage for tokens, add rate limit on `/auth/*`. |
| performance | PASS | Index `ix_tasks_owner_completed` mirrors legacy `.indexOn: ["completed"]`. Single round-trip per operation. |
| observability | GAP (accepted) | No logging/metrics added beyond uvicorn default + Next.js default. Add structured logging + a /metrics endpoint before prod. |
| compliance | N/A | `COMPLIANCE_SCOPE = none`. |
| data-parity | N/A | No data migration (demo). Data model parity verified via mapping table in `design.md`. |

## Open follow-ups (non-blocking)

- Alembic migrations (currently `create_all` on startup).
- httpOnly cookie auth via Next.js Route Handlers.
- Add OAuth providers (Google/GitHub) to restore the legacy social-sign-in surface.
- Frontend unit tests (Vitest + Testing Library) and an e2e smoke (Playwright).
- Structured logging + `/metrics`.

## Verdict

**PASS for v1.** Zero CRITICAL findings.
