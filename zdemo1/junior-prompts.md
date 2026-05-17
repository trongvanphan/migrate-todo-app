# Junior Dev Prompts — Reproduce the Migration End-to-End

Two scenarios. Pick whichever fits your situation.

---

## Scenario A — Start completely from scratch (no spec/design/tasks yet)

Use this if you are starting with only the source Angular app and an empty `todo-app-migrated/` folder.

Paste this single prompt into Claude Code and press Enter. Do not interrupt.

```
Migrate the Angular Firebase app at `todo-angular-firebase-demo/` to a modern stack
in `todo-app-migrated/`. Run the full SDS workflow (spec → design → tasks → execute → verify)
end-to-end without pausing for human input. All decisions are pre-made below — use them
exactly as written, do not ask clarifying questions.

---

ARCHITECTURE DECISIONS (final — do not deviate):

Backend:
- FastAPI + Uvicorn
- SQLAlchemy (sync, not async) + SQLite
- Pydantic v2 with ConfigDict(from_attributes=True)
- python-jose for JWT (HS256, 30-day expiry)
- pydantic-settings BaseSettings reading from .env
- Tables created via Base.metadata.create_all() in FastAPI lifespan
- No Alembic (SQLite greenfield, not needed)
- HTTPBearer() + get_current_user dependency for auth
- Ownership check: single combined filter(Task.id == id, Task.user_id == current_user.id) → always 404, never 403

Frontend:
- Next.js 14 App Router
- NextAuth v5 (NOT v4) — Google, GitHub, CredentialsProvider (anonymous/guest)
- TanStack Query v5 (@tanstack/react-query)
- Tailwind CSS with custom sm540:"540px" breakpoint
- Token exchange in jwt() callback with trigger === 'signIn' && account guard (NOT in signIn callback)
- Server Component page.tsx reads searchParams.completed → passes as prop to 'use client' TasksContainer
- Filter tabs use <Link> components, no useSearchParams()
- Refetch-after-mutate via invalidateQueries (no optimistic updates)
- useRef + useEffect([isEditing]) for autoFocus on TaskItem
- cancelRef pattern in TaskItem to prevent blur-save on Escape
- Jest config: use next/jest (SWC), NOT babel-jest — do NOT create .babelrc

Out of scope (do not implement):
- Twitter OAuth
- Facebook OAuth
- Data migration from Firebase
- CI/CD pipeline
- HTTPS (deferred to production)

Spec decisions (pre-answered, use these):
- FRs: sign-in (Google/GitHub/Guest), sign-out, route guard, create task, list tasks,
  filter tasks (All/Active/Completed), toggle completion, inline edit title, delete task,
  per-user isolation, responsive layout (540px)
- NFR-1: API < 200ms (local SQLite satisfies this, no special work needed)
- NFR-2: JWT 30-day expiry (implement in STEP-6 and auth.ts)
- NFR-3: HTTPS in production (deferred — document in README, no code needed)
- Out of scope: data migration, CI/CD, Twitter/Facebook OAuth

Task strategy: Walking Skeleton

---

STEPS TO EXECUTE IN ORDER:

1. Run /sds.spec
   - Spec file: spec-driven/todo-app-migration-fastapi-nextjs/spec.md
   - Use all decisions above. Skip elicitation questions — write the spec directly.
   - Include: 11 FRs, acceptance criteria in Given/When/Then, 3 NFRs, target DB schema, API surface.

2. Run /sds.design
   - Design file: spec-driven/todo-app-migration-fastapi-nextjs/design.md
   - Use all architecture decisions above. No need to research alternatives — decisions are final.
   - Document as Architecture Decisions (ADs) with Context/Decision/Rationale.
   - Include the 30-file inventory mapping files to FRs.

3. Run /sds.task
   - Tasks file: spec-driven/todo-app-migration-fastapi-nextjs/tasks.md
   - Use Walking Skeleton strategy.
   - Bundle order: B-1 (backend foundation) ∥ B-3 (frontend infra) → B-2 (task endpoints) → B-4 (auth flow) → B-5 (task UI) → B-6 (docs)
   - Test strategy: test-after (backend tests in B-2, frontend tests in B-5)

4. Run /sds.execute
   - Execute all bundles in order. Do not stop between bundles.
   - Code goes in todo-app-migrated/backend/ and todo-app-migrated/frontend/
   - Commit after each bundle with message: "[STEP-N] description"

5. Run /sds.verify
   - Run all 6 verification dimensions in parallel.
   - If any CRITICAL or HIGH findings: fix them automatically without asking.
   - Re-run verification after fixes.

Do not pause for human input at any step. If a decision is needed, use the decisions above.
```

---

## Scenario B — Artifacts already exist, just execute and verify

Use this if `spec.md`, `design.md`, and `tasks.md` already exist in `spec-driven/todo-app-migration-fastapi-nextjs/` (e.g. you cloned this repo and want to reproduce the code output).

### Prompt B-1 — Execute all bundles

```
Run /sds.execute for the migration at spec-driven/todo-app-migration-fastapi-nextjs/.

Execute all 6 bundles end-to-end without pausing for human input:
- B-1: Backend Foundation (STEP 1–6) — FastAPI scaffold, models, schemas, auth router
- B-3: Frontend Infrastructure (STEP 10–12) — Next.js 14, providers, type augmentation
- B-2: Backend Task Endpoints (STEP 7–9) — tasks router + pytest suite
- B-4: Frontend Auth Flow (STEP 13–17) — NextAuth v5, middleware, api.ts, SignIn, Header
- B-5: Frontend Task UI (STEP 18–22) — tasks page, TasksContainer, TaskForm, TaskList, TaskItem, tests
- B-6: Integration + Docs (STEP 23) — README files

All code goes in todo-app-migrated/backend/ and todo-app-migrated/frontend/.
Commit after each bundle with format: "[STEP-N] description"

Critical implementation rules (must follow exactly):
1. JWT exchange happens in NextAuth jwt() callback, NOT signIn() callback
2. Use next/jest (SWC) for jest.config.ts — do NOT create .babelrc
3. Ownership check in PATCH/DELETE: single combined filter(Task.id==id, Task.user_id==uid) → 404 only, never 403
4. Server Component page.tsx reads searchParams → passes as prop to 'use client' TasksContainer
5. Use cancelRef = useRef(false) in TaskItem to prevent blur-save on Escape

Do not ask questions. Execute all bundles sequentially to completion.
```

### Prompt B-2 — Verify and auto-fix

Run this immediately after B-1 completes.

```
Run /sds.verify on todo-app-migrated/ against the spec at
spec-driven/todo-app-migration-fastapi-nextjs/spec.md.

Check all 6 dimensions: traceability, completeness, code quality, test quality, regression, security.

For any findings at CRITICAL or HIGH severity: fix them automatically without asking.
Known items to check specifically:
- backend/.env must NOT be tracked by git (if it is: git rm --cached backend/.env, add to .gitignore)
- PATCH/DELETE ownership must use combined filter → 404 (not sequential 404→403)
- JWT expiry test must exist (test_expired_jwt_returns_401)
- TaskList must have empty state test
- Anonymous sign-in JWT must be validated in tests

After fixing, re-run the security and testing dimensions to confirm findings are resolved.
Output a final verify-report.md to spec-driven/todo-app-migration-fastapi-nextjs/.
```

---

## Scenario C — Already have the code, just run it

Use this if `todo-app-migrated/` already has the backend and frontend code and you just want to start the app.

### Prompt C-1 — Start both servers and smoke test

```
Start the todo-app-migrated application and run a smoke test to verify it works.

Steps (execute all without asking):

1. Backend setup:
   cd todo-app-migrated/backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   If .env does not exist: cp .env.example .env and generate SECRET_KEY with: openssl rand -base64 32
   Start server: uvicorn app.main:app --reload --port 8000 &
   Wait for it to be ready: curl -s http://localhost:8000/ should return {"status":"ok"}

2. Backend tests:
   pytest tests/ -v
   Expected: 15 passed

3. Frontend setup:
   cd todo-app-migrated/frontend
   npm install
   npx tsc --noEmit (expect 0 errors)
   npm test -- --watchAll=false (expect 13 tests passed)
   npm run build (expect BUILD SUCCEEDED)

4. API smoke test — run each curl command and verify the expected result:
   - POST /auth/anonymous → get TOKEN
   - POST /tasks (title="Buy milk") → id assigned, completed=false
   - POST /tasks (title="Write tests") → new task
   - POST /tasks (title="Deploy app") → new task
   - GET /tasks → 3 tasks
   - PATCH /tasks/1 (completed=true) → task 1 completed
   - GET /tasks?completed=false → 2 tasks
   - GET /tasks?completed=true → 1 task
   - PATCH /tasks/2 (title="Write integration tests") → title updated
   - DELETE /tasks/1 → HTTP 204
   - POST /auth/anonymous (second user, TOKEN_B) → new user
   - GET /tasks with TOKEN_B → empty list (isolation works)
   - DELETE /tasks/2 with TOKEN_B → HTTP 404 (ownership enforced)
   - POST /tasks (title="") with TOKEN → HTTP 422 (validation works)

Report which checks passed and which failed.
```

---

## Notes for Junior Devs

**What you still need to provide yourself (cannot be automated):**

| Item | Where to get it |
|------|----------------|
| `GOOGLE_CLIENT_ID` | Google Cloud Console → APIs & Services → OAuth 2.0 Client IDs |
| `GOOGLE_CLIENT_SECRET` | Same as above |
| `GITHUB_CLIENT_ID` | github.com/settings/developers → OAuth Apps → New OAuth App |
| `GITHUB_CLIENT_SECRET` | Same as above |
| `NEXTAUTH_SECRET` | Run: `openssl rand -base64 32` |
| `SECRET_KEY` (FastAPI) | Run: `openssl rand -base64 32` |

**Callback URLs to configure in OAuth providers:**

For local development:
- Google: `http://localhost:3000/api/auth/callback/google`
- GitHub: `http://localhost:3000/api/auth/callback/github`

**If Claude gets stuck mid-execution**, re-run the same prompt and add:

```
Continue from where you left off. Already completed: [list what's done].
Do not re-create files that already exist. Skip to the next incomplete step.
```
