---
title: "Tasks: Todo App Migration — FastAPI + Next.js"
slug: todo-app-migration-fastapi-nextjs
version: "2.0"
date: 2026-05-17
status: final
design_source: spec-driven/todo-app-migration-fastapi-nextjs/design.md
design_hash: sha256:014db3e31998c48ca9bd7105f4f12da52c1e382e4a79ff6cd1f9a9512e713c23
spec_source: spec-driven/todo-app-migration-fastapi-nextjs/spec.md
spec_hash: sha256:8da3d3e2298a6b45d4897c6e4c7613a293e24fa52d95d363b7673b8ece40fc1f
strategy: walking-skeleton
test_approach: test-after
validation: subagent
---

# Tasks: Todo App Migration — FastAPI + Next.js

## Overview

**23 STEPs** across **7 slices** grouped into **6 execution bundles**.

| Bundle | Slices | STEPs | Parallel? |
|---|---|---|---|
| B-1: Backend Foundation | 1–2 | STEP-1 to STEP-6 | Parallel with B-3 |
| B-2: Backend Task Endpoints | 3 | STEP-7 to STEP-9 | After B-1 |
| B-3: Frontend Infrastructure | 4 | STEP-10 to STEP-12 | Parallel with B-1 |
| B-4: Frontend Auth Flow | 5 | STEP-13 to STEP-17 | After B-3 (B-1 recommended) |
| B-5: Frontend Task UI | 6 | STEP-18 to STEP-22 | After B-4 |
| B-6: Integration + Docs | 7 | STEP-23 | After B-2 + B-5 |

---

## NFR Traceability

| NFR | Disposition | Evidence |
|---|---|---|
| NFR-1: API response < 200ms | Platform | SQLite + FastAPI on localhost; no dedicated STEP needed — acceptable at dev/demo scale |
| NFR-2: JWT expiry 30 days | Implemented | STEP-6 (create_access_token expiry=timedelta(days=30)) + STEP-13 (session.maxAge = 30*24*60*60) |
| NFR-3: HTTPS in production | Deferred | Out of scope per spec — local dev only; add TLS termination at deployment host |

---

## Conflict Analysis

| Hot File | Slices | Sequencing |
|---|---|---|
| `backend/app/main.py` | Slice 1 (create), Slice 2 (mount auth router), Slice 3 (mount tasks router) | Sequential — STEP-3 creates, STEP-6 and STEP-7 modify in B-1 and B-2 |
| `backend/app/schemas.py` | Slice 2 (auth schemas), Slice 3 (task schemas) | Both in B-1; write auth + task schemas together in STEP-4 |
| `backend/app/routers/tasks.py` | Slice 3 | STEP-7 creates, STEP-8 extends — sequential in B-2 |
| `frontend/app/layout.tsx` | Slice 4 | Single STEP-11; no conflict |
| `frontend/components/TasksContainer.tsx` | Slice 6 | Single STEP-18; no conflict |

**No dependency cycles detected.**

---

## Slices

### Slice 1: Backend Infrastructure
**Stage:** skeleton | **Goal:** Working FastAPI app with DB tables created on startup, CORS configured, env-driven config

### Slice 2: Backend Auth Endpoints
**Stage:** depth | **Goal:** /auth/oauth and /auth/anonymous return valid JWTs; get_current_user dependency functional

### Slice 3: Backend Task Endpoints
**Stage:** depth | **Goal:** Full task CRUD with per-user scoping, completion filter, and ownership 403

### Slice 4: Frontend Infrastructure
**Stage:** skeleton | **Goal:** Next.js 14 project builds; Tailwind configured; TypeScript strict; session + query providers wired

### Slice 5: Frontend Auth Flow
**Stage:** depth | **Goal:** Sign-in (Google, GitHub, guest) exchanges FastAPI JWT; middleware guards /tasks and /

### Slice 6: Frontend Task UI
**Stage:** depth | **Goal:** Task list with create, toggle, inline edit, delete, and URL-driven filter — all calling FastAPI via api.ts

### Slice 7: End-to-End Integration
**Stage:** integration | **Goal:** Both servers run; full sign-in → task CRUD → sign-out flow documented and verified

---

## Bundle B-1: Backend Foundation

> Stage: skeleton + depth | Parallel: yes (with B-3 — no shared files) | Files: backend/requirements.txt, backend/.env.example, backend/app/config.py, backend/app/database.py, backend/app/models.py, backend/app/main.py, backend/app/schemas.py, backend/app/dependencies.py, backend/app/routers/auth.py, backend/app/routers/__init__.py

**Bundle Verify**: A running FastAPI instance accepts POST /auth/anonymous and returns a JWT that GET /tasks accepts as a Bearer token.
- **Level**: integration
- **Given**: FastAPI running on localhost:8000 with todo.db initialized
- **Action**: `curl -X POST http://localhost:8000/auth/anonymous` → extract token; `curl -H "Authorization: Bearer <token>" http://localhost:8000/tasks`
- **Outcome**: /auth/anonymous returns `{ access_token, user_id }`; /tasks returns `[]` with 200

---

### Context Preamble — B-1

**Architecture Decisions:**
- AD-4: Sync SQLAlchemy + create_all in lifespan (not Alembic)
- AD-5: HTTPBearer + python-jose for JWT dependency injection
- AD-2: FastAPI JWT exchange returns { access_token, user_id }

**Findings:**
- F-8: Flat app/ package with routers/ subdirectory
- F-9: Sync SQLAlchemy, check_same_thread=False, get_db generator dependency
- F-10: HTTPBearer() + python-jose; OAuth2PasswordBearer is wrong here
- F-12: Pydantic v2, ConfigDict(from_attributes=True) on ORM schemas
- F-13: CORS: allow_credentials=True, explicit allow_origins list
- F-14: create_all in lifespan (idempotent); Alembic is premature for SQLite greenfield
- F-15: Upsert by (provider, provider_id) — NOT email

**Standards:** S-1 (no Firebase), S-2 (secrets in .env), S-5 (Pydantic v2), S-6 (get_db dependency), S-10 (JWT sub as str)

**Constraints:** C-1 (SQLite serialized writes — acceptable for dev/demo)

---

### STEP-1: FastAPI project scaffold + config

**Trace:** `MANUAL -> project scaffold`
**Effort:** S

**Files:**
- `todo-app-migrated/backend/requirements.txt` — create
- `todo-app-migrated/backend/.env` — create
- `todo-app-migrated/backend/.env.example` — create
- `todo-app-migrated/backend/app/__init__.py` — create
- `todo-app-migrated/backend/app/config.py` — create

**Intent:** Establish environment-driven configuration via pydantic-settings. Hardcoded secrets are the primary risk — all values must come from .env. `DATABASE_URL` defaults to `sqlite:///./todo.db` (relative path from where uvicorn is started). `CORS_ORIGINS` is a `list[str]` to support multiple origins.

**Implementation guidance:**
1. `requirements.txt`: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `python-jose[cryptography]`, `pydantic-settings`, `python-dotenv`, `pytest`, `httpx`
2. `config.py`: `class Settings(BaseSettings)` with `secret_key: str`, `algorithm: str = "HS256"`, `access_token_expire_days: int = 30`, `database_url: str = "sqlite:///./todo.db"`, `cors_origins: list[str] = ["http://localhost:3000"]`, `model_config = SettingsConfigDict(env_file=".env")`
3. Export `settings = Settings()` singleton at module level
4. `.env.example`: provide all keys with placeholder values; `.env` is gitignored
5. `app/__init__.py`: empty

**Verify:**
- Level: inspection | Given: `.env` with `SECRET_KEY=test` | Action: `from app.config import settings; assert settings.secret_key == "test"` | Outcome: import succeeds without error

**Standards:** S-2, S-5
**Dependencies:** Enables STEP-2, STEP-3

---

### STEP-2: Database engine + ORM models

**Trace:** `[FR-4 -> AC-4.1], [FR-5 -> AC-5.1], [FR-10 -> AC-10.1]`
**Informed by:** AD-4, F-9, F-14, F-15
**Effort:** S

**Files:**
- `todo-app-migrated/backend/app/database.py` — create
- `todo-app-migrated/backend/app/models.py` — create

**Intent:** `check_same_thread=False` is mandatory for SQLite + FastAPI (FastAPI uses a threadpool for sync dependencies). The `UNIQUE(provider, provider_id)` constraint on `users` is critical — without it, the upsert in `/auth/oauth` will create duplicate users. `ON DELETE CASCADE` on `tasks.user_id` ensures task cleanup if a user row is deleted. The `completed` index with `user_id` mirrors Firebase's `orderByChild('completed')` for efficient filter queries.

**Implementation guidance:**
1. `database.py`: `engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})`; `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`; `Base = declarative_base()`; `def get_db() -> Generator: db = SessionLocal(); try: yield db; finally: db.close()`
2. `models.py User`: id (Integer PK), provider (String not null), provider_id (String not null), email (String nullable), name (String nullable), created_at (DateTime server default). UniqueConstraint('provider', 'provider_id')
3. `models.py Task`: id (Integer PK), user_id (Integer FK→users.id cascade delete), title (String not null), completed (Boolean default False), created_at (DateTime server default). Index('idx_tasks_user_completed', 'user_id', 'completed')
4. Import Base from database.py into models.py; do NOT call create_all here — that belongs in lifespan

**Verify:**
- Level: integration | Given: test config with `DATABASE_URL=sqlite:///./test.db` | Action: call `Base.metadata.create_all(bind=engine)` then inspect tables via `engine.execute("SELECT name FROM sqlite_master")` | Outcome: `users` and `tasks` tables exist; unique constraint on users(provider, provider_id) present

**Standards:** S-6, S-10
**Dependencies:** Depends on STEP-1; enables STEP-3, STEP-4

---

### STEP-3: FastAPI app entry point + CORS

**Trace:** `MANUAL -> app wiring`
**Informed by:** F-13, AD-4
**Effort:** S

**Files:**
- `todo-app-migrated/backend/app/main.py` — create

**Intent:** `CORSMiddleware` must be added before router mounts and must use `allow_credentials=True` with an explicit `allow_origins` list. Using `allow_origins=["*"]` with `allow_credentials=True` is invalid per the CORS spec and raises an error. The lifespan context manager pattern replaces the deprecated `@app.on_event("startup")`.

**Implementation guidance:**
1. `@asynccontextmanager async def lifespan(app): Base.metadata.create_all(bind=engine); yield`
2. `app = FastAPI(lifespan=lifespan)`
3. Add `CORSMiddleware` with `allow_origins=settings.cors_origins`, `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`
4. Mount auth and tasks routers (stubs OK for now — add `app.include_router(auth.router, prefix="/auth", tags=["auth"])`)
5. Add `@app.get("/")` health check returning `{"status": "ok"}`

**Verify:**
- Level: integration | Given: FastAPI running | Action: `OPTIONS http://localhost:8000/tasks -H "Origin: http://localhost:3000"` | Outcome: response includes `Access-Control-Allow-Origin: http://localhost:3000` and `Access-Control-Allow-Credentials: true`

**Standards:** S-1
**Dependencies:** Depends on STEP-2; enables STEP-6, STEP-7

---

### STEP-4: Pydantic schemas (auth + tasks)

**Trace:** `[FR-1 -> AC-1.1], [FR-1 -> AC-1.2], [FR-4 -> AC-4.1], [FR-5 -> AC-5.1]`
**Informed by:** F-12, F-15, AD-5
**Effort:** S

**Files:**
- `todo-app-migrated/backend/app/schemas.py` — create

**Intent:** `OAuthLogin` uses `provider_id` (not email) as the identity key — email is mutable and non-unique across providers. `TaskOut.model_config = ConfigDict(from_attributes=True)` enables direct serialization from SQLAlchemy ORM objects. `TaskUpdate` must be a fully optional model (all fields `Optional`) to support partial PATCH semantics.

**Implementation guidance:**
1. Auth schemas: `OAuthLogin(provider: str, provider_id: str, email: str | None, name: str | None)`, `TokenResponse(access_token: str, user_id: int, token_type: str = "bearer")`
2. Task schemas: `TaskCreate(title: str)`, `TaskUpdate(title: str | None = None, completed: bool | None = None)`, `TaskOut(id: int, title: str, completed: bool, created_at: datetime, model_config=ConfigDict(from_attributes=True))`
3. Validate `TaskCreate.title` is non-empty: `@field_validator('title') def title_not_empty(cls, v): ...`
4. All schemas use Pydantic v2 syntax (`from pydantic import BaseModel, ConfigDict, field_validator`)

**Verify:**
- Level: inspection | Given: schemas.py imported | Action: `TaskCreate(title="")` | Outcome: `ValidationError` raised; `TaskOut.model_config.from_attributes is True`

**Standards:** S-5
**Dependencies:** Depends on STEP-1; enables STEP-5, STEP-6, STEP-7

---

### STEP-5: JWT dependency (get_current_user)

**Trace:** `[FR-10 -> AC-10.1], [FR-10 -> AC-10.2]`
**Informed by:** AD-5, F-10, S-10
**Effort:** S

**Files:**
- `todo-app-migrated/backend/app/dependencies.py` — create

**Intent:** `HTTPBearer()` extracts the raw token from `Authorization: Bearer <token>` automatically. Must raise `401` (not `403`) on invalid/expired token — 403 is reserved for ownership violations in task handlers. JWT `sub` claim is `str(user.id)` at encode time; must cast to `int` at decode time. A tampered or expired token must not return a user row.

**Implementation guidance:**
1. `security = HTTPBearer()`
2. `def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:`
3. Try/except `JWTError` around `jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])`
4. `user_id = int(payload.get("sub"))` — raise 401 if sub is missing or not castable
5. Query `db.query(User).filter(User.id == user_id).first()` — raise 401 if user not found

**Verify:**
- Level: unit | Given: valid JWT for user_id=1 | Action: call `get_current_user` with TestClient | Outcome: returns User(id=1); expired token → 401; missing sub → 401; non-existent user_id → 401

**Standards:** S-6, S-10
**Dependencies:** Depends on STEP-2, STEP-4; enables STEP-6, STEP-7, STEP-8

---

### STEP-6: Auth router (/auth/oauth + /auth/anonymous)

**Trace:** `[FR-1 -> AC-1.1], [FR-1 -> AC-1.2], [FR-1 -> AC-1.3]`
**Informed by:** AD-2, AD-3, F-15, NFR-2
**Effort:** M

**Files:**
- `todo-app-migrated/backend/app/routers/__init__.py` — create
- `todo-app-migrated/backend/app/routers/auth.py` — create
- `todo-app-migrated/backend/app/main.py` — modify (mount auth router)

**Intent:** `POST /auth/oauth` upsert logic: query by `(provider, provider_id)` first — if not found, create. Always return a fresh JWT. Token expiry must be exactly `settings.access_token_expire_days` days (NFR-2). `POST /auth/anonymous` generates `provider_id = str(uuid4())` — each anonymous sign-in creates a new user (no idempotency needed since CredentialsProvider calls this once per sign-in). `create_access_token` encodes `sub: str(user.id)` and `exp: datetime.utcnow() + timedelta(days=30)`.

**Implementation guidance:**
1. `router = APIRouter()`; `app.include_router(router, prefix="/auth", tags=["auth"])` in main.py
2. `POST /auth/oauth`: accept `OAuthLogin`, query user, create if missing (`db.add(user); db.commit(); db.refresh(user)`), call `create_access_token({"sub": str(user.id)})`
3. `POST /auth/anonymous`: `user = User(provider="anonymous", provider_id=str(uuid4()))`; same token generation
4. `create_access_token(data: dict) -> str`: uses `jose.jwt.encode` with `SECRET_KEY` and expiry
5. Both endpoints return `TokenResponse(access_token=token, user_id=user.id)`

**Test STEP (test-after):** `MANUAL -> Test for STEP-6`
- `tests/test_auth.py`: POST /auth/oauth twice with same provider_id → same user_id returned both times; POST /auth/anonymous → valid JWT; expired JWT → 401 on protected endpoint
- Level: integration | uses TestClient with SQLite in-memory DB

**Verify:**
- Level: integration | Given: running FastAPI | Action: POST /auth/oauth twice with `{provider: "google", provider_id: "uid123", email: "a@b.com", name: "A"}` | Outcome: both return same `user_id`; JWT decodable with correct sub

**Standards:** S-2, S-10
**Dependencies:** Depends on STEP-3, STEP-4, STEP-5; enables B-4 (STEP-13)

---

## Bundle B-2: Backend Task Endpoints

> Stage: depth | Parallel: no (depends on B-1) | Files: backend/app/routers/tasks.py, backend/app/main.py, backend/tests/test_auth.py, backend/tests/test_tasks.py

**Bundle Verify**: All task CRUD endpoints enforce per-user isolation and the completion filter returns correct subsets.
- **Level**: integration
- **Given**: Two users with JWTs (via /auth/anonymous x2); user A has 3 tasks (2 incomplete, 1 complete)
- **Action**: User B calls GET /tasks — sees 0 tasks; user A calls GET /tasks?completed=false — sees 2 tasks; user B calls DELETE /tasks/{user_A_task_id} — gets 403
- **Outcome**: All three assertions pass with correct HTTP status codes

---

### Context Preamble — B-2

**Architecture Decisions:** AD-4 (sync SQLAlchemy), AD-5 (HTTPBearer dependency), AD-7 (refetch-after-mutate — no server-side behavior change needed)

**Findings:** F-9 (sync get_db), F-10 (HTTPBearer), F-11 (inline ownership check), F-12 (Pydantic v2)

**Standards:** S-5 (Pydantic v2), S-6 (get_db dependency), S-10 (JWT sub as str)

**Constraints:** C-1 (SQLite writes serialized)

**Relevant ACs:** AC-4.1, AC-4.3, AC-5.1, AC-5.2, AC-5.3, AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-7.1, AC-7.2, AC-7.3, AC-8.1, AC-8.2, AC-9.1, AC-10.1, AC-10.2, AC-10.3

---

### STEP-7: Task GET + POST endpoints

**Trace:** `[FR-4 -> AC-4.1], [FR-4 -> AC-4.3], [FR-5 -> AC-5.1], [FR-5 -> AC-5.2], [FR-5 -> AC-5.3], [FR-6 -> AC-6.1], [FR-6 -> AC-6.2], [FR-6 -> AC-6.3]`
**Informed by:** AD-4, F-11
**Effort:** M

**Files:**
- `todo-app-migrated/backend/app/routers/tasks.py` — create
- `todo-app-migrated/backend/app/main.py` — modify (mount tasks router)

**Intent:** `GET /tasks` filters by `user_id` always — user scoping is enforced at the query level, not via post-filter. Optional `?completed=` param: when present, add `filter(Task.completed == (completed == "true"))`. When absent, return all user tasks. `POST /tasks` validates title via Pydantic (`TaskCreate` has non-empty validator). `created_at` is server-set — never accept from client.

**Implementation guidance:**
1. `GET /tasks`: `def list_tasks(completed: str | None = Query(None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db))` → query base `db.query(Task).filter(Task.user_id == current_user.id)`, conditionally add `.filter(Task.completed == (completed.lower() == "true"))` when completed is not None
2. `POST /tasks`: accept `TaskCreate`, create `Task(user_id=current_user.id, title=body.title)`, `db.add(task); db.commit(); db.refresh(task)`, return `TaskOut.model_validate(task)`
3. Both endpoints return `list[TaskOut]` or `TaskOut` respectively
4. Mount: `app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])` in main.py

**Verify:**
- Level: integration | Given: user A and user B each authenticated | Action: user A creates 2 tasks; user B calls GET /tasks | Outcome: user B sees empty list (AC-5.3); user A calls GET /tasks?completed=false and sees only incomplete tasks (AC-6.1)

**Standards:** S-5, S-6
**Dependencies:** Depends on B-1 complete; enables STEP-8

---

### STEP-8: Task PATCH + DELETE with ownership

**Trace:** `[FR-7 -> AC-7.1], [FR-7 -> AC-7.2], [FR-7 -> AC-7.3], [FR-8 -> AC-8.1], [FR-8 -> AC-8.2], [FR-8 -> AC-8.3], [FR-8 -> AC-8.4], [FR-8 -> AC-8.5], [FR-9 -> AC-9.1], [FR-9 -> AC-9.2], [FR-10 -> AC-10.2], [FR-10 -> AC-10.3]`
**Informed by:** AD-5, F-11
**Effort:** S

**Files:**
- `todo-app-migrated/backend/app/routers/tasks.py` — modify

**Intent:** Ownership check order matters: return 404 if task not found, then 403 if task belongs to another user. This prevents information leakage (user B can't enumerate user A's task IDs by probing for 403 vs 404). `PATCH` uses `TaskUpdate` with all-optional fields — apply only non-None values using `task.title = update.title if update.title is not None else task.title`. `DELETE` returns 204 (no content), not 200.

**Implementation guidance:**
1. `PATCH /tasks/{task_id}`: fetch task, 404 if missing, 403 if `task.user_id != current_user.id`, apply updates, commit, return `TaskOut.model_validate(task)`
2. `DELETE /tasks/{task_id}`: same ownership check, `db.delete(task); db.commit()`, return `Response(status_code=204)`
3. Never use a shared `verify_task_owner()` dependency — inline check is explicit and avoids double-fetch
4. For PATCH: `if update.title is not None: task.title = update.title` and `if update.completed is not None: task.completed = update.completed`

**Verify:**
- Level: integration | Given: user A owns task_id=1 | Action: user B calls PATCH /tasks/1 | Outcome: 403 Forbidden; user A calls PATCH /tasks/1 with `{completed: true}` → 200 with `completed: true`; user A calls DELETE /tasks/1 → 204; task no longer returned in GET /tasks

**Standards:** S-6
**Dependencies:** Depends on STEP-7

---

### STEP-9: Backend test suite

**Trace:** `MANUAL -> Test for STEP-6, STEP-7, STEP-8`
**Effort:** M

**Files:**
- `todo-app-migrated/backend/tests/__init__.py` — create
- `todo-app-migrated/backend/tests/conftest.py` — create
- `todo-app-migrated/backend/tests/test_auth.py` — create
- `todo-app-migrated/backend/tests/test_tasks.py` — create

**Intent:** Use FastAPI `TestClient` with an in-memory SQLite database (override `get_db` dependency). Fixtures: `client` (TestClient), `db` (in-memory session), `user_token(db)` helper that calls /auth/anonymous and returns token. Key cases: upsert idempotency (same provider_id → same user_id), per-user scoping (user B cannot see user A's tasks), ownership 403, completion filter.

**Implementation guidance:**
1. `conftest.py`: override `get_db` via `app.dependency_overrides[get_db]` with in-memory SQLite session; `client = TestClient(app)` fixture
2. `test_auth.py`: test upsert idempotency (POST /auth/oauth twice → same user_id), anonymous creates unique users, invalid JWT → 401
3. `test_tasks.py`: create task → appears in list; user B cannot see user A's tasks; PATCH by owner succeeds; PATCH by non-owner → 403; DELETE by owner → 204; GET?completed=false returns only incomplete
4. Run with `pytest tests/` from `backend/`

**Verify:**
- Level: unit | Given: `pytest tests/` from backend/ | Action: run all tests | Outcome: all pass; 0 failures; covers auth router, task scoping, ownership, and filter

**Standards:** S-6, S-10
**Dependencies:** Depends on STEP-7, STEP-8

---

## Bundle B-3: Frontend Infrastructure

> Stage: skeleton | Parallel: yes (with B-1 — no shared files) | Files: frontend/package.json, frontend/tsconfig.json, frontend/tailwind.config.ts, frontend/app/globals.css, frontend/app/layout.tsx, frontend/app/providers.tsx, frontend/types/next-auth.d.ts

**Bundle Verify**: Next.js project builds successfully with TypeScript strict mode, Tailwind configured, and session + query providers available in the component tree.
- **Level**: inspection
- **Given**: project bootstrapped
- **Action**: `npm run build` from `frontend/`
- **Outcome**: Build completes with 0 TypeScript errors; no "session.accessToken does not exist on type Session" error

---

### Context Preamble — B-3

**Architecture Decisions:** AD-1 (NextAuth v5), AD-6 (server page + client container)

**Findings:** F-7 (TypeScript augmentation required), F-20 (SessionProvider + QueryClientProvider in providers.tsx)

**Standards:** S-3 (TypeScript strict), S-4 (Tailwind only), S-7 ('use client' on hook-using components only)

---

### STEP-10: Next.js project initialization

**Trace:** `MANUAL -> project scaffold`
**Effort:** S

**Files:**
- `todo-app-migrated/frontend/package.json` — create
- `todo-app-migrated/frontend/tsconfig.json` — create
- `todo-app-migrated/frontend/tailwind.config.ts` — create
- `todo-app-migrated/frontend/app/globals.css` — create
- `todo-app-migrated/frontend/.env.local.example` — create

**Intent:** Pin `next-auth@5` explicitly (not `next-auth@latest` which may resolve to v4). Pin `@tanstack/react-query@5` — v5 has breaking changes from v4 (queryKey must be an array, `status: 'loading'` renamed, onSuccess/onError moved out of useMutation). Tailwind content paths must include `./app/**/*.{ts,tsx}` and `./components/**/*.{ts,tsx}`. `@/` path alias must map to the project root (not `src/`).

**Implementation guidance:**
1. `package.json` dependencies: `next@14`, `next-auth@5`, `@tanstack/react-query@5`, `react@18`, `react-dom@18`, `typescript`, `tailwindcss`, `autoprefixer`, `postcss`, `@types/react`, `@types/node`
2. `tsconfig.json`: `"strict": true`, `"paths": { "@/*": ["./*"] }`, `"plugins": [{ "name": "next" }]`
3. `tailwind.config.ts`: `content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"]`; add custom `screens: { "sm540": "540px" }` for spec's exact breakpoint
4. `globals.css`: Tailwind directives only (`@tailwind base; @tailwind components; @tailwind utilities`)
5. `.env.local.example`: `NEXTAUTH_SECRET=`, `AUTH_SECRET=`, `NEXTAUTH_URL=http://localhost:3000`, `NEXT_PUBLIC_API_URL=http://localhost:8000`, `GOOGLE_CLIENT_ID=`, `GOOGLE_CLIENT_SECRET=`, `GITHUB_CLIENT_ID=`, `GITHUB_CLIENT_SECRET=`

**Verify:**
- Level: inspection | Given: project files written | Action: `npx tsc --noEmit` | Outcome: 0 TypeScript errors

**Standards:** S-3, S-4
**Dependencies:** Enables STEP-11, STEP-12

---

### STEP-11: Root layout + Providers wrapper

**Trace:** `[FR-1 -> AC-1.1], [FR-3 -> AC-3.1]`
**Informed by:** F-20, AD-1
**Effort:** S

**Files:**
- `todo-app-migrated/frontend/app/layout.tsx` — create
- `todo-app-migrated/frontend/app/providers.tsx` — create

**Intent:** `layout.tsx` must remain a Server Component — no `'use client'` directive. `providers.tsx` must be `'use client'` because it uses React context (`SessionProvider`, `QueryClientProvider`). `QueryClient` initialized inside `useState(() => new QueryClient(...))` — this prevents re-creation on every render while still being client-safe (not a module-level singleton which would be shared across requests in SSR).

**Implementation guidance:**
1. `providers.tsx`: `'use client'`; `const [queryClient] = useState(() => new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, retry: 1 } } }))`; wrap children in `<SessionProvider><QueryClientProvider client={queryClient}>{children}</QueryClientProvider></SessionProvider>`
2. `layout.tsx`: Server Component; `import { Providers } from './providers'`; standard `<html lang="en"><body><Providers>{children}</Providers></body></html>`
3. Import `globals.css` in layout.tsx

**Verify:**
- Level: inspection | Given: layout.tsx opened | Action: check for 'use client' at top | Outcome: NOT present on layout.tsx; IS present on providers.tsx; `npm run build` succeeds

**Standards:** S-3, S-7
**Dependencies:** Depends on STEP-10; enables STEP-13

---

### STEP-12: TypeScript session type augmentation

**Trace:** `[FR-1 -> AC-1.1]`
**Informed by:** F-7, AD-2
**Effort:** XS

**Files:**
- `todo-app-migrated/frontend/types/next-auth.d.ts` — create

**Intent:** Without this augmentation, `session.accessToken` and `token.accessToken` produce TypeScript errors in `auth.ts` and `lib/api.ts`. `User.anonymousToken` is required so the CredentialsProvider `authorize` function can return the FastAPI token to the `jwt` callback without type errors. All three interfaces must be augmented.

**Implementation guidance:**
1. Augment `Session`: `accessToken?: string`
2. Augment `JWT` (from `next-auth/jwt`): `accessToken?: string; fastapiUserId?: number`
3. Augment `User` (from `next-auth`): `anonymousToken?: string`
4. File location: `types/next-auth.d.ts` — must be discoverable by `tsconfig.json` `typeRoots` or `include`

**Verify:**
- Level: inspection | Given: types/next-auth.d.ts written | Action: in api.ts, write `const t: string = session?.accessToken ?? ""` | Outcome: `npx tsc --noEmit` passes with 0 errors

**Standards:** S-3
**Dependencies:** Depends on STEP-10; enables STEP-13, STEP-15

---

## Bundle B-4: Frontend Auth Flow

> Stage: depth | Parallel: no (depends on B-3; B-1 strongly recommended for live token exchange) | Files: frontend/auth.ts, frontend/middleware.ts, frontend/app/api/auth/[...nextauth]/route.ts, frontend/lib/api.ts, frontend/app/page.tsx, frontend/components/SignIn.tsx, frontend/components/Header.tsx

**Bundle Verify**: A user can sign in with Google or as a guest, land on /tasks with a valid FastAPI JWT in session, and sign out returning to /.
- **Level**: e2e (manual)
- **Given**: Both servers running (FastAPI on :8000, Next.js on :3000); Google OAuth app configured
- **Action**: Navigate to http://localhost:3000 → click "Sign in with Google" → complete OAuth → check session.accessToken is non-null → click "Sign out"
- **Outcome**: Lands on /tasks after sign-in; session.accessToken is a decodable FastAPI JWT; sign-out returns to / and /tasks redirects back to /

---

### Context Preamble — B-4

**Architecture Decisions:** AD-1 (NextAuth v5), AD-2 (jwt callback exchange), AD-3 (Google + GitHub only initial), F-5 (CredentialsProvider anonymous), F-6 (server-to-server exchange — no CORS on auth endpoints)

**Findings:** F-1 (NextAuth v5 App Router), F-2 (jwt callback trigger guard), F-3 (token in NextAuth encrypted cookie), F-4 (auth()→Server, useSession()→Client, api.ts→fetch), F-5 (anonymous CredentialsProvider), F-6 (no CORS on auth endpoints)

**Standards:** S-1 (no Firebase), S-2 (secrets in .env.local), S-3 (TypeScript), S-7 ('use client' sparingly), S-9 (api.ts is single fetch point)

**Risks:** R-3 (NextAuth v5 API still maturing — pin exact patch version)

**Relevant ACs:** AC-1.1, AC-1.2, AC-1.3, AC-2.1, AC-2.2, AC-3.1, AC-3.2, AC-3.3

---

### STEP-13: NextAuth v5 configuration (auth.ts)

**Trace:** `[FR-1 -> AC-1.1], [FR-1 -> AC-1.2], [FR-2 -> AC-2.1]`
**Informed by:** AD-1, AD-2, AD-3, F-1, F-2, F-3, F-5
**Effort:** L

**Files:**
- `todo-app-migrated/frontend/auth.ts` — create

**Intent:** The `jwt` callback is the only correct place to exchange the FastAPI token. The `trigger === 'signIn' && account` guard ensures the POST to FastAPI happens exactly once (on sign-in), not on every session access. For CredentialsProvider, detect `account?.type === 'credentials'` and read `user.anonymousToken` (set in `authorize`). `session.maxAge = 30*24*60*60` must match the FastAPI 30-day JWT to prevent session-token misalignment. The `POST /auth/oauth` call is server-to-server — `process.env.NEXT_PUBLIC_API_URL` must be readable server-side too (use non-public env var for backend URL in production).

**Implementation guidance:**
1. Config structure: `export const { handlers, auth, signIn, signOut } = NextAuth({ providers: [...], callbacks: { jwt, session }, session: { maxAge: 30*24*60*60 } })`
2. Providers: `GoogleProvider`, `GitHubProvider`, `CredentialsProvider({ name: "anonymous", credentials: {}, async authorize() { /* call POST /auth/anonymous */ } })`
3. `jwt` callback: `if (trigger === 'signIn' && account) { if (account.type === 'credentials') { token.accessToken = (user as any).anonymousToken } else { const res = await fetch(${process.env.INTERNAL_API_URL}/auth/oauth, { method: 'POST', body: JSON.stringify({ provider: account.provider, provider_id: account.providerAccountId, email: profile?.email, name: profile?.name }) }); const data = await res.json(); token.accessToken = data.access_token } }`
4. `session` callback: `session.accessToken = token.accessToken as string; return session`
5. `authorize` in CredentialsProvider: call `POST /auth/anonymous`, return `{ id: String(data.user_id), name: 'Guest', anonymousToken: data.access_token }`

**Verify:**
- Level: integration | Given: FastAPI running; mock Google OAuth | Action: simulate signIn flow → inspect token in jwt callback | Outcome: `token.accessToken` is set; `session.accessToken` non-null in `auth()` call

**Standards:** S-1, S-2, S-3
**Dependencies:** Depends on STEP-11, STEP-12; enables STEP-14, STEP-15

---

### STEP-14: NextAuth route handler + middleware

**Trace:** `[FR-3 -> AC-3.1], [FR-3 -> AC-3.2], [FR-3 -> AC-3.3]`
**Informed by:** F-4, AD-1
**Effort:** S

**Files:**
- `todo-app-migrated/frontend/app/api/auth/[...nextauth]/route.ts` — create
- `todo-app-migrated/frontend/middleware.ts` — create

**Intent:** The route handler simply re-exports `handlers` from `auth.ts`. Middleware reads `req.auth` (populated from session cookie) without a DB call. Matcher must cover `/tasks/:path*` (protect task route) and `/` (redirect authenticated users). Without the `/` matcher, authenticated users are not redirected away from the sign-in page.

**Implementation guidance:**
1. `route.ts`: `import { handlers } from "@/auth"; export const { GET, POST } = handlers`
2. `middleware.ts`: `import { auth } from "@/auth"; export default auth((req) => { const isLoggedIn = !!req.auth; if (!isLoggedIn && req.nextUrl.pathname.startsWith('/tasks')) { return NextResponse.redirect(new URL('/', req.url)); } if (isLoggedIn && req.nextUrl.pathname === '/') { return NextResponse.redirect(new URL('/tasks', req.url)); } }); export const config = { matcher: ['/', '/tasks/:path*'] };`

**Verify:**
- Level: integration | Given: Next.js running, no session | Action: GET /tasks | Outcome: 307 redirect to /; GET / with valid session → 307 redirect to /tasks

**Standards:** S-3, S-7
**Dependencies:** Depends on STEP-13; enables STEP-16, STEP-18

---

### STEP-15: API client wrapper (lib/api.ts)

**Trace:** `[FR-4 -> AC-4.1], [FR-5 -> AC-5.1], [FR-6 -> AC-6.1]`
**Informed by:** F-4, S-9
**Effort:** S

**Files:**
- `todo-app-migrated/frontend/lib/api.ts` — create

**Intent:** Every function in `api.ts` calls `getSession()` before fetching — no token caching. Stale tokens are handled by the NextAuth session expiry. `NEXT_PUBLIC_API_URL` is used for client-side calls; consider a non-public env var for server-side calls. No `fetch()` outside this module — `S-9` is a firm boundary.

**Implementation guidance:**
1. `const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'`
2. `async function apiFetch(path, init?)`: call `getSession()`, extract `session?.accessToken`, add `Authorization: Bearer` header if present, call `fetch(BASE + path, merged_options)`; throw on non-ok response with status code in error message
3. Export: `getTasks(completed?: string)`, `createTask(title: string)`, `updateTask(id: number, changes: Partial<TaskUpdate>)`, `deleteTask(id: number)`
4. TypeScript: define `interface Task { id: number; title: string; completed: boolean; created_at: string }` and `interface TaskUpdate { title?: string; completed?: boolean }`
5. `getTasks`: build URL with `?completed=${completed}` when completed is not undefined

**Verify:**
- Level: inspection | Given: grep across components/ and app/ directories | Action: `grep -r "fetch(" --include="*.ts" --include="*.tsx" components/ app/ | grep -v api.ts` | Outcome: 0 results — all fetches go through api.ts

**Standards:** S-3, S-9
**Dependencies:** Depends on STEP-12, STEP-13; enables STEP-18, STEP-19, STEP-20, STEP-21

---

### STEP-16: Sign-in page + SignIn component

**Trace:** `[FR-1 -> AC-1.1], [FR-1 -> AC-1.2], [FR-1 -> AC-1.3]`
**Informed by:** AD-1, F-5, AD-3
**Effort:** S

**Files:**
- `todo-app-migrated/frontend/app/page.tsx` — create
- `todo-app-migrated/frontend/components/SignIn.tsx` — create

**Intent:** `app/page.tsx` is a Server Component — no hooks. `SignIn.tsx` is `'use client'`. Anonymous sign-in calls `signIn('credentials', { redirect: false })` because CredentialsProvider cannot use redirect flow. On success, `router.push('/tasks')` navigates. On error (AC-1.3), display the error to the user — check `result.error` from the `signIn` response. OAuth providers use `signIn('google', { callbackUrl: '/tasks' })`.

**Implementation guidance:**
1. `page.tsx`: Server Component that renders `<SignIn />` centered on the page with Tailwind
2. `SignIn.tsx`: `'use client'`; `useRouter()` from `next/navigation`; three buttons: Google, GitHub, "Continue as guest"
3. Google/GitHub: `onClick={() => signIn('google', { callbackUrl: '/tasks' })}` 
4. Guest: async handler calling `const result = await signIn('credentials', { redirect: false })`; if `result?.ok` then `router.push('/tasks')`; else show error state
5. Style buttons with Tailwind: full-width, border, hover state — mirror source app's `.sign-in__button` dimensions (height 48px equivalent)

**Verify:**
- Level: inspection | Given: SignIn.tsx | Action: check error handling branch | Outcome: error state renders when `result?.error` is truthy (AC-1.3 coverage)

**Standards:** S-3, S-4, S-7
**Dependencies:** Depends on STEP-13, STEP-14; parallel with STEP-17

---

### STEP-17: Header component + sign-out

**Trace:** `[FR-2 -> AC-2.1], [FR-2 -> AC-2.2]`
**Informed by:** AD-1
**Effort:** XS

**Files:**
- `todo-app-migrated/frontend/components/Header.tsx` — create

**Intent:** Header is `'use client'` (uses `useSession()`). Sign-out must use `callbackUrl: '/'` so the user lands on sign-in after logout (AC-2.1). Do not render the sign-out button when `status !== 'authenticated'` — prevents a flash of the button during session loading (AC-2.2 protection).

**Implementation guidance:**
1. `'use client'`; `const { data: session, status } = useSession()`
2. Render app title (left) and sign-out button (right) only when `status === 'authenticated'`
3. `onClick={() => signOut({ callbackUrl: '/' })}` on sign-out button
4. Include Header in `app/tasks/layout.tsx` (create a tasks layout) so it appears only on the tasks page, not the sign-in page

**Verify:**
- Level: inspection | Given: Header.tsx | Action: check signOut call | Outcome: `callbackUrl: '/'` present; button conditionally rendered on `status === 'authenticated'`

**Standards:** S-3, S-4, S-7
**Dependencies:** Depends on STEP-13; parallel with STEP-16

---

## Bundle B-5: Frontend Task UI

> Stage: depth | Parallel: no (depends on B-4) | Files: frontend/app/tasks/page.tsx, frontend/app/tasks/layout.tsx, frontend/components/TasksContainer.tsx, frontend/components/TaskForm.tsx, frontend/components/TaskList.tsx, frontend/components/TaskItem.tsx, frontend/jest.config.ts, frontend/jest.setup.ts, frontend/components/__tests__/TaskForm.test.tsx, frontend/components/__tests__/TaskItem.test.tsx

**Bundle Verify**: Authenticated user can create, toggle, edit, and delete tasks; filter tabs change the visible task set; all mutations refetch the task list.
- **Level**: e2e (manual)
- **Given**: Both servers running; user authenticated (guest session)
- **Action**: Create 3 tasks → toggle one complete → click "Completed" filter → edit another's title → delete the third
- **Outcome**: Only completed task shown in Completed filter; edited title persists; deleted task absent

---

### Context Preamble — B-5

**Architecture Decisions:** AD-6 (server page + client container), AD-7 (refetch-after-mutate), AD-8 (Link-based filter tabs)

**Findings:** F-16 (server searchParams → client prop), F-17 (TanStack Query v5 invalidateQueries), F-18 (Link tabs, no useSearchParams), F-19 (useRef + useEffect autoFocus), F-20 (TanStack Query v5 API)

**Standards:** S-3, S-4, S-7, S-8 (all mutations invalidate ['tasks']), S-9 (api.ts only)

**Relevant ACs:** AC-4.1–AC-4.4, AC-5.1–AC-5.3, AC-6.1–AC-6.4, AC-7.1–AC-7.3, AC-8.1–AC-8.5, AC-9.1–AC-9.2, AC-11.1–AC-11.2

---

### STEP-18: Tasks page (Server) + TasksContainer (Client)

**Trace:** `[FR-5 -> AC-5.1], [FR-5 -> AC-5.2], [FR-6 -> AC-6.1], [FR-6 -> AC-6.2], [FR-6 -> AC-6.3], [FR-6 -> AC-6.4]`
**Informed by:** AD-6, AD-8, F-16
**Effort:** M

**Files:**
- `todo-app-migrated/frontend/app/tasks/page.tsx` — create
- `todo-app-migrated/frontend/app/tasks/layout.tsx` — create
- `todo-app-migrated/frontend/components/TasksContainer.tsx` — create

**Intent:** `page.tsx` reads `searchParams.completed` synchronously — this is only valid in Server Components in Next.js 14 (becomes a Promise in Next.js 15). Do NOT add `'use client'` to page.tsx. `TasksContainer` receives `completed` as a prop — this eliminates `useSearchParams()` and its Suspense boundary requirement. `queryKey: ['tasks', completed]` ensures the query re-fires when the filter changes (different key = new fetch).

**Implementation guidance:**
1. `page.tsx`: Server Component; `export default function TasksPage({ searchParams }: { searchParams: { completed?: string } }) { return <TasksContainer completed={searchParams.completed} /> }`
2. `layout.tsx` (tasks layout): `import Header from "@/components/Header"; export default function TasksLayout({ children }) { return <><Header />{children}</> }`
3. `TasksContainer.tsx`: `'use client'`; `const queryClient = useQueryClient()`; `const { data: tasks = [], isLoading } = useQuery({ queryKey: ['tasks', completed], queryFn: () => api.getTasks(completed) })`; render `<TaskForm />` + `<TaskList tasks={tasks} completed={completed} onUpdate={...} onDelete={...} />`; define mutation handlers that call `invalidateQueries({ queryKey: ['tasks'] })` on success
4. Pass mutation handlers down to TaskList and TaskItem via props

**Verify:**
- Level: integration | Given: 3 tasks in DB (2 incomplete, 1 complete) | Action: render `<TasksContainer completed="false" />` | Outcome: useQuery called `getTasks("false")`; 2 tasks rendered; empty list renders without error

**Standards:** S-3, S-4, S-7, S-8, S-9
**Dependencies:** Depends on STEP-14, STEP-15; parallel with STEP-19 scoping tasks

---

### STEP-19: TaskForm component

**Trace:** `[FR-4 -> AC-4.1], [FR-4 -> AC-4.2], [FR-4 -> AC-4.3], [FR-4 -> AC-4.4]`
**Informed by:** AD-7, F-17
**Effort:** S

**Files:**
- `todo-app-migrated/frontend/components/TaskForm.tsx` — create

**Intent:** Blank title guard (AC-4.3) must trim before checking length — `" ".trim().length === 0` is falsy. After successful create (AC-4.4), clear the input AND re-focus it via `inputRef.current?.focus()`. The mutation's `onSuccess` both invalidates the query and calls clear+focus. Do not call the API if title is empty — no error toast needed (same behavior as source app's `submit()` method).

**Implementation guidance:**
1. `'use client'`; `const [title, setTitle] = useState('')`; `const inputRef = useRef<HTMLInputElement>(null)`
2. Mutation: `useMutation({ mutationFn: () => api.createTask(title.trim()), onSuccess: () => { setTitle(''); inputRef.current?.focus(); queryClient.invalidateQueries({ queryKey: ['tasks'] }) } })`
3. `onSubmit`: `e.preventDefault(); if (!title.trim()) return; mutation.mutate()`
4. Escape: `onKeyDown: e.key === 'Escape' && setTitle('')`
5. `autoFocus` on the input (HTML attribute is acceptable here — form loads once, no SSR conflict)
6. Style: full-width input, large font (`text-2xl sm540:text-3xl`), bottom border only (matching source app)

**Verify:**
- Level: unit | Given: TaskForm rendered | Action: submit with empty string | Outcome: createTask NOT called; submit with "Buy milk" → createTask called with "Buy milk"; Escape → input clears

**Standards:** S-3, S-4, S-7, S-8, S-9
**Dependencies:** Depends on STEP-15; parallel with STEP-20, STEP-21

---

### STEP-20: TaskList component + filter tabs

**Trace:** `[FR-5 -> AC-5.1], [FR-6 -> AC-6.1], [FR-6 -> AC-6.2], [FR-6 -> AC-6.3], [FR-6 -> AC-6.4], [FR-11 -> AC-11.1], [FR-11 -> AC-11.2]`
**Informed by:** AD-8, F-18
**Effort:** S

**Files:**
- `todo-app-migrated/frontend/components/TaskList.tsx` — create

**Intent:** Filter tabs are `<Link>` components — no `useSearchParams()` import. The active tab is determined by comparing the `completed` prop (from server page.tsx) to each tab's value. Using `className={completed === undefined ? 'active' : ''}` for "All" tab, `completed === 'false'` for "Active", `completed === 'true'` for "Completed". Responsive: task list items use `text-lg sm540:text-2xl` and `py-3 sm540:py-4` spacing per spec AC-11.2.

**Implementation guidance:**
1. `'use client'` (needs Next.js Link); props: `tasks: Task[], completed: string | undefined, onUpdate, onDelete`
2. Filter tabs: three `<Link>` elements to `/tasks`, `/tasks?completed=false`, `/tasks?completed=true`
3. Active state: compare `completed` prop to tab value; apply Tailwind highlight class (`text-white font-semibold` vs `text-gray-400`)
4. Map tasks to `<TaskItem>` components
5. Empty state: `{tasks.length === 0 && <p className="text-gray-500 text-center py-8">No tasks</p>}`

**Verify:**
- Level: inspection | Given: TaskList.tsx | Action: `grep -n "useSearchParams" components/TaskList.tsx` | Outcome: 0 matches; Link hrefs are `/tasks`, `/tasks?completed=false`, `/tasks?completed=true`

**Standards:** S-3, S-4, S-7, S-9
**Dependencies:** Depends on STEP-18

---

### STEP-21: TaskItem component (toggle, inline edit, delete)

**Trace:** `[FR-7 -> AC-7.1], [FR-7 -> AC-7.2], [FR-7 -> AC-7.3], [FR-8 -> AC-8.1], [FR-8 -> AC-8.2], [FR-8 -> AC-8.3], [FR-8 -> AC-8.4], [FR-8 -> AC-8.5], [FR-9 -> AC-9.1], [FR-9 -> AC-9.2]`
**Informed by:** F-17, F-19, AD-7
**Effort:** L

**Files:**
- `todo-app-migrated/frontend/components/TaskItem.tsx` — create

**Intent:** `useRef + useEffect([isEditing])` for autofocus — not HTML `autoFocus` (SSR-unreliable in React 18 strict mode). Blur handler must check BOTH conditions before saving: `editTitle.trim().length > 0 && editTitle !== task.title` (AC-8.4 and AC-8.5). Escape cancels without save — `onKeyDown` for Escape must call `setIsEditing(false)` and reset `editTitle` to `task.title`. Strikethrough on completed tasks: `line-through text-gray-500` Tailwind classes. All three mutations (`updateCompleted`, `updateTitle`, `deleteTask`) call `invalidateQueries({ queryKey: ['tasks'] })` on success.

**Implementation guidance:**
1. State: `const [isEditing, setIsEditing] = useState(false)`; `const [editTitle, setEditTitle] = useState(task.title)`; `const inputRef = useRef<HTMLInputElement>(null)`
2. `useEffect(() => { if (isEditing) inputRef.current?.focus(); }, [isEditing])`
3. Toggle mutation: `onUpdate({ completed: !task.completed })` — calls parent's PATCH handler
4. Edit save logic (handleSave): `if (editTitle.trim() && editTitle !== task.title) { onUpdate({ title: editTitle.trim() }) }; setIsEditing(false)`
5. Escape: `onKeyDown={(e) => { if (e.key === 'Escape') { setEditTitle(task.title); setIsEditing(false) } }}`
6. `onBlur` calls `handleSave` (note: blur fires before Escape keydown in some browsers — Escape handler must set a `cancelRef` flag or use `onKeyDown` with `e.preventDefault()` to suppress blur save on Escape)
7. Completed styling: `className={task.completed ? 'line-through text-gray-500' : 'text-white'}`
8. Three icon buttons: checkmark (toggle), pencil (edit/cancel), trash (delete) — use emoji or SVG icons; aria-label on all buttons

**Verify:**
- Level: unit | Given: task with title "Buy milk", completed=false | Action: trigger blur with editTitle="" | Outcome: onUpdate NOT called (AC-8.4); trigger blur with editTitle="Buy milk" → onUpdate NOT called (AC-8.5 — unchanged); trigger Escape → setIsEditing(false) and no onUpdate call (AC-8.3); trigger blur with editTitle="Buy groceries" → onUpdate called with { title: "Buy groceries" }

**Standards:** S-3, S-4, S-7, S-8, S-9
**Dependencies:** Depends on STEP-18, STEP-15

---

### STEP-22: Frontend test suite

**Trace:** `MANUAL -> Test for STEP-18, STEP-19, STEP-20, STEP-21`
**Effort:** M

**Files:**
- `todo-app-migrated/frontend/jest.config.ts` — create
- `todo-app-migrated/frontend/jest.setup.ts` — create
- `todo-app-migrated/frontend/components/__tests__/TaskForm.test.tsx` — create
- `todo-app-migrated/frontend/components/__tests__/TaskItem.test.tsx` — create

**Intent:** Mock `lib/api.ts` entirely and `getSession` from `next-auth/react` to return a fixed `accessToken`. Mock `useMutation` to capture the `mutationFn` calls. Test the behavioral invariants from AC-8.3, AC-8.4, AC-8.5, AC-4.3 — these are the non-obvious conditions most likely to regress.

**Implementation guidance:**
1. `jest.config.ts`: `testEnvironment: 'jsdom'`, `setupFilesAfterFramework: ['./jest.setup.ts']`, `moduleNameMapper: { '^@/(.*)$': '<rootDir>/$1' }`
2. `jest.setup.ts`: `import '@testing-library/jest-dom'`
3. `jest.mock('@/lib/api')` at top of each test file; `jest.mock('next-auth/react', () => ({ getSession: () => Promise.resolve({ accessToken: 'test-token' }), useSession: () => ({ data: { accessToken: 'test-token' }, status: 'authenticated' }) }))`
4. `TaskForm.test.tsx`: test empty submit (api.createTask not called), valid submit (called), Escape (state reset)
5. `TaskItem.test.tsx`: blur with empty title (onUpdate not called), blur with unchanged title (not called), Escape (setIsEditing false, no call), blur with changed title (called)

**Verify:**
- Level: unit | Given: test suite | Action: `npm test` from frontend/ | Outcome: all tests pass; TaskItem blur-with-unchanged-title test passes; TaskForm empty-submit test passes

**Standards:** S-3
**Dependencies:** Depends on STEP-19, STEP-21

---

## Bundle B-6: Integration + Documentation

> Stage: integration | Parallel: no (depends on B-2 + B-5) | Files: todo-app-migrated/README.md, todo-app-migrated/backend/README.md, todo-app-migrated/frontend/README.md

**Bundle Verify**: Developer can start both servers from a clean checkout and complete a full sign-in → create task → filter → sign-out flow using the documented steps.
- **Level**: inspection
- **Given**: Fresh clone of todo-app-migrated
- **Action**: Follow README startup instructions; verify each step completes without undocumented steps
- **Outcome**: FastAPI runs on :8000; Next.js runs on :3000; full auth + CRUD flow works

---

### Context Preamble — B-6

**Architecture Decisions:** AD-3 (Twitter/Facebook optional — document add-back instructions)

**Risks:** R-1 (Twitter OAuth 1.0a), R-2 (Facebook HTTPS)

---

### STEP-23: Integration documentation + startup guide

**Trace:** `MANUAL -> Integration verification`
**Effort:** S

**Files:**
- `todo-app-migrated/README.md` — create
- `todo-app-migrated/backend/README.md` — create
- `todo-app-migrated/frontend/README.md` — create

**Intent:** The startup sequence matters — FastAPI must be running before the Next.js app signs in (the `jwt` callback calls FastAPI). OAuth app setup (Google, GitHub) is the most common first-run blocker — document exactly where to create credentials. NEXTAUTH_SECRET generation (`openssl rand -base64 32`) must be explicit.

**Implementation guidance:**
1. Root `README.md`: project overview, monorepo structure, "Quick Start" with prerequisite list (Python 3.11+, Node 18+, OAuth app credentials)
2. `backend/README.md`: setup (`pip install -r requirements.txt`), `.env` configuration, run (`uvicorn app.main:app --reload --port 8000`), test (`pytest tests/`)
3. `frontend/README.md`: setup (`npm install`), `.env.local` from example, OAuth app setup instructions (Google Cloud Console, GitHub OAuth App), run (`npm run dev`), test (`npm test`)
4. Document optional providers (Twitter/Facebook) with links to developer portals and ngrok note for Facebook
5. Verify section: `curl http://localhost:8000/ → {"status": "ok"}`; `curl http://localhost:3000/ → HTML`

**Verify:**
- Level: inspection | Given: README.md complete | Action: read startup section | Outcome: Google OAuth setup instructions present; NEXTAUTH_SECRET generation command present; startup order (backend first) documented

**Dependencies:** Depends on B-2 + B-5 complete (all code written)

---

## Open Questions

*(None — all questions resolved during spec and design phases)*
