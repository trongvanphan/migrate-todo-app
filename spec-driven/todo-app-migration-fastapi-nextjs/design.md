---
slug: todo-app-migration-fastapi-nextjs
spec_source: spec-driven/todo-app-migration-fastapi-nextjs/spec.md
spec_hash: 8da3d3e2298a6b45d4897c6e4c7613a293e24fa52d95d363b7673b8ece40fc1f
status: final
created_date: 2026-05-16T00:00:00Z
last_updated: 2026-05-16T00:00:00Z
version: 1.0
test_approach: test-after
---

# Architectural Design: Todo App Migration — FastAPI + Next.js

**Spec:** `spec-driven/todo-app-migration-fastapi-nextjs/spec.md`
**Target:** `todo-app-migrated/` (greenfield monorepo)

---

## Technical Approach

### Overview

A greenfield implementation in `todo-app-migrated/` organized as a monorepo with two independent sub-projects: `backend/` (Python FastAPI) and `frontend/` (Next.js 14 App Router). No Firebase SDK appears in either project.

### Backend (`todo-app-migrated/backend/`)

Flat `app/` package layout following the FastAPI tutorial convention — right-sized for two routers. SQLite + SQLAlchemy (sync) stores users and tasks; tables are created on startup via `Base.metadata.create_all` in the lifespan context manager. JWT auth uses `python-jose` (HS256, 30-day expiry). All secrets read via `pydantic-settings` BaseSettings from `.env`.

**Auth flow (server-side only):**
- `POST /auth/oauth` — receives `{ provider, provider_id, email, name }` from NextAuth.js server code; upserts user by `(provider, provider_id)`; returns `{ access_token, user_id }`. Called server-to-server; no CORS required.
- `POST /auth/anonymous` — creates a guest user with `provider="anonymous"` and a UUID as `provider_id`; returns `{ access_token, user_id }`. Also server-to-server.
- `get_current_user` dependency — decodes Bearer JWT via `HTTPBearer()`, queries user row, raises 401 on invalid token.

**Task CRUD:**
All four task endpoints (`GET`, `POST`, `PATCH`, `DELETE`) inject `get_current_user` and `get_db`. PATCH and DELETE perform an inline ownership check (`task.user_id == current_user.id`, raises 403 on mismatch). `GET /tasks` accepts an optional `?completed=` query parameter that maps to `filter(Task.completed == value)` when present.

### Frontend (`todo-app-migrated/frontend/`)

Next.js 14 App Router with a deliberate server/client component split. The `app/layout.tsx` is a Server Component that imports a `'use client'` `Providers` wrapper (`app/providers.tsx`) containing `SessionProvider` (NextAuth) and `QueryClientProvider` (TanStack Query v5) side by side.

**Auth flow (NextAuth v5):**
- `auth.ts` at the project root configures Google and GitHub providers (Twitter + Facebook are optional — see Risks). CredentialsProvider handles anonymous sign-in.
- On first sign-in, the `jwt` callback detects `trigger === 'signIn' && account`, calls `POST /auth/oauth` or `POST /auth/anonymous` (server-to-server), and stores the returned FastAPI `access_token` on `token.accessToken`.
- The `session` callback forwards `token.accessToken` to the client-accessible session as `session.accessToken`.
- TypeScript module augmentation in `types/next-auth.d.ts` extends `Session` and `JWT` interfaces.
- `middleware.ts` uses NextAuth v5's `auth` export as middleware, redirecting unauthenticated users from `/tasks` to `/` and authenticated users from `/` to `/tasks`.

**Route: `/` (sign-in page):**
Server Component. Renders a client `SignIn` component with buttons for Google, GitHub, and "Continue as guest". Google/GitHub call `signIn('google'|'github')`. Anonymous calls `signIn('credentials', { redirect: false })` then `router.push('/tasks')`.

**Route: `/tasks` (task management):**
`app/tasks/page.tsx` is a Server Component that reads `searchParams.completed` synchronously and passes it as a prop to `TasksContainer` (`'use client'`). This eliminates the need for `useSearchParams()` and its Suspense requirement.

`TasksContainer` holds all data-fetching logic via TanStack Query:
- `useQuery({ queryKey: ['tasks', completed], queryFn: () => api.getTasks(completed) })` — fetches tasks from FastAPI.
- Mutations (create, update, delete) call `useMutation` and on success call `queryClient.invalidateQueries({ queryKey: ['tasks'] })` (refetch-after-mutate pattern — no optimistic updates).

`lib/api.ts` is the single typed fetch wrapper. Each exported function calls `getSession()` internally to retrieve `session.accessToken`, attaches `Authorization: Bearer <token>`, and calls FastAPI.

**Filter tabs:** `TaskList` renders three `<Link>` components (`/tasks`, `/tasks?completed=false`, `/tasks?completed=true`). Next.js re-renders `page.tsx` on navigation, passing the new `searchParams` to `TasksContainer`, which triggers a new `useQuery` fetch. No `useSearchParams()` or `router.push()` needed.

**Responsive layout (FR-11):** Tailwind CSS mobile-first approach. Base styles target mobile (≥320px). The `sm:` breakpoint (640px, closest Tailwind default to the spec's 540px target) applies larger font sizes and spacing: `text-lg sm:text-2xl` on task titles, `h-12 sm:h-16` on the task form input, `py-4 sm:py-6` padding on containers. If 540px precision is required, add a custom `screens.md540` value to `tailwind.config.ts`. All interactive elements (buttons, inputs) are full-width on mobile.

**Inline edit (TaskItem):** `isEditing` boolean state controls mode. On entering edit mode, a `useRef` + `useEffect([isEditing])` focuses the input imperatively — mirrors the Angular `AutoFocusDirective.ngOnInit()`. Blur saves (if title changed + non-empty), Escape cancels, Enter submits.

---

## Findings

| ID | Title | Source | Confidence | FRs |
|---|---|---|---|---|
| F-1 | NextAuth.js v5 is the correct choice for Next.js 14 App Router (native `auth()` function, no adapter needed) | training_knowledge | high | FR-1, FR-2, FR-3 |
| F-2 | FastAPI JWT exchange must happen in the NextAuth `jwt` callback with `trigger === 'signIn' && account` guard | training_knowledge | high | FR-1, FR-2 |
| F-3 | FastAPI `access_token` stored inside the NextAuth encrypted session cookie (JWE); exposed via `session` callback | training_knowledge | high | FR-1, FR-10 |
| F-4 | Server Components use `auth()`; Client Components use `useSession()`; API calls use shared `lib/api.ts` with `getSession()` | training_knowledge | high | FR-1, FR-4, FR-5 |
| F-5 | Anonymous auth: `CredentialsProvider.authorize` calls `POST /auth/anonymous`, returns FastAPI token on user object; `jwt` callback stores it | training_knowledge | high | FR-1 |
| F-6 | Auth exchange endpoints (`/auth/oauth`, `/auth/anonymous`) are server-to-server — no CORS needed; CORS only required for task CRUD browser calls | training_knowledge | high | FR-10 |
| F-7 | TypeScript module augmentation (`types/next-auth.d.ts`) required to type `session.accessToken` and `token.accessToken` | training_knowledge | high | FR-1 |
| F-8 | Flat `app/` package layout with `routers/` subdirectory is right-sized for 2 routers (matches FastAPI tutorial) | training_knowledge | high | FR-4–FR-10 |
| F-9 | Sync SQLAlchemy + `check_same_thread=False` for SQLite; FastAPI runs sync dependencies in a threadpool automatically | training_knowledge | high | FR-10 |
| F-10 | `HTTPBearer()` + `python-jose` for JWT extraction dependency; OAuth2PasswordBearer is semantically wrong for this architecture | training_knowledge | high | FR-4–FR-10 |
| F-11 | Inline ownership check in PATCH/DELETE handlers (fetch task → compare `user_id` → raise 403); separate dependency is over-engineering for 2 endpoints | training_knowledge | high | FR-7, FR-9, FR-10 |
| F-12 | Pydantic v2 with `ConfigDict(from_attributes=True)` on ORM response schemas; `model_config` replaces `class Config` | training_knowledge | high | FR-5 |
| F-13 | `CORSMiddleware` with `allow_credentials=True` and explicit `allow_origins` list (not `'*'`) | training_knowledge | high | FR-10 |
| F-14 | `Base.metadata.create_all(bind=engine)` in FastAPI lifespan context manager; Alembic is premature for SQLite greenfield | training_knowledge | high | FR-10 |
| F-15 | Upsert user by `(provider, provider_id)` — not email; email is mutable and non-unique across providers | training_knowledge | high | FR-1, FR-10 |
| F-16 | `app/tasks/page.tsx` is a Server Component reading `searchParams.completed`; renders `TasksContainer` (`'use client'`) as a prop-receiving child | training_knowledge | high | FR-5, FR-6 |
| F-17 | TanStack Query v5 refetch-after-mutate via `queryClient.invalidateQueries({ queryKey: ['tasks'] })`; no optimistic updates | training_knowledge | high | FR-7, FR-8, FR-9 |
| F-18 | Filter tabs use `<Link>` components pointing to full URLs; avoids `useSearchParams()` and its Suspense requirement | training_knowledge | high | FR-6 |
| F-19 | `useRef` + `useEffect([isEditing])` for autoFocus on edit input — SSR-safe, mirrors Angular `AutoFocusDirective.ngOnInit()` | training_knowledge | high | FR-8 |
| F-20 | `SessionProvider` + `QueryClientProvider` co-located in `app/providers.tsx` (`'use client'`); `QueryClient` initialized with `useState` to prevent recreation | training_knowledge | high | FR-1, FR-5 |

---

## Architecture Decisions

### AD-1: NextAuth.js v5 over v4

**Context:** The frontend needs OAuth sign-in (Google, GitHub) and anonymous auth. Next.js 14 App Router is the target.

**Decision:** Use NextAuth.js v5 (`next-auth@5`).

**Rationale:** v5 was designed specifically for the App Router. The `auth()` function works directly in Server Components, Route Handlers, and middleware without adapter configuration. v4 is in maintenance mode and requires `getServerSession(authOptions)` prop-drilling. Since this is greenfield there is no upgrade cost.

**Alternatives considered:**
- *NextAuth v4* — Works with App Router via compatibility shim, more documentation available, but maintenance-mode and `authOptions` prop-drilling is boilerplate.
- *Auth0 / Clerk* — Hosted auth services; out of scope (spec says full replacement with NextAuth.js).

---

### AD-2: FastAPI JWT Exchange in `jwt` Callback

**Context:** NextAuth handles OAuth; FastAPI must issue its own JWT for API authorization.

**Decision:** Call `POST /auth/oauth` (or `POST /auth/anonymous` for guests) inside NextAuth's `jwt` callback when `trigger === 'signIn' && account`. Store the returned `access_token` as `token.accessToken`. Expose it client-side via the `session` callback.

**Rationale:** The `jwt` callback is the only correct point: it runs server-side, has access to provider account data, and can write to the encrypted session cookie atomically. Client-side exchange creates a race condition where the first API request fires before the token is available.

**Alternatives considered:**
- *`signIn` callback* — Cannot write to the JWT; no mechanism to pass data to `jwt`.
- *Client-side exchange (useEffect/React Query)* — Race condition on first authenticated render.
- *Next.js Server Action after sign-in* — Cannot update NextAuth's cookie; race condition remains.

---

### AD-3: OAuth Providers — Google + GitHub Only (Initial)

**Context:** Spec FR-1 requires 5 providers (Google, GitHub, Twitter, Facebook, anonymous). Research found Twitter OAuth 1.0a complexity and Facebook HTTPS requirement create meaningful local dev friction.

**Decision:** Implement Google, GitHub, and anonymous for the initial migration. Document Twitter and Facebook as optional providers with configuration notes.

**Rationale:** The architecture is provider-agnostic — adding Twitter or Facebook is a config change (add provider to `auth.ts`, add env vars). The core auth exchange pattern (AD-2) works identically for all providers. The user confirmed this scoping decision.

**To add Twitter:** Install `next-auth/providers/twitter`, add `TWITTER_CLIENT_ID` and `TWITTER_CLIENT_SECRET` (OAuth 1.0a credentials from Twitter Developer Portal), add to providers array.

**To add Facebook:** Requires HTTPS callback URL — use `ngrok` for local dev or configure Facebook App's "Valid OAuth Redirect URIs" to include `https://<ngrok-url>/api/auth/callback/facebook`. Add `FACEBOOK_CLIENT_ID` and `FACEBOOK_CLIENT_SECRET`.

---

### AD-4: Sync SQLAlchemy + `create_all` in Lifespan

**Context:** FastAPI backend uses SQLite; spec is dev/demo scale.

**Decision:** Use sync SQLAlchemy with a `get_db` generator dependency. Initialize tables with `Base.metadata.create_all(bind=engine)` inside a `@asynccontextmanager` lifespan function.

**Rationale:** SQLite's write serialization means async provides no throughput benefit. FastAPI runs sync `Depends()` in a threadpool automatically. `create_all` is idempotent and eliminates migration tooling overhead for this scale.

**Alternatives considered:**
- *Async SQLAlchemy + aiosqlite* — No throughput benefit for SQLite; significantly more complex.
- *Alembic migrations* — Valuable for production schema evolution with live data; premature for greenfield SQLite.

---

### AD-5: `HTTPBearer` JWT Dependency Injection

**Context:** All task endpoints require authentication. FastAPI must extract and validate the Bearer JWT.

**Decision:** Use `fastapi.security.HTTPBearer()` with a `get_current_user(credentials, db)` dependency that decodes the JWT via `python-jose`, fetches the user row, and returns it. Inject via `Depends(get_current_user)` on all task router endpoints.

**Rationale:** `HTTPBearer` extracts Bearer tokens without semantic assumptions about the auth flow. Returns a full ORM `User` object to handlers, enabling ownership checks without extra queries.

**Alternatives considered:**
- *`OAuth2PasswordBearer`* — Designed for password grant flow; semantically incorrect for token-pass-through from NextAuth.
- *Manual header parsing* — Duplicates what `HTTPBearer` provides.

---

### AD-6: Server Page + Client Container Component Boundary

**Context:** Next.js App Router tasks page must support URL-driven filter state and authenticated data fetching.

**Decision:** `app/tasks/page.tsx` is a Server Component that reads `searchParams.completed` synchronously and passes it as a prop to `TasksContainer` (`'use client'`). `TasksContainer` holds all `useQuery`/`useMutation` logic.

**Rationale:** Server Component reading `searchParams` eliminates `useSearchParams()` and its required Suspense boundary. `TasksContainer` receiving `completed` as a prop means filtering re-triggers via Next.js navigation (Link click → page re-render → new prop → new `useQuery` fetch). No client-side URL state management needed.

**Alternatives considered:**
- *Full client page* — Loses server-side searchParams access; requires Suspense.
- *Server prefetch + HydrationBoundary* — Better performance but overkill for authenticated CRUD; adds significant boilerplate.

---

### AD-7: Refetch-after-mutate (No Optimistic Updates)

**Context:** Task mutations (create, update, delete) must update the task list.

**Decision:** All mutations call `queryClient.invalidateQueries({ queryKey: ['tasks'] })` on success. No optimistic update logic.

**Rationale:** The FastAPI backend on localhost:8000 responds well under 200ms. Optimistic updates require rollback logic on error and complex cache manipulation — significant complexity without meaningful UX benefit for this app. Matches the Angular source's behavior (Firebase real-time sync; no optimistic pattern was needed there either).

**Alternatives considered:**
- *Optimistic updates* — Instant UI feedback but rollback complexity; risk of state inconsistency on error.

---

### AD-8: Filter Tabs via `<Link>` Components (No `useSearchParams`)

**Context:** Three filter tabs (All / Active / Completed) must reflect their state in the URL and trigger filtered data fetches.

**Decision:** Filter tabs are `<Link href='/tasks'>`, `<Link href='/tasks?completed=false'>`, `<Link href='/tasks?completed=true'>`. Active state determined by comparing the prop `completed` (passed from server page) to the tab's value.

**Rationale:** Next.js `Link` handles navigation; the resulting URL change causes `page.tsx` to re-render with new `searchParams`, which passes a new `completed` prop to `TasksContainer`, which triggers a new `useQuery` fetch. No `useSearchParams()`, no Suspense, no `router.push()`.

---

## Standards

| ID | Rule | Domain | Applies To |
|---|---|---|---|
| S-1 | No Firebase SDK in either `frontend/` or `backend/` | dependency | All files |
| S-2 | All secrets in `.env` / `.env.local`; never committed | config | backend/.env, frontend/.env.local |
| S-3 | All frontend files in TypeScript (`.ts`, `.tsx`); strict mode enabled | language | frontend/ |
| S-4 | Styling via Tailwind CSS utility classes only; no custom CSS files except `globals.css` for Tailwind directives | styling | frontend/app/, frontend/components/ |
| S-5 | Pydantic v2 `ConfigDict(from_attributes=True)` on all ORM response schemas | backend | backend/app/schemas.py |
| S-6 | FastAPI route handlers never manage DB session lifecycle — use `Depends(get_db)` | backend | backend/app/routers/ |
| S-7 | `'use client'` directive only on components that use hooks, browser APIs, or event handlers | frontend | frontend/app/, frontend/components/ |
| S-8 | All TanStack Query mutations call `invalidateQueries({ queryKey: ['tasks'] })` on success | frontend | frontend/components/ |
| S-9 | `lib/api.ts` is the single point of FastAPI communication; no `fetch()` calls outside it | frontend | frontend/lib/ |
| S-10 | JWT `sub` claim is `str(user.id)`; decode as `int(payload['sub'])` | backend | backend/app/dependencies.py |

---

## File Inventory

### Backend (`todo-app-migrated/backend/`)

| File | Action | FRs | Notes |
|---|---|---|---|
| `requirements.txt` | CREATE | all | fastapi, uvicorn[standard], sqlalchemy, python-jose[cryptography], pydantic-settings, python-dotenv |
| `.env` | CREATE | all | SECRET_KEY, DATABASE_URL, CORS_ORIGINS |
| `.env.example` | CREATE | all | Template with placeholder values |
| `app/__init__.py` | CREATE | all | Empty package init |
| `app/main.py` | CREATE | all | FastAPI app + lifespan + CORSMiddleware + router mounts |
| `app/config.py` | CREATE | all | `pydantic-settings` BaseSettings — reads SECRET_KEY, DATABASE_URL, CORS_ORIGINS |
| `app/database.py` | CREATE | all | SQLAlchemy engine, SessionLocal, Base, `get_db` dependency |
| `app/models.py` | CREATE | FR-1, FR-4–FR-10 | `User` and `Task` ORM models |
| `app/schemas.py` | CREATE | FR-1, FR-4–FR-10 | Pydantic v2: OAuthLogin, AnonymousResponse, TokenResponse, TaskCreate, TaskUpdate, TaskOut |
| `app/dependencies.py` | CREATE | FR-1–FR-10 | `get_current_user` (HTTPBearer + JWT decode + user query) |
| `app/routers/__init__.py` | CREATE | — | Empty |
| `app/routers/auth.py` | CREATE | FR-1, FR-2 | `POST /auth/oauth`, `POST /auth/anonymous` |
| `app/routers/tasks.py` | CREATE | FR-4–FR-10 | `GET /tasks`, `POST /tasks`, `PATCH /tasks/{id}`, `DELETE /tasks/{id}` |

### Frontend (`todo-app-migrated/frontend/`)

| File | Action | FRs | Notes |
|---|---|---|---|
| `package.json` | CREATE | all | next@14, next-auth@5, @tanstack/react-query@5, typescript, tailwindcss |
| `tsconfig.json` | CREATE | all | strict mode, path aliases (`@/`) |
| `tailwind.config.ts` | CREATE | FR-11 | Content paths covering app/ and components/ |
| `.env.local` | CREATE | all | NEXTAUTH_SECRET, AUTH_SECRET, NEXTAUTH_URL, NEXT_PUBLIC_API_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET |
| `.env.local.example` | CREATE | all | Template |
| `auth.ts` | CREATE | FR-1–FR-3 | NextAuth v5 config: Google, GitHub, CredentialsProvider, jwt/session callbacks |
| `middleware.ts` | CREATE | FR-3 | Auth middleware: redirect /tasks → / if unauth; / → /tasks if auth |
| `types/next-auth.d.ts` | CREATE | FR-1 | Module augmentation: `Session.accessToken`, `JWT.accessToken`, `User.anonymousToken` |
| `lib/api.ts` | CREATE | FR-4–FR-10 | Typed fetch wrapper: getTasks, createTask, updateTask, deleteTask |
| `app/globals.css` | CREATE | FR-11 | Tailwind directives only (@tailwind base/components/utilities) |
| `app/layout.tsx` | CREATE | FR-1–FR-3 | Server Component root layout; imports Providers |
| `app/providers.tsx` | CREATE | FR-1, FR-5 | `'use client'`: SessionProvider + QueryClientProvider |
| `app/page.tsx` | CREATE | FR-1–FR-3 | Sign-in page (Server Component); renders `SignIn` client component |
| `app/tasks/page.tsx` | CREATE | FR-5, FR-6 | Server Component; reads `searchParams.completed`; renders `TasksContainer` |
| `app/api/auth/[...nextauth]/route.ts` | CREATE | FR-1–FR-3 | NextAuth v5 route handler |
| `components/SignIn.tsx` | CREATE | FR-1, FR-2 | `'use client'`: Google/GitHub/Guest sign-in buttons |
| `components/Header.tsx` | CREATE | FR-2, FR-3 | `'use client'`: `useSession()`, sign-out button |
| `components/TasksContainer.tsx` | CREATE | FR-4–FR-10 | `'use client'`: useQuery, mutations, renders TaskForm + TaskList |
| `components/TaskForm.tsx` | CREATE | FR-4 | `'use client'`: controlled input, Enter submits, Escape clears |
| `components/TaskList.tsx` | CREATE | FR-5, FR-6 | `'use client'`: filter tabs (Link) + task list |
| `components/TaskItem.tsx` | CREATE | FR-7, FR-8, FR-9 | `'use client'`: toggle, inline edit (useRef autoFocus), delete |

---

## Dependencies and Coupling

| Dependency | From | To | Notes |
|---|---|---|---|
| Auth token exchange | `auth.ts` (jwt callback) | `POST /auth/oauth`, `POST /auth/anonymous` | Server-to-server; no CORS needed |
| Session token access | `lib/api.ts` | `useSession()` / `getSession()` | All API calls go through api.ts; single coupling point |
| Task query key | `TasksContainer` + `TaskForm` + `TaskItem` | `['tasks', completed?]` | All mutations invalidate this key; coupling intentional |
| DB models shared | `app/routers/auth.py` + `app/routers/tasks.py` | `app/models.py` | Both routers import User and Task from models.py |
| Settings singleton | All backend modules | `app/config.py` | `from app.config import settings` in database.py, dependencies.py, routers |
| `get_current_user` depends on `get_db` | `app/dependencies.py` | `app/database.py` | Dependency chain: route handler → get_current_user → get_db |

**Recommended task sequencing:** Build backend first (auth endpoints, then task endpoints) so the frontend has a running API to test against. Within the frontend, implement auth flow before task CRUD.

---

## Spec Deviations

| Field | Spec Value | Design Value | Rationale |
|---|---|---|---|
| Auth providers (initial) | 5 (Google, GitHub, Twitter, Facebook, Anonymous) | 3 (Google, GitHub, Anonymous) | Twitter OAuth 1.0a complexity + Facebook HTTPS requirement create local dev friction; architecture is provider-agnostic, Twitter/Facebook can be added via config |

All other spec values preserved.

---

## Resolved Uncertainties

| Question | Answer |
|---|---|
| NextAuth v5 supports all 4 OAuth providers? | Yes — Google, GitHub, Twitter, Facebook all ship as first-party providers |
| Session maxAge alignment | Set `session: { maxAge: 30 * 24 * 60 * 60 }` in NextAuth config to match FastAPI 30-day JWT expiry |
| CredentialsProvider + App Router | Works; requires `signIn('credentials', { redirect: false })` from client + manual `router.push('/tasks')` |
| CSRF risk with Bearer auth | Not a concern — custom `Authorization` headers are not auto-sent by browsers cross-origin |
| `POST /auth/oauth` payload | Sends identity claims `{ provider, provider_id, email, name }` only — not the OAuth provider's access_token |
| `useSearchParams` Suspense requirement | Avoided by reading `searchParams` server-side in `page.tsx` and passing as prop |

---

## Constraints (Technical)

| ID | Constraint | Source | Rationale |
|---|---|---|---|
| C-1 | SQLite writes are serialized — not suitable for concurrent multi-user production load | technical | SQLite locking behavior; acceptable for dev/demo scale per spec |
| C-2 | Facebook OAuth requires HTTPS callback URI — use ngrok or configure Facebook App for localhost | technical | Facebook Developer Portal enforces HTTPS even in dev for browser-based OAuth |
| C-3 | `CredentialsProvider` does not support redirect-based flows — `redirect: false` required | technical | NextAuth CredentialsProvider documentation constraint |
| C-4 | NextAuth v5 session cookie size — FastAPI JWT (~200 bytes) + user info must stay under 4KB cookie limit | technical | Browser cookie size limit; easily satisfied for this data model |

---

## Assumptions

| ID | Assumption | Affects |
|---|---|---|
| A-1 | Developer provisions OAuth app credentials for Google and GitHub before running | FR-1 |
| A-2 | Next.js dev server runs on port 3000; FastAPI on port 8000 | FR-1, FR-4–FR-10 |
| A-3 | `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local`; configurable for production | FR-4–FR-10 |
| A-4 | `AUTH_SECRET` / `NEXTAUTH_SECRET` is a random 32-byte value generated by the developer | FR-1 |

---

## Risks (Technical)

| ID | Risk | Impact | Probability | Mitigation |
|---|---|---|---|---|
| R-1 | Twitter OAuth 1.0a requires different credential type and callback handling than OAuth 2.0 | medium | medium | Deferred to optional; document provider config steps in README |
| R-2 | Facebook OAuth requires HTTPS redirect URI blocking local dev without ngrok | medium | high | Deferred to optional; note ngrok workaround in README |
| R-3 | NextAuth v5 API may have undocumented breaking changes vs published docs (still maturing) | low | low | Pin to specific patch version in `package.json`; check release notes before upgrade |

---

## Test Approach

**Resolved:** `test-after` — greenfield project, no test framework pre-configured.

**Recommended setup (not blocking implementation):**
- **Backend:** `pytest` + `httpx` (for FastAPI `TestClient`). Unit test auth token creation/validation; integration test task CRUD with in-memory SQLite.
- **Frontend:** `jest` + `@testing-library/react` for component unit tests. `playwright` or `cypress` for E2E sign-in + task flows.

---

## Open Questions

*(None — all questions resolved during research and design phases)*
