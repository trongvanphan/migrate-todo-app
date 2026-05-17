# E2E Flow: Migrating Angular Firebase App → FastAPI + Next.js

> A step-by-step guide for reproducing the full migration from `todo-angular-firebase-demo/` to `todo-app-migrated/`. Written for a junior developer.

---

## Big Picture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MIGRATION PIPELINE                               │
│                                                                         │
│   SOURCE                          TARGET                                │
│  Angular 4          ──────►   FastAPI + Next.js                        │
│  Firebase Auth                NextAuth.js (Google, GitHub, Guest)       │
│  Firebase RTDB                SQLite + SQLAlchemy                       │
│  AngularFire SDK               TanStack Query + Bearer JWT              │
└─────────────────────────────────────────────────────────────────────────┘

WORKFLOW (6 phases):

  ┌───────────┐   ┌───────────┐   ┌───────────┐
  │  PHASE 1  │   │  PHASE 2  │   │  PHASE 3  │
  │  Analyze  │──►│   Spec    │──►│  Design   │
  │  Legacy   │   │  (spec.md)│   │(design.md)│
  └───────────┘   └───────────┘   └─────┬─────┘
                                        │
  ┌───────────┐   ┌───────────┐         ▼
  │  PHASE 6  │   │  PHASE 5  │   ┌───────────┐
  │  Verify   │◄──│  Execute  │◄──│  PHASE 4  │
  │(verify.md)│   │  (code)   │   │   Tasks   │
  └───────────┘   └───────────┘   │(tasks.md) │
                                  └───────────┘
```

---

## Repository Structure

```
migrate-todo-app/                   ← outer git repo (this repo)
├── CLAUDE.md
├── todo-angular-firebase-demo/     ← source app (DO NOT MODIFY)
├── todo-app-migrated/              ← inner git repo — your output goes here
│   ├── backend/                    ← FastAPI
│   └── frontend/                   ← Next.js
└── spec-driven/
    └── todo-app-migration-fastapi-nextjs/
        ├── spec.md
        ├── design.md
        ├── tasks.md
        └── verify-report.md
```

---

## Prerequisites

Before starting, make sure you have:

| Tool | Version | Check command |
|------|---------|---------------|
| Python | 3.10+ | `python3 --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| Git | any | `git --version` |

You will also need later (for OAuth testing):
- A **Google Cloud Console** project with OAuth 2.0 credentials
- A **GitHub OAuth App** (github.com → Settings → Developer Settings → OAuth Apps)

---

## Phase 1 — Analyze the Legacy App

**Goal:** Understand what the original Angular app does before writing a single line of new code.

```
todo-angular-firebase-demo/
├── src/app/
│   ├── firebase/          ← Firebase init (AngularFire2)
│   ├── auth/              ← AuthService + 5 OAuth providers
│   └── tasks/             ← CRUD + filter (ReplaySubject)
```

### Steps

1. Read the source app entry point:
   ```bash
   cat todo-angular-firebase-demo/src/app/app.module.ts
   ```

2. Identify the **data model** — tasks live at `/tasks/{uid}/{taskKey}` in Firebase Realtime DB.  
   Each task has at minimum: `{ title: string, completed: boolean }`

3. Identify the **auth providers**: Google, GitHub, Twitter, Facebook, Anonymous (5 total).

4. Identify the **filter mechanism**: `ReplaySubject<filter>` + `switchMap` + `orderByChild('completed')`.

5. Note what the migrated app will **NOT** include (out of scope):
   - Twitter / Facebook OAuth (deferred — complexity + HTTPS requirements)
   - Data migration from Firebase
   - CI/CD pipeline

**Outcome:** You know *what* to build before you design *how* to build it.

---

## Phase 2 — Write the Specification

**Goal:** Produce `spec.md` — a formal list of requirements with acceptance criteria.

### Steps

1. Create the output directory:
   ```bash
   mkdir -p spec-driven/todo-app-migration-fastapi-nextjs
   ```

2. Write `spec.md` with this structure:

```
spec.md
├── Functional Requirements (FR-1 to FR-11)
│   ├── FR-1: Sign in with Google / GitHub / Guest
│   ├── FR-2: Sign out
│   ├── FR-3: Redirect unauthenticated users to sign-in page
│   ├── FR-4: Create a task
│   ├── FR-5: View tasks list
│   ├── FR-6: Filter tasks (All / Active / Completed)
│   ├── FR-7: Toggle task completion
│   ├── FR-8: Edit task title (inline)
│   ├── FR-9: Delete a task
│   ├── FR-10: Per-user data isolation
│   └── FR-11: Responsive layout (540px breakpoint)
│
├── Acceptance Criteria (34 total, Given/When/Then format)
│   Example:
│   AC-4.3: Given the task form is open,
│            When the user submits an empty or whitespace-only title,
│            Then no task is created and an error is shown.
│
└── Non-Functional Requirements
    ├── NFR-1: API response < 200ms (local SQLite)
    ├── NFR-2: JWT valid for 30 days
    └── NFR-3: HTTPS in production (deferred for local dev)
```

3. Also document the **target DB schema** and **API surface** in spec.md:

```sql
-- users table
id          INTEGER PRIMARY KEY
provider    TEXT    -- "google" | "github" | "anonymous"
provider_id TEXT    -- unique per provider
email       TEXT

-- tasks table
id          INTEGER PRIMARY KEY
user_id     INTEGER REFERENCES users(id)
title       TEXT    NOT NULL
completed   BOOLEAN DEFAULT FALSE
created_at  DATETIME DEFAULT now()
```

```
API endpoints:
POST   /auth/oauth         ← sign in with Google/GitHub
POST   /auth/anonymous     ← guest sign-in
GET    /tasks              ← list tasks (optional ?completed=true/false)
POST   /tasks              ← create task
PATCH  /tasks/{id}         ← update title or completion
DELETE /tasks/{id}         ← delete task
```

**Outcome:** `spec-driven/todo-app-migration-fastapi-nextjs/spec.md` is complete.

---

## Phase 3 — Architectural Design

**Goal:** Decide *how* to implement each requirement. Produce `design.md`.

### Key Architecture Decisions (ADs)

```
┌───────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE DECISIONS                     │
│                                                               │
│  AD-1: Auth layer → NextAuth v5 + FastAPI JWT exchange        │
│  AD-2: Database  → SQLite + SQLAlchemy (no async needed)      │
│  AD-3: Twitter/Facebook deferred (complexity + HTTPS)         │
│  AD-4: Pydantic v2 with ConfigDict(from_attributes=True)      │
│  AD-5: create_all in lifespan (not Alembic — SQLite greenfield│
│  AD-6: Server page.tsx + client TasksContainer pattern        │
│  AD-7: Refetch-after-mutate (no optimistic updates)           │
│  AD-8: Link-based filter tabs (no useSearchParams)            │
└───────────────────────────────────────────────────────────────┘
```

### Critical Design Decisions Explained

**AD-1: How NextAuth talks to FastAPI**

```
User clicks "Sign in with Google"
        │
        ▼
NextAuth.js handles OAuth redirect
        │
        ▼
  jwt() callback fires
  (trigger === 'signIn' && account)
        │
        ▼
  POST /auth/oauth  ←── sends { provider, provider_id, email }
        │
        ▼
  FastAPI returns { access_token, user_id }
        │
        ▼
  Token stored in NextAuth encrypted session cookie (JWE)
        │
        ▼
  All API calls use:  Authorization: Bearer <access_token>
```

> ⚠️ **Why jwt() not signIn()?** The `signIn` callback cannot write to the NextAuth JWT. The token exchange MUST happen in the `jwt` callback.

**AD-6: Server page + Client container pattern**

```
app/tasks/page.tsx  (Server Component)
    │
    │  reads searchParams.completed synchronously
    │  passes it as a prop ↓
    │
    ▼
TasksContainer.tsx  ('use client')
    │
    │  uses useQuery(['tasks', completed])
    │  handles mutations
    ▼
  TaskList, TaskItem, TaskForm
```

> ⚠️ This avoids needing `useSearchParams()` + `<Suspense>` entirely.

**Outcome:** `spec-driven/todo-app-migration-fastapi-nextjs/design.md` is complete.

---

## Phase 4 — Task Decomposition

**Goal:** Break the design into small, executable steps organized by bundle.

### Bundle Map

```
┌──────────────┐    ┌──────────────────────┐
│   B-1        │    │   B-3                │
│  Backend     │    │   Frontend           │
│  Foundation  │    │   Infrastructure     │
│  (STEP 1-6)  │    │   (STEP 10-12)       │
└──────┬───────┘    └──────────┬───────────┘
       │                       │
       ▼                       ▼
┌──────────────┐    ┌──────────────────────┐
│   B-2        │    │   B-4                │
│  Backend     │    │   Frontend Auth Flow │
│  Task API    │    │   (STEP 13-17)       │
│  (STEP 7-9)  │    └──────────┬───────────┘
└──────┬───────┘               │
       │                       ▼
       │            ┌──────────────────────┐
       │            │   B-5                │
       │            │   Frontend Task UI   │
       │            │   (STEP 18-22)       │
       │            └──────────┬───────────┘
       │                       │
       └──────────┬────────────┘
                  ▼
       ┌──────────────────────┐
       │   B-6                │
       │   Integration + Docs │
       │   (STEP 23)          │
       └──────────────────────┘

Parallel:  B-1 ║ B-3
Sequential: → B-2 → B-4 → B-5 → B-6
```

**Outcome:** `spec-driven/todo-app-migration-fastapi-nextjs/tasks.md` is complete.

---

## Phase 5 — Code Execution

**Goal:** Write all the code, following the bundle order above.

### Step-by-step file creation

#### Bundle 1 — Backend Foundation (STEP 1–6)

```bash
cd todo-app-migrated
mkdir -p backend/app/routers backend/tests
```

Create files in this order:

| File | What it does |
|------|-------------|
| `backend/requirements.txt` | fastapi, uvicorn, sqlalchemy, python-jose, pydantic-settings, httpx, pytest |
| `backend/.env.example` | Template for SECRET_KEY, DATABASE_URL |
| `backend/app/config.py` | `Settings(BaseSettings)` reading from `.env` |
| `backend/app/database.py` | SQLAlchemy engine, `get_db` generator |
| `backend/app/models.py` | `User` + `Task` ORM models |
| `backend/app/schemas.py` | Pydantic v2 schemas (OAuthLogin, TaskCreate, TaskOut, etc.) |
| `backend/app/dependencies.py` | `get_current_user` — validates Bearer JWT, returns User |
| `backend/app/main.py` | FastAPI app + lifespan (create_all) + CORS |
| `backend/app/routers/auth.py` | `POST /auth/oauth` and `POST /auth/anonymous` |

**Key detail — `config.py`:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str = "sqlite:///./todo.db"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30

    class Config:
        env_file = ".env"
```

**Key detail — JWT dependency:**
```python
# dependencies.py
from fastapi.security import HTTPBearer

security = HTTPBearer()

def get_current_user(token: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token.credentials, settings.SECRET_KEY, algorithms=["HS256"])
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise HTTPException(401)
        return user
    except Exception:
        raise HTTPException(401, "Invalid token")
```

---

#### Bundle 3 — Frontend Infrastructure (STEP 10–12)

```bash
cd todo-app-migrated
npx create-next-app@14 frontend --typescript --tailwind --app --no-src-dir --no-import-alias
cd frontend
npm install next-auth@5 @tanstack/react-query@5 @tanstack/react-query-devtools
```

Create/update these files:

| File | What it does |
|------|-------------|
| `frontend/tailwind.config.ts` | Add custom `sm540: "540px"` breakpoint |
| `frontend/app/layout.tsx` | Server root layout (no 'use client') |
| `frontend/app/providers.tsx` | `'use client'` — wraps SessionProvider + QueryClientProvider |
| `frontend/types/next-auth.d.ts` | Augments Session with `accessToken`, JWT with `accessToken` |

**Key detail — `providers.tsx`:**
```tsx
'use client'
import { SessionProvider } from 'next-auth/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient())
  return (
    <SessionProvider>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </SessionProvider>
  )
}
```

> ⚠️ The `useState` guard is required — it ensures a new `QueryClient` is created per-render boundary without being re-created on every render.

---

#### Bundle 2 — Backend Task Endpoints (STEP 7–9)

| File | What it does |
|------|-------------|
| `backend/app/routers/tasks.py` | `GET/POST/PATCH/DELETE /tasks` with ownership check |
| `backend/tests/conftest.py` | In-memory SQLite test DB + dependency override |
| `backend/tests/test_auth.py` | Tests: upsert, anonymous, invalid token |
| `backend/tests/test_tasks.py` | Tests: isolation, filter, ownership, delete |

**Key detail — ownership check (prevents ID enumeration):**
```python
# WRONG — leaks task existence to unauthorized users:
task = db.query(Task).filter(Task.id == task_id).first()  # 404 if missing
if task.user_id != current_user.id: raise HTTPException(403)  # 403 reveals task exists!

# CORRECT — single combined query:
task = db.query(Task).filter(
    Task.id == task_id,
    Task.user_id == current_user.id   # ← ownership check combined
).first()
if task is None:
    raise HTTPException(404)  # same 404 for "not found" AND "not yours"
```

**Run backend tests:**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
# Expected: 15 passed
```

---

#### Bundle 4 — Frontend Auth Flow (STEP 13–17)

| File | What it does |
|------|-------------|
| `frontend/auth.ts` | NextAuth v5 config: Google, GitHub, CredentialsProvider (anonymous) |
| `frontend/app/api/auth/[...nextauth]/route.ts` | Re-exports NextAuth handlers |
| `frontend/middleware.ts` | Route guard: `/tasks` → `/` if unauth; `/` → `/tasks` if auth |
| `frontend/lib/api.ts` | Typed fetch wrapper: injects `Authorization: Bearer` from session |
| `frontend/components/SignIn.tsx` | Sign-in buttons: Google, GitHub, Guest |
| `frontend/components/Header.tsx` | Sign-out button |

**Key detail — `auth.ts` JWT callback:**
```typescript
callbacks: {
  async jwt({ token, account, user }) {
    // Only run token exchange on initial sign-in
    if (account && user) {
      if (account.provider === 'credentials') {
        // Guest: token already in user object
        token.accessToken = (user as any).anonymousToken
      } else {
        // OAuth: exchange with FastAPI
        const res = await fetch(`${BACKEND_URL}/auth/oauth`, {
          method: 'POST',
          body: JSON.stringify({
            provider: account.provider,
            provider_id: account.providerAccountId,
            email: token.email,
            name: token.name,
          })
        })
        const data = await res.json()
        token.accessToken = data.access_token
      }
    }
    return token
  }
}
```

---

#### Bundle 5 — Frontend Task UI (STEP 18–22)

| File | What it does |
|------|-------------|
| `frontend/app/tasks/page.tsx` | Server Component — reads `searchParams.completed`, passes as prop |
| `frontend/components/TasksContainer.tsx` | Client — useQuery + 3 mutations, invalidateQueries on success |
| `frontend/components/TaskForm.tsx` | Controlled input, trim() + empty check, Escape clears |
| `frontend/components/TaskList.tsx` | `<Link>` filter tabs (All / Active / Completed) |
| `frontend/components/TaskItem.tsx` | Toggle, inline edit, delete; `cancelRef` for Escape handling |
| `frontend/jest.config.ts` | Uses `next/jest` (NOT babel-jest) |
| `frontend/components/__tests__/TaskForm.test.tsx` | 4 tests |
| `frontend/components/__tests__/TaskItem.test.tsx` | 5 tests |
| `frontend/components/__tests__/TaskList.test.tsx` | 4 tests |

**Key detail — `cancelRef` in TaskItem (prevents blur-save on Escape):**
```tsx
const cancelRef = useRef(false)

const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'Enter') handleBlur()
  if (e.key === 'Escape') {
    cancelRef.current = true    // ← set flag BEFORE blur fires
    setEditValue(task.title)
    setIsEditing(false)
  }
}

const handleBlur = () => {
  if (cancelRef.current) {
    cancelRef.current = false   // ← reset flag
    return                      // ← don't save
  }
  // save...
}
```

> ⚠️ In some browsers, `onBlur` fires before `onKeyDown`. Without `cancelRef`, pressing Escape would trigger an unintended save.

**Run frontend tests:**
```bash
cd frontend
npm install
npm test -- --watchAll=false
# Expected: 13 tests passed
```

---

#### Bundle 6 — Documentation (STEP 23)

Create three README files:
- `todo-app-migrated/README.md` — monorepo overview + quick start
- `backend/README.md` — setup, .env table, API endpoints
- `frontend/README.md` — OAuth setup, NEXTAUTH_SECRET, feature parity table

---

## Phase 6 — Verification

**Goal:** Confirm all 11 FRs are implemented correctly, no security issues.

### Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│                    VERIFICATION CHECKLIST                       │
├──────────────────────────────────┬──────────┬───────────────────┤
│ Check                            │ Tool     │ Expected result   │
├──────────────────────────────────┼──────────┼───────────────────┤
│ Backend unit tests               │ pytest   │ 15 passed         │
│ Frontend unit tests              │ jest     │ 13 passed         │
│ TypeScript type check            │ tsc      │ 0 errors          │
│ Next.js production build         │ npm build│ SUCCESS           │
│ .env NOT tracked by git          │ git ls-files│ empty output   │
│ API smoke test (16 checks)       │ curl     │ all pass          │
└──────────────────────────────────┴──────────┴───────────────────┘
```

### API Smoke Test (run these manually)

```bash
# 1. Start backend
cd todo-app-migrated/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 2. Run smoke test in another terminal
BASE="http://localhost:8000"

# Health check
curl $BASE/
# Expected: {"status":"ok"}

# Anonymous sign-in
TOKEN=$(curl -s -X POST $BASE/auth/anonymous | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token: $TOKEN"

# Create 3 tasks
curl -s -X POST $BASE/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk"}'

curl -s -X POST $BASE/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Write tests"}'

curl -s -X POST $BASE/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Deploy app"}'

# List all tasks (should return 3)
curl -s $BASE/tasks -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Toggle task 1 to completed
curl -s -X PATCH $BASE/tasks/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"completed":true}'

# Filter active tasks (should return 2)
curl -s "$BASE/tasks?completed=false" -H "Authorization: Bearer $TOKEN"

# Filter completed tasks (should return 1)
curl -s "$BASE/tasks?completed=true" -H "Authorization: Bearer $TOKEN"

# Edit task title
curl -s -X PATCH $BASE/tasks/2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Write integration tests"}'

# Delete task 1
curl -s -o /dev/null -w "%{http_code}" \
  -X DELETE $BASE/tasks/1 \
  -H "Authorization: Bearer $TOKEN"
# Expected: 204

# Per-user isolation — create a second user
TOKEN_B=$(curl -s -X POST $BASE/auth/anonymous | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s $BASE/tasks -H "Authorization: Bearer $TOKEN_B"
# Expected: [] (empty — user B has no tasks)

# Ownership enforcement
curl -s -o /dev/null -w "%{http_code}" \
  -X DELETE $BASE/tasks/2 \
  -H "Authorization: Bearer $TOKEN_B"
# Expected: 404 (not 403 — prevents ID enumeration)

# Empty title validation
curl -s -o /dev/null -w "%{http_code}" \
  -X POST $BASE/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":""}'
# Expected: 422
```

---

## Running the Full App Locally

```
                    ┌─────────────────────┐
                    │  Browser            │
                    │  localhost:3000      │
                    └────────┬────────────┘
                             │ HTTP
                    ┌────────▼────────────┐
                    │  Next.js Frontend   │
                    │  npm run dev        │
                    │  localhost:3000      │
                    └────────┬────────────┘
                             │ HTTP/Bearer JWT
                    ┌────────▼────────────┐
                    │  FastAPI Backend     │
                    │  uvicorn --reload   │
                    │  localhost:8000      │
                    └────────┬────────────┘
                             │ SQLAlchemy
                    ┌────────▼────────────┐
                    │  todo.db (SQLite)   │
                    └─────────────────────┘
```

### Terminal 1 — Backend

```bash
cd todo-app-migrated/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Edit .env and set:
#   SECRET_KEY=$(openssl rand -base64 32)
#   DATABASE_URL=sqlite:///./todo.db

uvicorn app.main:app --reload --port 8000
# ✓ Verify: curl http://localhost:8000/  →  {"status":"ok"}
```

### Terminal 2 — Frontend

```bash
cd todo-app-migrated/frontend
npm install

# Create .env.local from example
cp .env.local.example .env.local
# Edit .env.local and set:
#   NEXTAUTH_SECRET=$(openssl rand -base64 32)
#   NEXTAUTH_URL=http://localhost:3000
#   GOOGLE_CLIENT_ID=...     # from Google Cloud Console
#   GOOGLE_CLIENT_SECRET=... # from Google Cloud Console
#   GITHUB_CLIENT_ID=...     # from github.com/settings/developers
#   GITHUB_CLIENT_SECRET=... # from github.com/settings/developers
#   BACKEND_URL=http://localhost:8000

npm run dev
# ✓ Open: http://localhost:3000
```

---

## Manual E2E Test Checklist

Once both servers are running, test these flows in the browser:

```
Sign-in flow:
  [ ] Visit http://localhost:3000 → see sign-in page (not /tasks)
  [ ] Click "Continue as Guest" → redirected to /tasks
  [ ] Click "Sign out" → back to /
  [ ] Try visiting /tasks → redirected to / (middleware guard works)

  [ ] Click "Sign in with Google" → OAuth popup → /tasks
  [ ] Click "Sign in with GitHub" → OAuth popup → /tasks

Task flows (sign in as Guest to test):
  [ ] Type a task title → press Enter → task appears in list
  [ ] Try submitting empty title → nothing happens
  [ ] Try submitting whitespace-only title → nothing happens
  [ ] Click the checkbox → task gets strikethrough + completed state

Filter flows:
  [ ] Click "Active" → only incomplete tasks shown
  [ ] Click "Completed" → only completed tasks shown
  [ ] Click "All" → all tasks shown
  [ ] URL updates to ?completed=false / ?completed=true / (no param)

Inline edit flows:
  [ ] Double-click task title → input appears, focused automatically
  [ ] Change title → press Enter → title saved
  [ ] Change title → blur (click elsewhere) → title saved
  [ ] Change title → press Escape → original title preserved (NOT saved)

Delete flow:
  [ ] Click delete button → task removed from list immediately

Isolation:
  [ ] Sign in as Guest → create tasks
  [ ] Sign out → sign in as different Google account
  [ ] Verify: no tasks from guest account are visible
```

---

## Common Mistakes to Avoid

| Mistake | What actually happens | Fix |
|--------|----------------------|-----|
| Using `signIn` callback for token exchange | NextAuth ignores writes to JWT in signIn callback | Use `jwt` callback with `trigger === 'signIn' && account` |
| `useSearchParams()` in task page | Requires `<Suspense>` boundary — breaks SSR | Use Server Component page → pass prop to client component |
| `babel-jest` + `.babelrc` for tests | Next.js opts out of SWC → TanStack Query v5 private class fields fail at build | Use `next/jest` in `jest.config.ts`, delete `.babelrc` |
| Sequential 404 → 403 ownership check | Leaks task existence to unauthorized users | Combined query: `filter(id == x, user_id == y)` → always 404 |
| Committing `.env` to git | Secret key in version history | `git rm --cached backend/.env`, add to `.gitignore` |
| `StaticPool` missing in tests | Each test gets empty in-memory DB | Add `poolclass=StaticPool` to test engine |
| Missing `ts-node` for jest.config.ts | `'ts-node' is required for TypeScript configuration` | `npm install --save-dev ts-node` |

---

## Feature Parity: Original vs Migrated

| Original Angular + Firebase | Migrated FastAPI + Next.js |
|----------------------------|---------------------------|
| Firebase Auth anonymous sign-in | `POST /auth/anonymous` → JWT |
| Firebase Auth Google/GitHub OAuth | NextAuth → `POST /auth/oauth` upsert |
| Firebase write `/tasks/{uid}` | `POST /tasks` → SQLite row |
| `completed: false` default | `completed=False` in Pydantic schema |
| `orderByChild('completed')` filter | `?completed=true/false` SQL filter |
| AngularFire `.update()` | `PATCH /tasks/{id}` |
| AngularFire `.remove()` | `DELETE /tasks/{id}` → 204 |
| Firebase Security Rules | `filter(Task.user_id == current_user.id)` |
| `title.trim().length > 0` guard | Pydantic `@field_validator` → 422 |
| Firebase JWT (session-based) | HS256 JWT, 30-day `exp` |
| `AutoFocusDirective` | `useRef + useEffect([isEditing])` |
| ReplaySubject + switchMap filter | URL `searchParams` → SQL query param |

---

## Final Test Counts (Expected)

| Category | Count | Status |
|----------|-------|--------|
| Backend: auth tests | 7 | ✅ pass |
| Backend: task tests | 8 | ✅ pass |
| Frontend: TaskForm | 4 | ✅ pass |
| Frontend: TaskItem | 5 | ✅ pass |
| Frontend: TaskList | 4 | ✅ pass |
| TypeScript check | — | ✅ 0 errors |
| Next.js build | — | ✅ succeeds |
| API smoke test | 16 | ✅ pass |

**Total automated: 28 tests. All green.**
