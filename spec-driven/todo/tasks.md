# Tasks: Todo App Migration
> Domain: `todo` — React 18 + TypeScript + Vite + Firebase v10
> Generated from: spec.md + design.md

---

## Bundle 1: Project Scaffold

**Goal:** Establish the base project structure with Vite, React 18, TypeScript (strict), Tailwind CSS, PWA support, and Vitest configuration.

---

### STEP 1.1 — package.json

**Intent:** Define all runtime and dev dependencies with pinned major versions.

**Implementation guidance:**
- `"type": "module"` required for ESM-first Vite
- Include scripts: `dev`, `build` (`tsc && vite build`), `preview`, `test`, `test:run`, `lint`
- Runtime deps: `firebase@^10`, `react@^18`, `react-dom@^18`, `react-router-dom@^6`
- Dev deps: `vite`, `@vitejs/plugin-react`, `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/jest-dom`, `tailwindcss`, `postcss`, `autoprefixer`, `vite-plugin-pwa`, TypeScript types

**Verify:** `npm install` completes without peer-dep errors; `node_modules/` is created.

---

### STEP 1.2 — TypeScript configuration

**Intent:** Enable TypeScript strict mode for the app source and a separate config for Vite config files.

**Implementation guidance:**
- `tsconfig.json`: `strict: true`, `noEmit: true`, `jsx: "react-jsx"`, `moduleResolution: "bundler"`, `target: "ES2020"`, `include: ["src"]`
- `tsconfig.node.json`: for `vite.config.ts` — `module: "ESNext"`, `moduleResolution: "bundler"`, `composite: true`

**Verify:** `npx tsc --noEmit` exits 0 on an empty `src/` (or with placeholder files).

---

### STEP 1.3 — Vite config + PWA plugin

**Intent:** Configure Vite with React fast-refresh and PWA manifest/service-worker generation.

**Implementation guidance:**
- `vite.config.ts`: register `@vitejs/plugin-react()` and `VitePWA({ registerType: 'autoUpdate', manifest: { name, short_name, theme_color, icons } })`
- Icon paths: `/icon-192.png` and `/icon-512.png` (placed in `public/`)

**Verify:** `npx vite --version` runs; config imports resolve without TS errors.

---

### STEP 1.4 — Tailwind CSS + PostCSS

**Intent:** Enable Tailwind utility classes across all TSX files.

**Implementation guidance:**
- `tailwind.config.ts`: `content: ['./index.html', './src/**/*.{ts,tsx}']`
- `postcss.config.js`: plugins `tailwindcss` and `autoprefixer` (ES module default export)
- `src/index.css`: `@tailwind base; @tailwind components; @tailwind utilities;`

**Verify:** A TSX file using `className="flex"` should produce no Tailwind-related errors.

---

### STEP 1.5 — Vitest config

**Intent:** Configure Vitest with jsdom environment and `@testing-library/jest-dom` matchers.

**Implementation guidance:**
- `vitest.config.ts`: `environment: 'jsdom'`, `setupFiles: ['./src/test/setup.ts']`, `globals: true`
- `src/test/setup.ts`: `import '@testing-library/jest-dom'`

**Verify:** `npx vitest run` with no test files exits 0 (or with "no test files found" message).

---

### STEP 1.6 — index.html + public assets

**Intent:** Provide the HTML entry point and public directory placeholder for PWA icons.

**Implementation guidance:**
- `index.html`: `<div id="root">` + `<script type="module" src="/src/main.tsx">`
- `public/.gitkeep`: ensures `public/` is tracked by git (real PNG icons added separately before production deploy)
- `.env.example`: document all `VITE_FIREBASE_*` env vars
- `.gitignore`: exclude `node_modules`, `dist`, `.env`, `*.env.local`, `.DS_Store`

**Verify:** `index.html` opens in browser via `npm run dev` (after main.tsx is created in Bundle 2).

---

## Bundle 2: Auth Layer

**Goal:** Wire Firebase Auth with a React context provider and `useAuth` hook. Implement anonymous auto-sign-in and social sign-in. Render `AuthPanel` in the app header.

---

### STEP 2.1 — Firebase initialization (src/firebase.ts)

**Intent:** Create singleton Firebase app, Auth, and Firestore instances consumed throughout the app.

**Implementation guidance:**
- Import `initializeApp`, `getAuth`, `getFirestore` from their respective Firebase v10 modules
- Config reads from `import.meta.env.VITE_FIREBASE_*` variables
- Export named constants `app`, `auth`, `db`

**Verify:** File compiles with `tsc --noEmit`; no `any` types.

---

### STEP 2.2 — Task types (src/types/task.ts)

**Intent:** Define the canonical `Task` interface and `FilterType` union used across hooks and components.

**Implementation guidance:**
- `Task`: `{ id: string; title: string; completed: boolean; createdAt: Timestamp | null }`
- `FilterType`: `'all' | 'active' | 'completed'`
- Import `Timestamp` from `firebase/firestore`

**Verify:** No TS errors; `createdAt: null` is allowed (transient before server confirms write).

---

### STEP 2.3 — AuthContext provider (src/contexts/AuthContext.tsx)

**Intent:** Centralize auth state: run `onAuthStateChanged` once, auto-trigger `signInAnonymously` on null user, expose sign-in/sign-out methods and error state.

**Implementation guidance:**
- `AuthProvider` wraps children with context value
- `useEffect([], ...)` registers `onAuthStateChanged` — unsubscribes on unmount
- When callback fires with `null`: call `signInAnonymously(auth)` (auto anon session)
- When callback fires with user: `setUser(user); setLoading(false)`
- `signInWithGoogle/Github/Twitter/Facebook`: call `signInWithPopup` with corresponding provider; catch `AuthError` and set `authError` state
- `signOut`: calls `firebaseSignOut(auth)`; subsequent `onAuthStateChanged(null)` re-triggers anon sign-in
- Export `useAuth()` hook that throws if used outside provider

**Verify:** Context compiles; `useAuth()` returns correct shape; `loading` starts `true`.

---

### STEP 2.4 — AuthPanel component (src/components/AuthPanel.tsx)

**Intent:** Render sign-in buttons for anonymous users; show display name and sign-out for authenticated social users.

**Implementation guidance:**
- If `user.isAnonymous`: show four social sign-in buttons (Google, GitHub, Twitter, Facebook)
- If social user: show `user.displayName ?? user.email ?? 'User'` and a Sign Out button
- Display `authError` if non-null
- Each button calls the corresponding `useAuth` method

**Verify:** Component renders without errors; buttons are accessible (labeled).

---

### STEP 2.5 — App entry (src/main.tsx)

**Intent:** Bootstrap React app with router, auth provider, and CSS.

**Implementation guidance:**
- `ReactDOM.createRoot(document.getElementById('root')!).render(...)`
- Wrap in `<React.StrictMode>`, `<BrowserRouter>`, then `<App />`
- Import `./index.css`

**Verify:** Dev server starts; page loads without console errors.

---

## Bundle 3: Task CRUD

**Goal:** Implement Firestore helpers, `useTasks` subscription hook, `useFilteredTasks` memoization hook, and the three task UI components (`TaskForm`, `TaskItem`, `TaskList`).

---

### STEP 3.1 — Firestore helpers (src/lib/firestore.ts)

**Intent:** Thin wrappers around Firestore SDK calls; no React hooks; directly callable from event handlers.

**Implementation guidance:**
- `subscribeTasks(uid, cb)`: `onSnapshot(query(collection(db,'tasks',uid,'items'), orderBy('createdAt','asc')), snap => cb(docs))` — returns `Unsubscribe`
- `addTask(uid, title)`: `addDoc` with `{ title: trimmed, completed: false, createdAt: serverTimestamp() }` — no-op if trimmed is empty
- `toggleTask(uid, taskId, completed)`: `updateDoc` with `{ completed }`
- `updateTaskTitle(uid, taskId, title)`: `updateDoc` with `{ title: trimmed }` — no-op if empty
- `deleteTask(uid, taskId)`: `deleteDoc`
- Collection path: `tasks/{uid}/items/{taskId}` (subcollection keeps per-user isolation)

**Verify:** All functions have correct TypeScript signatures; no implicit `any`.

---

### STEP 3.2 — useTasks hook (src/hooks/useTasks.ts)

**Intent:** Subscribe to the user's tasks in real-time; unsubscribe on unmount; handle null uid.

**Implementation guidance:**
- `useTasks(uid: string | null)` → `{ tasks: Task[], loading: boolean }`
- `useEffect([uid])`: if uid is null → reset state, early return; else call `subscribeTasks(uid, setTasks)` and set loading false in callback; return unsubscribe function
- `setLoading(true)` when uid changes (before new subscription fires)

**Verify:** Hook returns `loading: true` initially; updates when snapshot fires.

---

### STEP 3.3 — useFilteredTasks hook (src/hooks/useFilteredTasks.ts)

**Intent:** Client-side filter derivation via `useMemo` — no extra Firestore queries.

**Implementation guidance:**
- `useFilteredTasks(tasks: Task[], filter: FilterType)` → `Task[]`
- `useMemo([tasks, filter])`: switch on filter type, return appropriate subset

**Verify:** Returns correct subsets for each filter value; memoized (same reference when inputs unchanged).

---

### STEP 3.4 — TaskForm component (src/components/TaskForm.tsx)

**Intent:** Input form with auto-focus, Enter-to-submit, trimming, and empty-title guard.

**Implementation guidance:**
- Props: `{ uid: string }`
- `useRef<HTMLInputElement>` + `useEffect([], () => inputRef.current?.focus())`
- `onSubmit`: trim title, guard empty, call `addTask(uid, trimmed)`, clear input
- Styled with Tailwind: full-width input + Add button

**Verify:** Input is focused on mount; submit creates a task; empty submit is no-op.

---

### STEP 3.5 — TaskItem component (src/components/TaskItem.tsx)

**Intent:** Single task row with checkbox toggle, inline title editing (double-click), and delete.

**Implementation guidance:**
- Props: `{ task: Task; uid: string }`
- Local state: `editing: boolean`, `editTitle: string`
- View mode: checkbox + `<span onDoubleClick={enterEditMode}>` + delete button
- Edit mode: `<input ref>` auto-focused via `useEffect([editing])`, `onBlur={saveEdit}`, `onKeyDown` handles Enter (save) and Escape (revert + exit)
- `saveEdit`: trim title; only call `updateTaskTitle` if `trimmed.length > 0 && trimmed !== task.title`
- Delete: calls `deleteTask(uid, task.id)`
- Completed tasks: `line-through text-gray-400` on title span

**Verify:** Double-click enters edit mode; Enter saves; Escape reverts; empty title does not save; unchanged title does not call updateDoc.

---

### STEP 3.6 — TaskList component (src/components/TaskList.tsx)

**Intent:** Render a list of `TaskItem` components; show empty state when no tasks.

**Implementation guidance:**
- Props: `{ tasks: Task[]; uid: string }`
- If `tasks.length === 0`: render empty state paragraph
- Else: render `<ul>` mapping tasks to `<TaskItem key={task.id} />`

**Verify:** Empty state renders for zero tasks; all tasks render with unique keys.

---

## Bundle 4: Filter + PWA + App Wiring

**Goal:** Implement URL-based filter state, wire all components into `App.tsx`, and ensure PWA manifest config is correct.

---

### STEP 4.1 — FilterTabs component (src/components/FilterTabs.tsx)

**Intent:** Render three filter buttons that read/write the `?filter` URL search param.

**Implementation guidance:**
- Use `useSearchParams()` from `react-router-dom`
- Current filter: `(searchParams.get('filter') as FilterType) ?? 'all'`
- Each button calls `setSearchParams(f === 'all' ? {} : { filter: f })`
- Active tab: `bg-blue-500 text-white`; inactive: `bg-gray-100 hover:bg-gray-200`
- Labels: "all", "active", "completed" (capitalized via `capitalize` Tailwind class)

**Verify:** Clicking tabs updates URL; back button restores previous filter; active tab is visually distinct.

---

### STEP 4.2 — App.tsx wiring

**Intent:** Root component that wraps `AuthProvider`, reads auth state, shows loading spinner, and renders the full task UI.

**Implementation guidance:**
- `AuthProvider` wraps the inner `TodoApp` component
- `TodoApp`: reads `{ user, loading }` from `useAuth()`; reads `filter` from `useSearchParams`
- Loading state: full-screen centered spinner while `loading === true`
- When loaded: render `<header>` with `<AuthPanel>` + `<main>` with `<TaskForm>`, `<FilterTabs>`, `<TaskList>`
- `uid = user?.uid ?? null`; pass to `useTasks`, `TaskForm`, `TaskList`
- `useFilteredTasks(tasks, filter)` derives visible tasks

**Verify:** App renders header + task area; loading spinner shows briefly on first load.

---

### STEP 4.3 — PWA icons placeholder

**Intent:** Ensure `public/` directory exists and is tracked so `vite-plugin-pwa` manifest icon paths resolve.

**Implementation guidance:**
- Create `public/.gitkeep` (real 192×192 and 512×512 PNG icons must be added before production deploy)
- Note in `.env.example` that PWA icons are needed for production installability

**Verify:** `public/` directory exists; no build errors related to missing icons in dev mode.

---

### STEP 4.4 — Firestore config files

**Intent:** Provide Firestore security rules and composite index definitions for deployment.

**Implementation guidance:**
- `firestore.rules`: allow read/write only if `request.auth != null && request.auth.uid == uid`; deny-all wildcard for all other paths
- `firestore.indexes.json`: composite index on `(completed ASC, createdAt ASC)` for the `tasks` collection group
- Place both at the repo root of `todo-app-migrated/`

**Verify:** Files are valid JSON/rules syntax; no parse errors.

---

## Bundle 5: Tests + Final Polish

**Goal:** Write Vitest unit tests for `TaskItem` and `useFilteredTasks`. Verify TypeScript strict-mode compliance. Confirm tests pass.

---

### STEP 5.1 — Vitest setup file

**Intent:** Import `@testing-library/jest-dom` matchers globally for all test files.

**Implementation guidance:**
- `src/test/setup.ts`: single line `import '@testing-library/jest-dom'`
- Ensure `vitest.config.ts` references this file in `setupFiles`

**Verify:** `expect(...).toBeInTheDocument()` is available in tests without manual import.

---

### STEP 5.2 — TaskItem unit tests (src/test/TaskItem.test.tsx)

**Intent:** Cover all FR-2.3 (toggle), FR-2.4 (delete), and FR-2.5 (inline edit) acceptance criteria.

**Implementation guidance:**
- Mock `../lib/firestore` with `vi.mock` (all functions as `vi.fn()`)
- Mock `../firebase` with empty `{}` objects
- Mock `firebase/firestore` to prevent real SDK initialization
- Test cases:
  1. Renders task title
  2. `toggleTask` called on checkbox click
  3. `deleteTask` called on delete button click
  4. Double-click enters edit mode (input visible)
  5. Escape reverts title without calling `updateTaskTitle`
  6. Empty title on Enter → no `updateTaskTitle` call
  7. Unchanged title on Enter → no `updateTaskTitle` call
  8. Completed task has `line-through` class on title span

**Verify:** All 8 tests pass with `vitest run`.

---

### STEP 5.3 — useFilteredTasks unit tests (src/test/useFilteredTasks.test.ts)

**Intent:** Verify client-side filter logic for all three filter values.

**Implementation guidance:**
- Use `renderHook` from `@testing-library/react`
- Test tasks array: one active (`completed: false`) + one done (`completed: true`)
- Test cases:
  1. `'all'` → returns both tasks
  2. `'active'` → returns only incomplete task
  3. `'completed'` → returns only complete task

**Verify:** All 3 tests pass with `vitest run`.

---

### STEP 5.4 — TypeScript strict-mode check

**Intent:** Confirm the entire `src/` compiles with zero errors under `strict: true`.

**Implementation guidance:**
- Run `npx tsc --noEmit` from `todo-app-migrated/`
- Fix any errors: unused variables (`noUnusedLocals`), implicit any, missing return types
- Common fixes: explicit return types on helper functions, proper `as` casts with type guards

**Verify:** `tsc --noEmit` exits 0 with no output.

---

### STEP 5.5 — Full test run

**Intent:** Confirm all tests pass after TS fixes.

**Implementation guidance:**
- Run `npx vitest run` from `todo-app-migrated/`
- If any test fails, diagnose and fix the root cause (do not suppress)

**Verify:** All tests pass; exit code 0; test count matches expected (8 TaskItem + 3 useFilteredTasks = 11 total).
