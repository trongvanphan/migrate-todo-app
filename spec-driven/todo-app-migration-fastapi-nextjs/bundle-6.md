# Bundle B-6: Integration + Documentation

> Stage: integration | Parallel: no (depends on B-2 + B-5) | Files: todo-app-migrated/README.md, todo-app-migrated/backend/README.md, todo-app-migrated/frontend/README.md

**Bundle Verify**: Developer can start both servers from a clean checkout and complete sign-in → create task → filter → sign-out using only the documented steps.
- **Level**: inspection
- **Given**: Fresh clone of todo-app-migrated
- **Action**: Follow README startup instructions step by step
- **Outcome**: FastAPI on :8000; Next.js on :3000; no undocumented steps required

---

## Context

**Architecture Decisions:** AD-3 (Twitter/Facebook optional — include add-back instructions)

**Risks:** R-1 (Twitter OAuth 1.0a), R-2 (Facebook HTTPS — ngrok required)

---

## STEPs

### STEP-23: Integration documentation + startup guide
**Trace:** `MANUAL -> Integration verification` | **Effort:** S

**Files:**
- `todo-app-migrated/README.md` — create
- `todo-app-migrated/backend/README.md` — create
- `todo-app-migrated/frontend/README.md` — create

**Intent:** Startup sequence matters (FastAPI first). OAuth credential setup is the most common first-run blocker. `NEXTAUTH_SECRET` generation must be explicit (`openssl rand -base64 32`).

**Implementation guidance:**
1. Root README: monorepo overview, prerequisites (Python 3.11+, Node 18+), quick start pointing to sub-READMEs
2. `backend/README.md`: `pip install -r requirements.txt`, `.env` config (SECRET_KEY, DATABASE_URL, CORS_ORIGINS), `uvicorn app.main:app --reload --port 8000`, `pytest tests/`
3. `frontend/README.md`: `npm install`, `.env.local` from example, Google Cloud Console OAuth setup, GitHub OAuth App setup, `NEXTAUTH_SECRET=\`openssl rand -base64 32\``, `npm run dev`, `npm test`
4. Optional providers: Twitter OAuth 1.0a note, Facebook HTTPS + ngrok note with links
5. Verify section: `curl http://localhost:8000/ → {"status": "ok"}`

**Verify:**
- Level: inspection | Given: README.md | Action: read startup section | Outcome: Google OAuth steps present; NEXTAUTH_SECRET generation command present; startup order (backend first) documented

**Dependencies:** Depends on B-2 + B-5 complete
