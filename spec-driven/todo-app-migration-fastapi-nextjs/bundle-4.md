# Bundle B-4: Frontend Auth Flow

> Stage: depth | Parallel: no (depends on B-3; B-1 strongly recommended for live token exchange) | Files: frontend/auth.ts, frontend/middleware.ts, frontend/app/api/auth/[...nextauth]/route.ts, frontend/lib/api.ts, frontend/app/page.tsx, frontend/components/SignIn.tsx, frontend/components/Header.tsx

**Bundle Verify**: A user can sign in with Google or as a guest, land on /tasks with a valid FastAPI JWT in session, and sign out returning to /.
- **Level**: e2e (manual)
- **Given**: Both servers running; Google OAuth app configured
- **Action**: Navigate to http://localhost:3000 → sign in with Google → check session.accessToken is set → sign out
- **Outcome**: Lands on /tasks after sign-in; session.accessToken is a decodable FastAPI JWT; sign-out returns to /

---

## Context

**Architecture Decisions:** AD-1 (NextAuth v5), AD-2 (jwt callback exchange), AD-3 (Google + GitHub only initially), F-5 (CredentialsProvider anonymous), F-6 (server-to-server — no CORS on auth endpoints)

**Findings:** F-1 (NextAuth v5 App Router), F-2 (jwt callback trigger guard), F-3 (token in encrypted cookie), F-4 (auth()→Server, useSession()→Client, api.ts→fetch), F-5 (CredentialsProvider anonymous)

**Standards:** S-1, S-2, S-3, S-7, S-9

**Risks:** R-3 (NextAuth v5 still maturing — pin exact patch version)

**Relevant ACs:** AC-1.1, AC-1.2, AC-1.3, AC-2.1, AC-2.2, AC-3.1, AC-3.2, AC-3.3

---

## STEPs

### STEP-13: NextAuth v5 configuration (auth.ts)
**Trace:** `[FR-1 -> AC-1.1], [FR-1 -> AC-1.2], [FR-2 -> AC-2.1]` | **Informed by:** AD-1, AD-2, AD-3, F-1, F-2, F-3, F-5 | **Effort:** L

**Files:**
- `todo-app-migrated/frontend/auth.ts` — create

**Intent:** The `jwt` callback with `trigger === 'signIn' && account` guard exchanges the FastAPI token exactly once per sign-in. `session.maxAge = 30*24*60*60` must match FastAPI JWT 30-day expiry. CredentialsProvider reads `user.anonymousToken` set in `authorize`.

**Implementation guidance:**
1. `export const { handlers, auth, signIn, signOut } = NextAuth({ providers: [...], callbacks: { jwt, session }, session: { maxAge: 30*24*60*60 } })`
2. Providers: `GoogleProvider`, `GitHubProvider`, `CredentialsProvider({ name: "anonymous", credentials: {}, async authorize() { call POST /auth/anonymous; return { id: String(data.user_id), name: 'Guest', anonymousToken: data.access_token } } })`
3. `jwt` callback: `if (trigger === 'signIn' && account) { if (account.type === 'credentials') { token.accessToken = (user as any).anonymousToken } else { fetch POST /auth/oauth with provider identity; token.accessToken = data.access_token } }`
4. `session` callback: `session.accessToken = token.accessToken as string; return session`
5. Use `process.env.INTERNAL_API_URL` (non-public) for server-side FastAPI calls

**Verify:**
- Level: integration | Given: FastAPI running; mock Google OAuth | Action: simulate signIn → inspect jwt callback | Outcome: token.accessToken set; session.accessToken non-null

> **Standards:** S-1, S-2, S-3

**Dependencies:** Depends on STEP-11, STEP-12; enables STEP-14, STEP-15

---

### STEP-14: NextAuth route handler + middleware
**Trace:** `[FR-3 -> AC-3.1], [FR-3 -> AC-3.2], [FR-3 -> AC-3.3]` | **Informed by:** F-4, AD-1 | **Effort:** S

**Files:**
- `todo-app-migrated/frontend/app/api/auth/[...nextauth]/route.ts` — create
- `todo-app-migrated/frontend/middleware.ts` — create

**Intent:** Route handler re-exports handlers from auth.ts. Middleware reads `req.auth` without a DB call. Matcher must cover `/tasks/:path*` AND `/` for bidirectional guard.

**Implementation guidance:**
1. `route.ts`: `import { handlers } from "@/auth"; export const { GET, POST } = handlers`
2. `middleware.ts`: check `req.auth`; unauthenticated + /tasks/* → redirect to /; authenticated + / → redirect to /tasks; matcher: `['/', '/tasks/:path*']`

**Verify:**
- Level: integration | Given: no session | Action: GET /tasks | Outcome: 307 → /; GET / with session → 307 → /tasks

> **Standards:** S-3

**Dependencies:** Depends on STEP-13; enables STEP-16, STEP-18

---

### STEP-15: API client wrapper (lib/api.ts)
**Trace:** `[FR-4 -> AC-4.1], [FR-5 -> AC-5.1], [FR-6 -> AC-6.1]` | **Informed by:** F-4, S-9 | **Effort:** S

**Files:**
- `todo-app-migrated/frontend/lib/api.ts` — create

**Intent:** Every function calls `getSession()` before fetching — no token caching. S-9 is a firm boundary: no fetch() outside this module.

**Implementation guidance:**
1. `const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'`
2. `apiFetch(path, init?)`: await getSession(); add Authorization: Bearer; call fetch; throw on non-ok
3. Export: `getTasks(completed?)`, `createTask(title)`, `updateTask(id, changes)`, `deleteTask(id)`
4. TypeScript: `interface Task { id: number; title: string; completed: boolean; created_at: string }`

**Verify:**
- Level: inspection | Given: codebase written | Action: `grep -r "fetch(" --include="*.tsx" components/ app/ | grep -v api.ts` | Outcome: 0 results

> **Standards:** S-3, S-9

**Dependencies:** Depends on STEP-12, STEP-13; enables STEP-18–STEP-21

---

### STEP-16: Sign-in page + SignIn component
**Trace:** `[FR-1 -> AC-1.1], [FR-1 -> AC-1.2], [FR-1 -> AC-1.3]` | **Informed by:** AD-1, F-5, AD-3 | **Effort:** S

**Files:**
- `todo-app-migrated/frontend/app/page.tsx` — create
- `todo-app-migrated/frontend/components/SignIn.tsx` — create

**Intent:** `page.tsx` is Server Component. `SignIn.tsx` is 'use client'. Anonymous: `signIn('credentials', { redirect: false })` then `router.push`. OAuth: `signIn('google', { callbackUrl: '/tasks' })`. Handle `result.error` for AC-1.3.

**Implementation guidance:**
1. `page.tsx`: Server Component rendering centered `<SignIn />`
2. `SignIn.tsx`: three buttons — Google, GitHub, "Continue as guest"; guest handler checks `result?.error`; style with Tailwind (full-width, 48px height equivalent)
3. Show error message when sign-in fails

**Verify:**
- Level: inspection | Given: SignIn.tsx | Action: check error branch | Outcome: error state renders when result?.error is truthy

> **Standards:** S-3, S-4, S-7

**Dependencies:** Depends on STEP-13, STEP-14; parallel with STEP-17

---

### STEP-17: Header component + sign-out
**Trace:** `[FR-2 -> AC-2.1], [FR-2 -> AC-2.2]` | **Informed by:** AD-1 | **Effort:** XS

**Files:**
- `todo-app-migrated/frontend/components/Header.tsx` — create

**Intent:** Sign-out uses `callbackUrl: '/'`. Button hidden when `status !== 'authenticated'` — prevents flash.

**Implementation guidance:**
1. `'use client'`; `useSession()` for status
2. Sign-out button: `signOut({ callbackUrl: '/' })`; only renders when `status === 'authenticated'`
3. Include in `app/tasks/layout.tsx`

**Verify:**
- Level: inspection | Given: Header.tsx | Action: check signOut call | Outcome: `callbackUrl: '/'` present; button conditionally rendered

> **Standards:** S-3, S-4, S-7

**Dependencies:** Depends on STEP-13; parallel with STEP-16
