# Working Journal — Todo App Migration (Angular Firebase → FastAPI + Next.js)

**Date:** 2026-05-17  
**Model:** Claude Sonnet 4.6 (1M context)  
**Repo:** `migrate-todo-app/` → output in `todo-app-migrated/`

---

## What We Did, Start to Finish

---

### Phase 0 — Project Orientation (CLAUDE.md initialization)

**Trigger:** `/init` and `/init for 'todo-angular-firebase-demo'`

We started by analyzing the existing codebase to understand what we were migrating *from*. Two CLAUDE.md files were created:

**Root CLAUDE.md** (`/migrate-todo-app/CLAUDE.md`):
- Established the repo purpose: `todo-angular-firebase-demo/` = source (Angular 4 + Firebase), `todo-app-migrated/` = migration target (empty at the time)
- Documented all npm commands, module architecture (FirebaseModule, AuthModule, TasksModule), Firebase data model, service worker

**Source app CLAUDE.md** (`/todo-angular-firebase-demo/CLAUDE.md`):
- Deeper documentation of route structure, guard logic, ReplaySubject filter pattern
- Noted the `fdescribe`/`fit` tip for running single tests (no native `--spec` flag in Angular CLI 1.x)

**Key finding:** The source app is Angular 4 with AngularFire2, Firebase Realtime Database, 5 OAuth providers (Google, GitHub, Twitter, Facebook, Anonymous), tasks stored at `/tasks/{uid}/{taskKey}`.

---

### Phase 1 — Planning the Approach

**Trigger:** "what steps do you need to migrate todo-angular-firebase-demo to python fast api, front end is react nextjs"

Initial plan was written to `/Users/trongpv6/.claude/plans/what-steps-do-you-harmonic-hollerith.md`.

**Architecture decisions made (via user Q&A):**
- Auth: Full replacement — NextAuth.js + FastAPI JWT (no Firebase SDK)
- Database: SQLite + SQLAlchemy (dev/demo scale)
- Styling: Tailwind CSS
- Structure: Monorepo `/frontend` + `/backend` inside `todo-app-migrated/`

**User then redirected:** "ultraplan with: demo site of legacy app" — they wanted the structured 4-step SDS (Spec-Driven Skills) workflow instead of a one-shot plan.

The SDS workflow maps to their 4 steps:
1. Analyze legacy code → **`/sds.spec`** (spec + context)
2. Use output → **`/sds.design`** + **`/sds.task`** (plan + tasks)
3. Tasks → code → **`/sds.execute`** (new code)
4. Code → **`/sds.verify`** (review + verify)

---

### Phase 2 — Specification (`/sds.spec`)

**Output:** `spec-driven/todo-app-migration-fastapi-nextjs/spec.md`

Two Explore agents ran in parallel:
- One did deep analysis of ALL source files (components, templates, services, guards, models, CSS classes, animations)
- One fetched the live demo at `ng2-todo-app.firebaseapp.com` (only got HTML shell — Angular SPA, no SSR)

**Elicitation questions asked:**
- Overview confirmation → approved
- FR review → all 10 Must-Have + 1 Should-Have approved
- Out of scope → Data migration from Firebase + CI/CD pipeline
- NFRs → API < 200ms + JWT 30 days + HTTPS in production
- Success metrics → functional parity + API correctness + auth coverage + sds.verify

**Spec produced:**
- **11 FRs** (FR-1 through FR-11), 10 Must-Have, 1 Should-Have
- **34 acceptance criteria** in Given/When/Then BDD format
- **3 NFRs**
- Technical context section documenting: legacy data model mapping, auth flow replacement, filter mechanism (ReplaySubject → URL query param)
- Target DB schema (SQL), target API surface (6 endpoints)

---

### Phase 3 — Architectural Design (`/sds.design`)

**Output:** `spec-driven/todo-app-migration-fastapi-nextjs/design.md`

**Phase 0 of sds.design:** Confirmed greenfield (`todo-app-migrated/` had only a LICENSE), triggering Full adaptive flow with 3 research subagents.

**3 research subagents dispatched in parallel:**

1. **NextAuth.js ↔ FastAPI JWT exchange** — Found:
   - Use NextAuth.js v5 (not v4) — App Router native support, `auth()` function
   - Exchange FastAPI JWT in the `jwt` callback with `trigger === 'signIn' && account` guard (server-side, one-time per sign-in)
   - Store `access_token` inside NextAuth encrypted session cookie (JWE)
   - CredentialsProvider pattern for anonymous sign-in

2. **FastAPI + SQLAlchemy structure** — Found:
   - Flat `app/` package layout (right-sized for 2 routers)
   - Sync SQLAlchemy + `check_same_thread=False` for SQLite (no async needed)
   - `HTTPBearer()` + python-jose for JWT dependency injection
   - Inline ownership checks in PATCH/DELETE (not a dependency — 2 endpoints don't justify it)
   - Pydantic v2 with `ConfigDict(from_attributes=True)`
   - `create_all` in lifespan (not Alembic for SQLite greenfield)

3. **Next.js App Router + TanStack Query patterns** — Found:
   - Server page reads `searchParams.completed` synchronously → passes as prop to `TasksContainer` ('use client')
   - Eliminates `useSearchParams()` and its Suspense boundary requirement
   - Refetch-after-mutate via `invalidateQueries({ queryKey: ['tasks'] })` — no optimistic updates
   - Filter tabs use `<Link>` components (no `useSearchParams`)
   - `useRef + useEffect([isEditing])` for autoFocus — SSR-safe, mirrors Angular AutoFocusDirective

**Key decisions (8 ADs):**
- AD-3: Twitter + Facebook deferred (Twitter OAuth 1.0a complexity, Facebook needs HTTPS for localhost)
- AD-6: Server page.tsx + client TasksContainer — eliminates Suspense requirement
- AD-7: Refetch-after-mutate (no optimistic updates — local FastAPI is fast enough)
- AD-8: Link-based filter tabs — no `useSearchParams`

**Design document produced:**
- 8 Architecture Decisions with Context/Decision/Rationale/Alternatives
- 20 Findings (F-1 through F-20) with source + confidence
- 10 Standards (S-1 through S-10)
- 30-file inventory (12 backend + 18 frontend), each mapped to FRs
- 1 Spec Deviation: Twitter/Facebook deferred (approved)

**Validation:** Advisory findings on FR-11 (responsive detail) → patched with Tailwind `sm:` breakpoint guidance → validation passed.

---

### Phase 4 — Task Decomposition (`/sds.task`)

**Output:** `spec-driven/todo-app-migration-fastapi-nextjs/tasks.md` + 6 bundle files + 6 progress files

**Strategy chosen by user:** Walking Skeleton

**7 slices → 6 execution bundles:**

| Bundle | Slices | STEPs | Parallel? |
|---|---|---|---|
| B-1: Backend Foundation | 1–2 | STEP-1 to STEP-6 | Yes (with B-3) |
| B-2: Backend Task Endpoints | 3 | STEP-7 to STEP-9 | After B-1 |
| B-3: Frontend Infrastructure | 4 | STEP-10 to STEP-12 | Yes (with B-1) |
| B-4: Frontend Auth Flow | 5 | STEP-13 to STEP-17 | After B-3 |
| B-5: Frontend Task UI | 6 | STEP-18 to STEP-22 | After B-4 |
| B-6: Integration + Docs | 7 | STEP-23 | After B-2 + B-5 |

**Each STEP contains:**
- Trace (`[FR-N -> AC-N.M]`)
- Effort (XS/S/M/L)
- Intent (the "why" and risk flags — non-obvious constraints)
- Implementation guidance (max 5 bullets)
- Verify clause (Level | Given | Action | Outcome)
- Standards (S-N references)
- Dependencies

**NFR traceability:**
- NFR-1 (< 200ms): Platform (SQLite + localhost)
- NFR-2 (JWT 30 days): Implemented — STEP-6 + STEP-13
- NFR-3 (HTTPS): Deferred — out of scope per spec

**Test approach:** `test-after` — STEP-9 (backend tests) and STEP-22 (frontend tests) are paired test STEPs.

**Validation:** All 10 quality checks passed (TQ-1 through TQ-10).

---

### Phase 5 — Code Execution (`/sds.execute`)

**Branch:** `spec-driven/todo-app-migration-fastapi-nextjs/exec` (outer repo)  
**Code commits:** In `todo-app-migrated/` inner git repo (23 `[STEP-N]` commits)

**Execution order (sequential, parallelism=1):**
B-1 → B-3 → B-2 → B-4 → B-5 → B-6

**Note on repo structure:** `todo-app-migrated/` is its own git repo (already existed with a LICENSE and an initial commit). The outer repo (`migrate-todo-app/`) tracks it as a gitlink (submodule reference). After each bundle, the outer repo was committed with the updated submodule pointer + progress files.

#### Bundle 1 — Backend Foundation (STEP-1 to STEP-6)
Created the complete FastAPI backend structure:
- `backend/requirements.txt` — fastapi, uvicorn, sqlalchemy, python-jose, pydantic-settings, httpx, pytest
- `backend/app/config.py` — `Settings(BaseSettings)` reading from `.env`
- `backend/app/database.py` — SQLAlchemy engine with `check_same_thread=False`, `get_db` generator
- `backend/app/models.py` — `User` (UniqueConstraint provider+provider_id) and `Task` (FK cascade, Index user+completed)
- `backend/app/main.py` — FastAPI app with lifespan (create_all), CORSMiddleware, health check
- `backend/app/schemas.py` — Pydantic v2: OAuthLogin, TokenResponse, TaskCreate (field_validator), TaskUpdate (all optional), TaskOut (from_attributes)
- `backend/app/dependencies.py` — `HTTPBearer()` + `get_current_user` (401 on any failure)
- `backend/app/routers/auth.py` — `POST /auth/oauth` (upsert by provider+provider_id), `POST /auth/anonymous` (uuid4)

#### Bundle 3 — Frontend Infrastructure (STEP-10 to STEP-12)
Created Next.js 14 project foundation:
- `frontend/package.json` — next@14, next-auth@5, @tanstack/react-query@5
- `frontend/tsconfig.json` — strict mode, `@/` path alias
- `frontend/tailwind.config.ts` — custom `sm540: "540px"` breakpoint (spec AC-11.2)
- `frontend/app/layout.tsx` — Server Component (no 'use client')
- `frontend/app/providers.tsx` — `'use client'`, SessionProvider + QueryClientProvider with useState guard
- `frontend/types/next-auth.d.ts` — augments Session.accessToken, JWT.accessToken, User.anonymousToken

#### Bundle 2 — Backend Task Endpoints (STEP-7 to STEP-9)
Completed the FastAPI API:
- `backend/app/routers/tasks.py` — `GET /tasks` (filter by user_id + optional completed), `POST /tasks` (201), `PATCH /tasks/{id}` (inline ownership), `DELETE /tasks/{id}` (204)
- `backend/tests/conftest.py` — StaticPool in-memory SQLite, dependency override, fixtures
- `backend/tests/test_auth.py` — upsert idempotency, unique anonymous users, invalid token 401
- `backend/tests/test_tasks.py` — per-user scoping, completion filter, ownership 404, 204 delete

**Test result: 13 passing**

#### Bundle 4 — Frontend Auth Flow (STEP-13 to STEP-17)
Complete NextAuth + FastAPI integration:
- `frontend/auth.ts` — NextAuth v5 with Google, GitHub, CredentialsProvider (anonymous); `jwt` callback exchanges FastAPI token on `trigger === 'signIn'`; `session.maxAge = 30*24*60*60`
- `frontend/app/api/auth/[...nextauth]/route.ts` — re-exports handlers
- `frontend/middleware.ts` — bidirectional guard: `/tasks` → `/` if unauth; `/` → `/tasks` if auth
- `frontend/lib/api.ts` — `getSession()` + Bearer injection; exports getTasks, createTask, updateTask, deleteTask
- `frontend/components/SignIn.tsx` — Google, GitHub, guest buttons; error handling for AC-1.3
- `frontend/components/Header.tsx` — conditional sign-out button (`callbackUrl: '/'`)

#### Bundle 5 — Frontend Task UI (STEP-18 to STEP-22)
Complete task management UI:
- `frontend/app/tasks/page.tsx` — Server Component; reads `searchParams.completed`; passes to TasksContainer
- `frontend/components/TasksContainer.tsx` — `'use client'`; `useQuery(['tasks', completed])`; three mutations with `invalidateQueries`
- `frontend/components/TaskForm.tsx` — controlled input; `trim()` before empty check; Escape clears; re-focuses after create
- `frontend/components/TaskList.tsx` — three `<Link>` filter tabs; no `useSearchParams()`; active state from prop
- `frontend/components/TaskItem.tsx` — `useRef + useEffect([isEditing])` for autoFocus; `cancelRef` prevents blur-save on Escape; saves only if `changed && non-empty`; strikethrough via Tailwind
- `frontend/jest.config.ts` — `setupFilesAfterEnv` (note: corrected from the erroneous `setupFilesAfterFramework` in the task spec)
- `frontend/components/__tests__/TaskForm.test.tsx` — 4 tests covering AC-4.3
- `frontend/components/__tests__/TaskItem.test.tsx` — 5 tests covering AC-8.3, AC-8.4, AC-8.5, AC-7.1

#### Bundle 6 — Integration + Documentation (STEP-23)
Three README files:
- `todo-app-migrated/README.md` — monorepo overview, quick start (backend first!), optional Twitter/Facebook notes
- `backend/README.md` — setup, `.env` config table, uvicorn command, API endpoints table, pytest
- `frontend/README.md` — Google/GitHub OAuth setup steps, NEXTAUTH_SECRET generation, npm run dev/test, feature parity table

**Outer repo commits after each bundle:** 5 commits updating the submodule pointer + progress files.

---

### Phase 6 — Verification (`/sds.verify`)

**6 parallel verification agents dispatched:**

| Dimension | Verdict | Key Findings |
|---|---|---|
| Traceability | PASS | All 11 FRs → ADs → STEPs → commits, spec hash verified |
| Completeness | PASS WITH CAVEATS | Twitter/Facebook not implemented (approved deviation) |
| Code Quality | PASS | 1 INFO: AnonymousResponse consolidated to TokenResponse |
| Test Quality | PASS WITH CAVEATS | 1 HIGH: JWT expiry not tested; 2 MEDIUM: test gaps |
| Regression | PASS | 13 backend tests passing, structural checks all pass |
| Security | **FAIL** | 1 CRITICAL: `backend/.env` committed to git |

**Overall verdict: FAIL** (driven by the CRITICAL .env finding)

---

### Phase 7 — Remediation

**User selected to fix:** VF-1 (CRITICAL) + VF-5/9/10 (MEDIUM)

**VF-1 — Remove .env from git:**
```bash
git rm --cached backend/.env
echo "backend/.env" >> .gitignore
```
`backend/.env` is no longer tracked; `.gitignore` prevents future accidents.

**VF-5 — Fix 404/403 task ID enumeration:**
Changed PATCH + DELETE from sequential `404 → 403` checks to a single combined query:
```python
# Before (leaked task existence to unauthorized users):
task = db.query(Task).filter(Task.id == task_id).first()   # 404 if missing
if task.user_id != current_user.id: raise 403              # 403 reveals task exists

# After (prevents enumeration):
task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
if task is None: raise 404  # same 404 for both "not found" and "not owned"
```

**VF-9 — TaskList empty state test:**
Created `frontend/components/__tests__/TaskList.test.tsx` with 4 tests including empty state (`tasks=[]` → renders "No tasks").

**VF-10 — Anonymous JWT validation test:**
Added `test_anonymous_token_is_valid_jwt` — decodes the returned JWT, asserts `sub == str(user_id)` and `exp` is in the future.

**Bonus VF-2 — JWT expiry boundary test:**
Added `test_expired_jwt_returns_401` — encodes a JWT with `exp = now - 1 day`, asserts GET /tasks returns 401.

**Ownership tests updated:** Both `test_update_task_ownership` and `test_delete_task_ownership` updated to expect 404 (not 403) — aligned with the VF-5 fix. Comments explain the VF-5 reasoning.

**Backend test count after remediation: 15 passing (was 13)**

---

### Phase 8 — Re-Verification (`/sds.verify --focus security,testing`)

**2 focused agents confirmed:**

| Finding | Status |
|---|---|
| VF-1 CRITICAL (.env in git) | ✅ FIXED — `git ls-files backend/.env` returns empty |
| VF-5 MEDIUM (404/403 enumeration) | ✅ FIXED — single combined query confirmed |
| VF-2 HIGH (JWT expiry test) | ✅ FIXED — `test_expired_jwt_returns_401` exists |
| VF-9 MEDIUM (TaskList empty state) | ✅ FIXED — `TaskList.test.tsx` with empty state assertion |
| VF-10 MEDIUM (anonymous JWT unvalidated) | ✅ FIXED — `test_anonymous_token_is_valid_jwt` decodes and asserts |

**Final verdict: PASS WITH CAVEATS**

Remaining open (hardening backlog, not blocking):
- VF-3 HIGH: JWT 30-day expiry (accepted per spec NFR-2)
- VF-6 MEDIUM: No rate limiting on `/auth/anonymous`
- VF-7 MEDIUM: CORS `allow_methods=["*"]` (should restrict to specific methods)
- VF-8 MEDIUM: No `ProviderEnum` allowlist on `/auth/oauth`
- VF-4 MEDIUM: Twitter + Facebook OAuth not implemented (approved AD-3 deviation)

---

## Final State of the Repository

### Outer repo (`migrate-todo-app/`) — `main` branch
```
migrate-todo-app/
├── CLAUDE.md                                    # Root project guidance
├── spec-driven/
│   └── todo-app-migration-fastapi-nextjs/
│       ├── spec.md                              # 11 FRs, 34 ACs, 3 NFRs
│       ├── design.md                            # 8 ADs, 20 Findings, 10 Standards
│       ├── tasks.md                             # 23 STEPs, NFR traceability
│       ├── bundle-1.md → bundle-6.md            # Self-contained execution units
│       ├── progress-bundle-1.md → -6.md         # All steps: done
│       └── verify-report.md                     # PASS WITH CAVEATS
├── todo-angular-firebase-demo/                  # Source app (Angular 4 + Firebase)
└── todo-app-migrated/                           # ← tracked as gitlink (submodule)
```

### Inner repo (`todo-app-migrated/`) — `main` branch, 27 commits
```
todo-app-migrated/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore                               # includes backend/.env
│   ├── README.md
│   └── app/
│       ├── config.py                            # pydantic-settings BaseSettings
│       ├── database.py                          # SQLAlchemy engine + get_db
│       ├── models.py                            # User + Task ORM models
│       ├── schemas.py                           # Pydantic v2 schemas
│       ├── dependencies.py                      # get_current_user (HTTPBearer)
│       ├── main.py                              # FastAPI + lifespan + CORS
│       └── routers/
│           ├── auth.py                          # POST /auth/oauth, /auth/anonymous
│           └── tasks.py                         # GET/POST/PATCH/DELETE /tasks
└── frontend/
    ├── package.json                             # next@14, next-auth@5, react-query@5
    ├── tsconfig.json                            # strict, @/ alias
    ├── tailwind.config.ts                       # sm540: "540px" custom breakpoint
    ├── auth.ts                                  # NextAuth v5 config
    ├── middleware.ts                            # Route guards
    ├── types/next-auth.d.ts                     # Session type augmentation
    ├── lib/api.ts                               # Typed fetch wrapper (Bearer injection)
    ├── app/
    │   ├── layout.tsx                           # Server Component root
    │   ├── providers.tsx                        # 'use client' SessionProvider + QueryClient
    │   ├── page.tsx                             # Sign-in page (Server Component)
    │   ├── globals.css                          # Tailwind directives only
    │   ├── api/auth/[...nextauth]/route.ts      # NextAuth route handler
    │   └── tasks/
    │       ├── layout.tsx                       # Header wrapper
    │       └── page.tsx                         # Server Component (reads searchParams)
    └── components/
        ├── SignIn.tsx                           # Google, GitHub, guest buttons
        ├── Header.tsx                           # Sign-out button (conditional)
        ├── TasksContainer.tsx                   # useQuery + mutations
        ├── TaskForm.tsx                         # Create task input
        ├── TaskList.tsx                         # Filter tabs (Link) + list
        ├── TaskItem.tsx                         # Toggle, inline edit, delete
        └── __tests__/
            ├── TaskForm.test.tsx                # 4 tests (AC-4.3 coverage)
            ├── TaskItem.test.tsx                # 5 tests (AC-8.3/4/5 coverage)
            └── TaskList.test.tsx                # 4 tests (empty state + filters)
```

---

## Git History Summary

### Outer repo (`migrate-todo-app`)
```
f7170ce  docs(verify): update report — FAIL → PASS WITH CAVEATS after remediation
1c2287e  fix: apply remediation for VF-1, VF-5, VF-9, VF-10 from sds.verify
4a6b322  merge: Bundle 6 — Integration + Documentation
4f63c5d  merge: Bundle 5 — Frontend Task UI
a30b227  merge: Bundle 4 — Frontend Auth Flow
8e9d4ef  merge: Bundle 2 — Backend Task Endpoints
cea5f56  merge: Bundle 3 — Frontend Infrastructure
9500a55  first commit (spec-driven artifacts + initial submodule pointer)
```

### Inner repo (`todo-app-migrated`)
```
679499e  fix(security+tests): address VF-5/VF-9/VF-10 findings
54fbd79  fix(security): remove backend/.env from version control [VF-1]
4a49151  [STEP-23] Integration documentation + startup guide
6d75548  [STEP-22] Frontend test suite
9c5a8e6  [STEP-21] TaskItem component (toggle, inline edit, delete)
e561106  [STEP-20] TaskList component + filter tabs
a22dbb9  [STEP-19] TaskForm component
3ae75a4  [STEP-18] Tasks page (Server) + TasksContainer (Client)
309ad3c  [STEP-17] Header component + sign-out
dcad427  [STEP-16] Sign-in page + SignIn component
c7f3d9b  [STEP-15] API client wrapper (lib/api.ts)
9c6478f  [STEP-14] NextAuth route handler + middleware
f2a2e3d  [STEP-13] NextAuth v5 configuration (auth.ts)
31a1f82  [STEP-8] Task PATCH + DELETE with ownership
e22362e  [STEP-9] Backend test suite
e01a079  [STEP-7] Task GET + POST endpoints
e4fb9a1  [STEP-12] TypeScript session type augmentation
074e0a1  [STEP-11] Root layout + Providers wrapper
09ef024  [STEP-10] Next.js project initialization
4dec796  [STEP-6] Auth router (/auth/oauth + /auth/anonymous)
c9cc510  [STEP-5] JWT dependency (get_current_user)
607358e  [STEP-4] Pydantic schemas (auth + tasks)
072f53f  [STEP-3] FastAPI app entry point + CORS
80726a6  [STEP-2] Database engine + ORM models
55b7b14  [STEP-1] FastAPI project scaffold + config
f837921  Initial commit
```

---

## How to Run the App

```bash
# 1. Backend (start first — frontend exchanges tokens with FastAPI on sign-in)
cd todo-app-migrated/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # Set SECRET_KEY with: openssl rand -base64 32
uvicorn app.main:app --reload --port 8000
# Verify: curl http://localhost:8000/ → {"status": "ok"}

# 2. Frontend (new terminal)
cd todo-app-migrated/frontend
npm install
cp .env.local.example .env.local   # Fill in OAuth credentials + NEXTAUTH_SECRET
npm run dev                         # http://localhost:3000

# 3. Backend tests
cd todo-app-migrated/backend
source .venv/bin/activate
pytest tests/ -v    # → 15 passed
```

---

## Key Technical Decisions That Weren't Obvious

1. **JWT callback, not signIn callback** — The `signIn` callback cannot write to the NextAuth JWT. The token exchange with FastAPI must happen in the `jwt` callback with `trigger === 'signIn' && account` guard.

2. **Server page → client container pattern** — `app/tasks/page.tsx` reads `searchParams` synchronously (Server Component) and passes `completed` as a prop to `TasksContainer`. This avoids `useSearchParams()` and its Suspense boundary requirement entirely.

3. **`cancelRef` for Escape in TaskItem** — In React, `onBlur` fires before `onKeyDown` in some browsers. A `cancelRef = useRef(false)` flag set in the Escape handler prevents the blur handler from saving after Escape is pressed.

4. **`StaticPool` for SQLite in-memory tests** — SQLite in-memory databases are per-connection by default. Without `StaticPool`, each test gets an empty DB. `StaticPool` shares a single connection across all tests within a session.

5. **`setupFilesAfterEnv` not `setupFilesAfterFramework`** — The sds.task skill had a typo in the jest config field name. The executing agent correctly used `setupFilesAfterEnv` (the real Jest API).

6. **404 not 403 for unauthorized task access** — To prevent task ID enumeration (user B probing IDs to learn which ones exist), PATCH and DELETE combine the existence + ownership check into one query and always return 404, whether the task doesn't exist or belongs to another user.

7. **`backend/.env` was committed** — The inner repo's `.gitignore` only excluded `.venv` and `__pycache__`. The `.env` file was tracked in git. This was the CRITICAL security finding caught by `sds.verify`. Fixed with `git rm --cached`.
