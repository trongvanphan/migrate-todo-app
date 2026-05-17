# Architecture Design: Todo App Migration
> Domain: `todo` — React 18 + TypeScript + Vite + Firebase v10 + TanStack Query v5

---

## 1. Architecture Decisions

### AD-1: Firestore vs Realtime Database

**Context:**
The legacy app uses Firebase Realtime Database with AngularFire2 v4 RC. The database stores tasks at `/tasks/{uid}/{pushKey}` with server-side `orderByChild('completed').equalTo(filter)` queries. The SDK (AngularFire2 v4, Firebase SDK v4) is from 2017 and has been superseded by multiple major versions.

**Decision:**
Migrate to **Firebase Firestore v10** (modular SDK) with a collection path of `/tasks/{uid}/{docId}`.

**Rationale:**
1. **Query expressiveness:** Firestore supports compound queries (`where` + `orderBy` on different fields) with composite indexes. Realtime Database requires `.indexOn` and only supports one `orderByChild` per query; mixing sort and filter requires client-side re-sorting.
2. **Modular SDK tree-shaking:** Firebase v10 modular SDK (`import { collection, query, where } from 'firebase/firestore'`) enables Vite to tree-shake unused SDK surface. The legacy app imported the entire Firebase bundle.
3. **Document model parity:** Firestore documents map naturally to TypeScript interfaces. The `$key` virtual field in AngularFire2 maps cleanly to `doc.id` in the Firestore SDK.
4. **`serverTimestamp()` sentinel:** Firestore's `serverTimestamp()` is the direct equivalent of `firebase.database.ServerValue.TIMESTAMP`. The stored type changes from `number` (epoch ms) to `Timestamp` object; `createdAt` sort still works natively.
5. **Security model:** Firestore security rules are more expressive and easier to test than Realtime Database JSON rules.
6. **Long-term support:** Firestore is Firebase's primary database product; Realtime Database is in maintenance mode.

**Trade-off accepted:** Firestore requires composite indexes for compound queries (e.g., `where('completed','==',true)` + `orderBy('createdAt')`). These are defined declaratively in `firestore.indexes.json` and deployed with the Firebase CLI — no runtime cost.

---

### AD-2: TanStack Query v5 for Firebase Realtime Subscriptions

**Context:**
TanStack Query is designed for async server state (fetch, cache, refetch). Firebase Firestore uses `onSnapshot` subscriptions rather than one-shot promises. Bridging these requires custom integration.

**Decision:**
Use **TanStack Query v5** for Firestore subscriptions by wrapping `onSnapshot` in a custom `QueryObservable` pattern inside `useTasks`. The `useTasks` hook uses `useQuery` with a `queryFn` that returns a `Promise` for the initial load, then separately subscribes to `onSnapshot` and calls `queryClient.setQueryData` on each snapshot update.

Alternatively (simpler): use **React `useState` + `useEffect`** directly in `useTasks` for the real-time subscription, and use TanStack Query only for mutations (optimistic updates). This is the approach chosen here for clarity and lower complexity.

**Decision (refined):**
- `useTasks`: `useEffect` + `useState` for the `onSnapshot` real-time subscription. Returns `{ tasks, loading, error }`.
- `useFilteredTasks`: Derives filtered list from `tasks` array client-side (avoids separate Firestore queries for "All" filter; one subscription per user session).
- Firestore mutations (`addDoc`, `updateDoc`, `deleteDoc`): called directly in event handlers in `lib/firestore.ts` helpers; no TanStack Query mutation wrappers needed (Firestore's optimistic local writes make loading states unnecessary for simple CRUD).

**Rationale:**
- `onSnapshot` already provides real-time push updates — TanStack Query's polling and stale-time features add no value here.
- Keeping one `onSnapshot` subscription for all tasks (no separate query per filter) means a single listener and client-side filtering — this is simpler and avoids Firestore index requirements for the compound filtered+sorted query.
- TanStack Query is retained as a dependency for any future REST/Cloud Functions integration and for its DevTools.

---

### AD-3: Auth Provider Pattern — FirebaseContext + useAuth Hook

**Context:**
The app needs auth state (current user, UID, loading) accessible from multiple components: the route guard, the header sign-out button, and the `useTasks` hook (which needs the UID to scope Firestore queries).

**Decision:**
Implement a **`FirebaseContext`** provider (in `src/firebase.ts` + a separate context in `src/contexts/FirebaseContext.tsx`) that:
1. Calls `onAuthStateChanged` once on mount.
2. On first `null` user, calls `signInAnonymously` automatically.
3. Exposes `{ user, loading, error }` via React context.

The **`useAuth` hook** (`src/hooks/useAuth.ts`) reads from this context and provides sign-in/sign-out methods, keeping auth logic centralized and the hook API minimal.

**Rationale:**
- Mirrors the Angular service pattern (`AuthService` injectable) but in React idiom.
- `onAuthStateChanged` must only be registered once to avoid multiple listeners accumulating across re-renders — the context provider with `useEffect([])`  guarantees this.
- The anonymous sign-in auto-trigger on `null` user (from `onAuthStateChanged`) is the correct place for this logic because it runs after Firebase SDK initialization, not on component mount.
- All components that need auth state (`App`, `AuthPanel`, `TaskForm`, `useTasks`) consume `useAuth()` without prop drilling.

---

### AD-4: Filter State Location — URL Search Params

**Context:**
The legacy app used Angular's matrix URL syntax (`;completed=true`) to store filter state in the URL. Filter state must survive page refresh and be bookmarkable ("here are my active tasks" link).

**Decision:**
Store filter state as a **URL search parameter** `?filter=all|active|completed` using React Router's `useSearchParams` hook.

**Rationale:**
1. **Bookmarkable:** A user can copy the URL to share or bookmark a specific filter view.
2. **Browser back/forward:** Changing the filter adds a history entry; back button restores the previous filter — identical to the legacy Angular router behavior.
3. **No global state needed:** Filter is derived from the URL on each render; no `useState` or `useReducer` is needed for filter at the app level.
4. **Default behavior:** Absence of the `?filter` param defaults to "all" — consistent with the legacy "no param = show all" default.
5. **Standard params over matrix syntax:** Query string `?filter=active` is more conventional than Angular's matrix URL syntax and works with any HTTP server.

---

### AD-5: Vite PWA Plugin vs sw-precache

**Context:**
The legacy app used `sw-precache` as a post-build script to generate a service worker. `sw-precache` is deprecated (last release 2017); its successor is `workbox-webpack-plugin` or the Vite ecosystem equivalent.

**Decision:**
Use **`vite-plugin-pwa`** (wraps Workbox) to replace `sw-precache`.

**Rationale:**
1. **Native Vite integration:** `vite-plugin-pwa` hooks into Vite's build lifecycle — no `postbuild` script required.
2. **Workbox under the hood:** `sw-precache`'s author built Workbox as its official successor. `vite-plugin-pwa` uses Workbox's `generateSW` or `injectManifest` mode.
3. **Web App Manifest generation:** The plugin generates the `manifest.webmanifest` automatically from config — satisfies FR-4.1.
4. **Zero config for precache:** The default `generateSW` mode precaches all Vite build output (JS, CSS, HTML) — equivalent to the legacy `sw-precache` configuration.
5. **TypeScript types:** Full TypeScript support; no hacks needed.

---

## 2. File Inventory

Every file to be created in `todo-app-migrated/`. Files are listed with their purpose, the FRs they implement, and key dependencies.

```
todo-app-migrated/
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── package.json
├── .env.example
├── firestore.rules
├── firestore.indexes.json
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── firebase.ts
    ├── contexts/
    │   └── FirebaseContext.tsx
    ├── hooks/
    │   ├── useAuth.ts
    │   ├── useTasks.ts
    │   └── useFilteredTasks.ts
    ├── components/
    │   ├── AuthPanel.tsx
    │   ├── TaskForm.tsx
    │   ├── TaskList.tsx
    │   ├── TaskItem.tsx
    │   └── FilterTabs.tsx
    ├── types/
    │   └── task.ts
    └── lib/
        └── firestore.ts
```

---

### Root Config Files

#### `index.html`
- **Purpose:** HTML entry point; loads `src/main.tsx` as a module; meta tags for PWA.
- **FRs:** FR-4.1 (PWA manifest link)
- **Dependencies:** None

#### `vite.config.ts`
- **Purpose:** Vite build configuration. Registers `@vitejs/plugin-react` and `vite-plugin-pwa`. Configures PWA manifest (name, icons, theme color, start_url).
- **FRs:** FR-4.1 (installable), FR-4.2 (offline caching via Workbox precache)
- **Dependencies:** `vite`, `@vitejs/plugin-react`, `vite-plugin-pwa`

#### `tailwind.config.ts`
- **Purpose:** Tailwind CSS configuration. Sets `content` glob to `./src/**/*.{ts,tsx}`. No custom theme extensions required for MVP.
- **FRs:** NFR-3 (responsive)
- **Dependencies:** `tailwindcss`

#### `tsconfig.json`
- **Purpose:** TypeScript compiler config. Sets `strict: true`, `target: "ES2020"`, `lib: ["ES2020", "DOM"]`, `module: "ESNext"`, `moduleResolution: "bundler"`, `jsx: "react-jsx"`.
- **FRs:** NFR-1 (TypeScript strict mode)
- **Dependencies:** None

#### `package.json`
- **Purpose:** Project manifest. Scripts: `dev`, `build`, `preview`, `test`, `lint`.
- **Key dependencies:** `react`, `react-dom`, `react-router-dom`, `firebase`, `@tanstack/react-query`, `tailwindcss`, `vite-plugin-pwa`.
- **Dev dependencies:** `vitest`, `@testing-library/react`, `@testing-library/user-event`, `@vitejs/plugin-react`, `typescript`, `eslint`.
- **Dependencies:** All packages above

#### `.env.example`
- **Purpose:** Documents required environment variables without committing secrets. Never `.env`.
- **Content:**
  ```
  VITE_FIREBASE_API_KEY=
  VITE_FIREBASE_AUTH_DOMAIN=
  VITE_FIREBASE_PROJECT_ID=
  VITE_FIREBASE_STORAGE_BUCKET=
  VITE_FIREBASE_MESSAGING_SENDER_ID=
  VITE_FIREBASE_APP_ID=
  ```
- **FRs:** Infrastructure (replaces `src/environments/firebase.ts`)
- **Dependencies:** None

#### `firestore.rules`
- **Purpose:** Firestore security rules. Enforces per-user data isolation (see Section 3).
- **FRs:** FR-3.1, FR-3.2 (server-side enforcement)
- **Dependencies:** None (deployed via Firebase CLI)

#### `firestore.indexes.json`
- **Purpose:** Declares composite indexes required for filtered + ordered queries.
- **Content:** Composite index on `(completed ASC, createdAt ASC)` for the `tasks/{uid}` collection group.
- **FRs:** FR-2.6 (filter queries)
- **Dependencies:** None (deployed via Firebase CLI)

---

### Source Files

#### `src/main.tsx`
- **Purpose:** React entry point. Renders `<App />` wrapped in `<QueryClientProvider>` (TanStack Query), `<BrowserRouter>` (React Router), and `<FirebaseProvider>` (auth context).
- **FRs:** All (bootstraps the app)
- **Imports:** `react`, `react-dom/client`, `react-router-dom`, `@tanstack/react-query`, `./contexts/FirebaseContext`, `./App`

#### `src/App.tsx`
- **Purpose:** Root component. Reads auth state from `useAuth()`. Renders routes:
  - `/` → `<AuthPanel />` (guarded: redirects to `/tasks` if authenticated)
  - `/tasks` → task UI (`<TaskForm />` + `<FilterTabs />` + `<TaskList />`) guarded by auth
  - Shows a full-screen loading indicator while auth state is resolving
  - Shows the app header (with sign-out button) when authenticated
- **FRs:** FR-1.3 (auth state persistence), FR-3.2 (auth guard), AC-1.3.2 (loading state)
- **Imports:** `react-router-dom`, `./hooks/useAuth`, `./components/*`

#### `src/firebase.ts`
- **Purpose:** Initialize Firebase app, Auth, and Firestore singletons. Exports `auth` and `db` instances.
- **Content:**
  ```typescript
  import { initializeApp } from 'firebase/app';
  import { getAuth } from 'firebase/auth';
  import { getFirestore } from 'firebase/firestore';

  const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    // ... other env vars
  };

  const app = initializeApp(firebaseConfig);
  export const auth = getAuth(app);
  export const db = getFirestore(app);
  ```
- **FRs:** All Firebase-dependent FRs (foundation)
- **Imports:** `firebase/app`, `firebase/auth`, `firebase/firestore`

---

#### `src/contexts/FirebaseContext.tsx`
- **Purpose:** React context provider that runs `onAuthStateChanged` once, auto-triggers `signInAnonymously` on null user, and exposes `{ user, loading, error }` to the tree.
- **FRs:** FR-1.1 (anonymous auto sign-in), FR-1.3 (auth persistence), AC-1.3.2 (loading state)
- **Exports:** `FirebaseProvider` (component), `useFirebase` (context hook — consumed by `useAuth`)
- **Imports:** `react`, `firebase/auth`, `./firebase` (auth singleton)
- **Internal logic:**
  ```
  useEffect([], () => {
    return onAuthStateChanged(auth, (user) => {
      if (user === null) {
        signInAnonymously(auth);  // auto anonymous sign-in
      } else {
        setUser(user);
        setLoading(false);
      }
    });
  });
  ```

---

#### `src/hooks/useAuth.ts`
- **Purpose:** Consumer hook that reads from `FirebaseContext` and provides sign-in/sign-out methods. Abstracts Firebase auth methods from components.
- **FRs:** FR-1.2 (social sign-in), FR-1.4 (sign-out)
- **Exports:** `useAuth()` returning `{ user, loading, error, signInWithGoogle, signInWithGithub, signInWithTwitter, signInWithFacebook, signOut }`
- **Imports:** `firebase/auth` (provider constructors, `signInWithPopup`, `signOut`), `./contexts/FirebaseContext`
- **Error handling:** Each `signInWithPopup` call catches and returns the error to the component (not swallowed) — fixes the legacy silent-error bug (AC-1.2.5)

#### `src/hooks/useTasks.ts`
- **Purpose:** Subscribes to the Firestore `/tasks/{uid}` collection via `onSnapshot`. Returns `{ tasks, loading, error }`. Unsubscribes on unmount.
- **FRs:** FR-2.2 (view task list), FR-2.2.4 (real-time updates)
- **Exports:** `useTasks(uid: string)` returning `{ tasks: Task[], loading: boolean, error: Error | null }`
- **Imports:** `firebase/firestore`, `react`, `../types/task`, `../firebase`
- **Internal logic:**
  ```
  useEffect([uid], () => {
    const q = query(
      collection(db, 'tasks', uid),
      orderBy('createdAt', 'asc')
    );
    return onSnapshot(q, (snapshot) => {
      setTasks(snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() })));
      setLoading(false);
    }, (err) => setError(err));
  });
  ```
- **Note:** All tasks are fetched in one subscription; filtering is done client-side in `useFilteredTasks` to avoid multiple Firestore listeners.

#### `src/hooks/useFilteredTasks.ts`
- **Purpose:** Derives the visible task list from `useTasks` output + the current filter value. Pure client-side filter — no additional Firestore queries.
- **FRs:** FR-2.6 (filter tasks)
- **Exports:** `useFilteredTasks(tasks: Task[], filter: 'all' | 'active' | 'completed')` returning `Task[]`
- **Imports:** `react` (useMemo), `../types/task`
- **Internal logic:** `useMemo` on tasks + filter:
  - `'all'` → return all tasks
  - `'active'` → `tasks.filter(t => !t.completed)`
  - `'completed'` → `tasks.filter(t => t.completed)`

---

#### `src/components/AuthPanel.tsx`
- **Purpose:** Sign-in page component. Renders five sign-in buttons (Anonymous, Google, GitHub, Twitter, Facebook). Displays error message if sign-in fails. On success, navigates to `/tasks`.
- **FRs:** FR-1.1 (anonymous), FR-1.2 (social sign-in), AC-1.2.5 (error display), AC-1.2.6 (navigate on success)
- **Imports:** `react`, `react-router-dom` (useNavigate), `../hooks/useAuth`
- **Internal logic:** Each button handler calls the appropriate `useAuth` method, catches errors and sets local `errorMessage` state, and calls `navigate('/tasks')` on success.

#### `src/components/TaskForm.tsx`
- **Purpose:** Create-task input form. Auto-focuses on mount (via `useRef` + `useEffect`). Submits on Enter, clears on Escape. Trims title; no-op on empty.
- **FRs:** FR-2.1 (create task) — all ACs
- **Imports:** `react`, `../hooks/useAuth` (for `user.uid`), `../lib/firestore` (createTask)
- **Props:** None (reads UID from `useAuth`)
- **Internal:** `<input ref={inputRef} onKeyDown={handleEscape} />` inside `<form onSubmit={handleSubmit}>`.

#### `src/components/TaskList.tsx`
- **Purpose:** Renders the list of `TaskItem` components. Receives the filtered task array as a prop. No logic beyond mapping.
- **FRs:** FR-2.2 (view task list)
- **Props:** `tasks: Task[]`, `uid: string`
- **Imports:** `react`, `./TaskItem`, `../types/task`

#### `src/components/TaskItem.tsx`
- **Purpose:** Single task row. Displays title + completion checkbox + edit icon + delete button. Manages local `editing` state and `editTitle` input value. On edit save: trim, guard (non-empty AND changed), call `updateTask`. Toggle and delete call Firestore helpers directly.
- **FRs:** FR-2.3 (toggle), FR-2.4 (delete), FR-2.5 (inline edit) — all ACs
- **Props:** `task: Task`, `uid: string`
- **Imports:** `react`, `../lib/firestore` (updateTask, deleteTask), `../types/task`
- **Internal logic for save:**
  ```typescript
  const handleSave = () => {
    const trimmed = editTitle.trim();
    if (trimmed.length && trimmed !== task.title) {
      updateTask(uid, task.id, { title: trimmed });
    }
    setEditing(false);
  };
  ```
- **Auto-focus on edit mode:** `useEffect([editing], () => { if (editing) editInputRef.current?.focus(); })`

#### `src/components/FilterTabs.tsx`
- **Purpose:** Renders three filter tabs (All / Active / Completed). Reads and writes `?filter` URL search param via `useSearchParams`. Highlights the active tab.
- **FRs:** FR-2.6 (filter tasks) — all ACs
- **Props:** None (reads from URL)
- **Imports:** `react`, `react-router-dom` (useSearchParams)
- **Internal logic:** Each tab is a `<button>` that calls `setSearchParams({ filter: value })`. Active tab determined by `searchParams.get('filter') ?? 'all'`.

---

#### `src/types/task.ts`
- **Purpose:** Canonical TypeScript type definitions for the Task domain.
- **FRs:** NFR-1 (TypeScript strict mode)
- **Exports:** `Task` interface, `NewTask` type
- **Imports:** `firebase/firestore` (Timestamp)
- **Content:**
  ```typescript
  import type { Timestamp } from 'firebase/firestore';

  export interface Task {
    id: string;
    title: string;
    completed: boolean;
    createdAt: Timestamp | null;
  }

  export type TaskUpdate = Partial<Pick<Task, 'title' | 'completed'>>;
  ```

#### `src/lib/firestore.ts`
- **Purpose:** Pure helper functions wrapping Firestore SDK calls. No React hooks. Directly callable from event handlers. Each function is a thin wrapper that imports `db` from `../firebase`.
- **FRs:** FR-2.1 (create), FR-2.3 (toggle), FR-2.4 (delete), FR-2.5 (edit)
- **Exports:**
  ```typescript
  createTask(uid: string, title: string): Promise<DocumentReference>
  updateTask(uid: string, taskId: string, changes: TaskUpdate): Promise<void>
  deleteTask(uid: string, taskId: string): Promise<void>
  ```
- **Imports:** `firebase/firestore`, `../firebase` (db), `../types/task`
- **`createTask` implementation:**
  ```typescript
  addDoc(collection(db, 'tasks', uid), {
    title,
    completed: false,
    createdAt: serverTimestamp(),
  });
  ```

---

## 3. Firebase Security Rules (Firestore)

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Tasks: each user can only read and write their own task documents
    match /tasks/{uid}/{taskId} {
      allow read, write: if request.auth != null && request.auth.uid == uid;
    }

    // Deny all other paths by default (Firestore default is deny)
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

**Rules rationale:**
- `request.auth != null` — rejects unauthenticated requests (anonymous users have a non-null `auth` with a UID)
- `request.auth.uid == uid` — the path segment `{uid}` must match the caller's UID; no cross-user reads or writes
- Anonymous users are fully supported: Firebase assigns them a UID, so `request.auth` is non-null
- The wildcard deny-all at the bottom is defensive but redundant (Firestore denies by default); included for explicitness

**Firestore indexes (`firestore.indexes.json`):**
```json
{
  "indexes": [
    {
      "collectionGroup": "tasks",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "completed", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "ASCENDING" }
      ]
    }
  ]
}
```
This composite index is required for future use if server-side filtered queries are added. For the current client-side filter approach (one `onSnapshot` + `useMemo`), only a single-field `createdAt` index is needed (auto-created by Firestore).

---

## 4. State Flow Diagram

```
Firebase Firestore
      │
      │  onSnapshot(query(collection(db,'tasks',uid), orderBy('createdAt')))
      │  fires on: mount, any doc add/update/delete
      ▼
useTasks(uid)                                    [src/hooks/useTasks.ts]
  useState: tasks[], loading, error
      │
      │  tasks[] (all tasks for user)
      ▼
useFilteredTasks(tasks, filter)                  [src/hooks/useFilteredTasks.ts]
  useMemo: derives visible[] from filter URL param
      │
      │  visibleTasks[]
      ▼
<TaskList tasks={visibleTasks} uid={uid}>        [src/components/TaskList.tsx]
      │
      │  maps tasks[] → <TaskItem>
      ▼
<TaskItem task={task} uid={uid}>                 [src/components/TaskItem.tsx]
  local state: editing (bool), editTitle (string)
      │
      ├─── checkbox click  ──► updateTask(uid, task.id, { completed: !task.completed })
      │                              │
      ├─── delete click   ──► deleteTask(uid, task.id)
      │                              │
      └─── edit save      ──► updateTask(uid, task.id, { title: trimmed })
                                     │
                         [src/lib/firestore.ts: updateDoc / deleteDoc]
                                     │
                                     ▼
                            Firestore write committed
                                     │
                                     ▼
                         onSnapshot fires with updated snapshot
                                     │
                                     ▼
                         useTasks updates tasks[] state
                                     │
                                     ▼
                         React re-renders TaskList → TaskItem
```

**Key invariant:** There is one `onSnapshot` listener per authenticated session (unsubscribed on `useTasks` unmount). All UI mutations go through `lib/firestore.ts` helpers → Firestore → onSnapshot re-fires → React state update → re-render. No local state mutation of the tasks array outside of the snapshot callback.

---

## 5. Auth Flow

```
Browser loads app
      │
      ▼
FirebaseProvider mounts                          [src/contexts/FirebaseContext.tsx]
  setLoading(true)
  registers onAuthStateChanged(auth, handler)
      │
      ▼
<App /> renders loading spinner (auth.loading === true)
      │
      │  [Firebase SDK checks localStorage for persisted session]
      │
      ├─── [Session found] ──► onAuthStateChanged fires with User
      │                              setUser(user), setLoading(false)
      │                              App renders: redirect / → /tasks
      │
      └─── [No session] ──► onAuthStateChanged fires with null
                                   signInAnonymously(auth) called automatically
                                         │
                                         ▼
                                   onAuthStateChanged fires again with anonymous User
                                         setUser(anonUser), setLoading(false)
                                         App renders: / (sign-in page, user is authed anonymously)
                                               │
                                               ▼
                                    User sees <AuthPanel /> sign-in buttons
                                    (anonymous session is active but sign-in shown for social upgrade)
                                               │
                             User clicks social provider button
                                               │
                                               ▼
                                    useAuth.signInWith*() called
                                    signInWithPopup(auth, provider)
                                               │
                                    ├─── success ──► onAuthStateChanged fires with social User
                                    │                setUser(socialUser)
                                    │                navigate('/tasks')
                                    │
                                    └─── error ──► setError(message)
                                                   AuthPanel shows error message
                                                   user stays on sign-in page

      [On /tasks route]
      useTasks(user.uid) mounts → onSnapshot subscribed
      Tasks load and render in real-time

      [User clicks Sign Out]
      signOut(auth) called
      onAuthStateChanged fires with null
      signInAnonymously() called automatically (new anon session)
      App renders sign-in page again
```

**Notes:**
- The auto-anonymous sign-in on null means the user always has a Firebase UID, even before choosing a social provider. This ensures tasks can be created immediately without requiring social sign-in.
- After social sign-in, `user.uid` changes (from anonymous UID to social UID). Tasks created under the anonymous UID are not automatically migrated. This matches the legacy behavior — the legacy app also used a new UID after social sign-in.
- Sign-out leads immediately to a new anonymous session (via the `null` → `signInAnonymously` trigger), so the task list is always scoped to the current UID.
