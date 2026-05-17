# Bundle B-3: Frontend Infrastructure

> Stage: skeleton | Parallel: yes (with B-1 — no shared files) | Files: frontend/package.json, frontend/tsconfig.json, frontend/tailwind.config.ts, frontend/app/globals.css, frontend/app/layout.tsx, frontend/app/providers.tsx, frontend/types/next-auth.d.ts

**Bundle Verify**: Next.js project builds successfully with TypeScript strict mode, Tailwind configured, and session + query providers available.
- **Level**: inspection
- **Given**: project bootstrapped
- **Action**: `npm run build` from `frontend/`
- **Outcome**: 0 TypeScript errors; no "session.accessToken does not exist" error

---

## Context

**Architecture Decisions:** AD-1 (NextAuth v5), AD-6 (server page + client container)

**Findings:** F-7 (TypeScript augmentation required), F-20 (SessionProvider + QueryClientProvider in providers.tsx)

**Standards:** S-3 (TypeScript strict), S-4 (Tailwind only), S-7 ('use client' sparingly)

---

## STEPs

### STEP-10: Next.js project initialization
**Trace:** `MANUAL -> project scaffold` | **Effort:** S

**Files:**
- `todo-app-migrated/frontend/package.json` — create
- `todo-app-migrated/frontend/tsconfig.json` — create
- `todo-app-migrated/frontend/tailwind.config.ts` — create
- `todo-app-migrated/frontend/app/globals.css` — create
- `todo-app-migrated/frontend/.env.local.example` — create

**Intent:** Pin `next-auth@5` (not latest). Pin `@tanstack/react-query@5` (breaking changes from v4). Tailwind content paths must cover app/ and components/. Add `sm540: "540px"` custom screen to match spec AC-11.2.

**Implementation guidance:**
1. `package.json` deps: `next@14`, `next-auth@5`, `@tanstack/react-query@5`, `react@18`, `react-dom@18`, `typescript`, `tailwindcss`, `autoprefixer`, `postcss`, `@types/react`, `@types/node`
2. `tsconfig.json`: `"strict": true`, `"paths": { "@/*": ["./*"] }`, `"plugins": [{ "name": "next" }]`
3. `tailwind.config.ts`: `content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"]`; `theme.extend.screens: { "sm540": "540px" }`
4. `globals.css`: `@tailwind base; @tailwind components; @tailwind utilities` only
5. `.env.local.example`: all required keys with empty values

**Verify:**
- Level: inspection | Given: files written | Action: `npx tsc --noEmit` | Outcome: 0 errors

> **Standards:** S-3, S-4

**Dependencies:** Enables STEP-11, STEP-12

---

### STEP-11: Root layout + Providers wrapper
**Trace:** `[FR-1 -> AC-1.1], [FR-3 -> AC-3.1]` | **Informed by:** F-20, AD-1 | **Effort:** S

**Files:**
- `todo-app-migrated/frontend/app/layout.tsx` — create
- `todo-app-migrated/frontend/app/providers.tsx` — create

**Intent:** `layout.tsx` must remain a Server Component. `providers.tsx` is `'use client'`. `QueryClient` in `useState(() => new QueryClient(...))` — prevents recreation on re-render.

**Implementation guidance:**
1. `providers.tsx`: `'use client'`; `const [queryClient] = useState(() => new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, retry: 1 } } }))`; wrap in `<SessionProvider><QueryClientProvider>{children}</QueryClientProvider></SessionProvider>`
2. `layout.tsx`: Server Component; imports Providers and globals.css; standard html/body structure

**Verify:**
- Level: inspection | Given: layout.tsx | Action: check for 'use client' | Outcome: NOT on layout.tsx; IS on providers.tsx

> **Standards:** S-3, S-7

**Dependencies:** Depends on STEP-10; enables STEP-13

---

### STEP-12: TypeScript session type augmentation
**Trace:** `[FR-1 -> AC-1.1]` | **Informed by:** F-7, AD-2 | **Effort:** XS

**Files:**
- `todo-app-migrated/frontend/types/next-auth.d.ts` — create

**Intent:** Without this, `session.accessToken` causes TypeScript errors everywhere. Must augment Session, JWT, and User interfaces.

**Implementation guidance:**
1. Augment `Session`: `accessToken?: string`
2. Augment `JWT` (from `next-auth/jwt`): `accessToken?: string; fastapiUserId?: number`
3. Augment `User` (from `next-auth`): `anonymousToken?: string`

**Verify:**
- Level: inspection | Given: types written | Action: `npx tsc --noEmit` after writing `const t: string = session?.accessToken ?? ""` in api.ts | Outcome: 0 errors

> **Standards:** S-3

**Dependencies:** Depends on STEP-10; enables STEP-13, STEP-15
