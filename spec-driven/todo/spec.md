# Specification: Todo App Migration
> Domain: `todo` — migrating `todo-angular-firebase-demo` to React 18 + TypeScript + Vite + Firebase v10

---

## 1. Functional Requirements

### EP-1: Authentication

#### FR-1.1: Anonymous Sign-In

The app automatically signs in the user anonymously on first visit if no Firebase Auth session exists.

**AC-1.1.1 — Auto anonymous sign-in on first visit**
- Given: The user visits the app for the first time (no persisted Firebase Auth session)
- When: `onAuthStateChanged` fires with `null`
- Then: `signInAnonymously()` is called automatically and the user is signed in with a Firebase-assigned UID

**AC-1.1.2 — No re-trigger for existing session**
- Given: The user has a persisted Firebase Auth session (anonymous or social)
- When: `onAuthStateChanged` fires with a non-null user
- Then: `signInAnonymously()` is NOT called; the existing user is used as-is

**AC-1.1.3 — Anonymous user has a UID**
- Given: The user is signed in anonymously
- When: Auth state is observed
- Then: `user.uid` is a non-empty string and can be used to scope Firestore task reads/writes

#### FR-1.2: Social Sign-In (Google, GitHub, Twitter, Facebook via popup)

The user can upgrade from anonymous or sign in directly with a social provider.

**AC-1.2.1 — Google sign-in via popup**
- Given: The user is on the sign-in panel
- When: They click the "Google" button
- Then: `signInWithPopup(GoogleAuthProvider)` is called and on success the user is authenticated

**AC-1.2.2 — GitHub sign-in via popup**
- Given: The user is on the sign-in panel
- When: They click the "GitHub" button
- Then: `signInWithPopup(GithubAuthProvider)` is called and on success the user is authenticated

**AC-1.2.3 — Twitter sign-in via popup**
- Given: The user is on the sign-in panel
- When: They click the "Twitter" button
- Then: `signInWithPopup(TwitterAuthProvider)` is called and on success the user is authenticated

**AC-1.2.4 — Facebook sign-in via popup**
- Given: The user is on the sign-in panel
- When: They click the "Facebook" button
- Then: `signInWithPopup(FacebookAuthProvider)` is called and on success the user is authenticated

**AC-1.2.5 — Sign-in error is surfaced to the user**
- Given: A social sign-in attempt fails (popup closed, provider error, network error)
- When: `signInWithPopup` rejects
- Then: An error message is displayed in the UI; the user is NOT navigated away from the sign-in panel
- Note: This fixes the legacy bug where errors were swallowed and the app silently navigated to `/tasks`

**AC-1.2.6 — Successful sign-in navigates to task list**
- Given: The user clicks any sign-in button
- When: The sign-in promise resolves successfully
- Then: The user is navigated to the task list view (`/tasks`)

#### FR-1.3: Auth State Persistence

**AC-1.3.1 — Session survives page refresh**
- Given: The user is signed in (any provider)
- When: The page is reloaded
- Then: `onAuthStateChanged` fires with the same user; the user does not need to sign in again
- Note: Firebase Auth SDK handles local persistence by default; no extra configuration is required

**AC-1.3.2 — Auth state is available before task list renders**
- Given: The app is loading
- When: `onAuthStateChanged` has not yet fired (initial loading state)
- Then: A loading indicator is shown; neither the sign-in panel nor the task list renders until auth state is resolved

#### FR-1.4: Sign Out

**AC-1.4.1 — Sign out clears session**
- Given: The user is authenticated
- When: They click the "Sign Out" button in the app header
- Then: `signOut()` is called, the Firebase Auth session is cleared, and the user is redirected to the sign-in page

**AC-1.4.2 — Sign-out button is only visible when authenticated**
- Given: The app header is rendered
- When: The user is authenticated
- Then: The sign-out button is visible
- When: The user is not authenticated (impossible in normal flow, but guarded anyway)
- Then: The sign-out button is not rendered

---

### EP-2: Task Management

#### FR-2.1: Create Task

**AC-2.1.1 — Task form is auto-focused on load**
- Given: The task list view has mounted
- When: The DOM is ready
- Then: The title input has browser focus (equivalent of `autofocus` attribute)

**AC-2.1.2 — Enter submits a new task**
- Given: The task form input has a non-empty title
- When: The user presses Enter (form submit)
- Then: A new task document is created in Firestore with `{ title: trimmedTitle, completed: false, createdAt: serverTimestamp() }`; the input is cleared

**AC-2.1.3 — Empty title is a no-op**
- Given: The task form input is empty or contains only whitespace
- When: The user presses Enter
- Then: No Firestore write is made; the input is cleared

**AC-2.1.4 — Title is trimmed before save**
- Given: The user types `"  buy milk  "` in the task form
- When: They press Enter
- Then: The task is saved with `title = "buy milk"` (leading/trailing whitespace stripped)

**AC-2.1.5 — Escape clears the input**
- Given: The task form input contains text
- When: The user presses Escape
- Then: The input is cleared without submitting

**AC-2.1.6 — New task is completed = false by default**
- Given: A new task is created
- When: The task document is read from Firestore
- Then: `completed` equals `false`

**AC-2.1.7 — createdAt is server-assigned**
- Given: A new task is created
- When: The task document is read from Firestore
- Then: `createdAt` is a Firestore `Timestamp` set by the server (not the client clock)

#### FR-2.2: View Task List

**AC-2.2.1 — Tasks are ordered by creation time**
- Given: The user has multiple tasks
- When: The task list renders
- Then: Tasks appear in ascending `createdAt` order (oldest first)

**AC-2.2.2 — Each task row shows title and completion checkbox**
- Given: A task exists in the list
- When: The task item renders
- Then: The task title is visible; a checkbox reflecting the `completed` state is visible

**AC-2.2.3 — Empty state when no tasks**
- Given: The user has no tasks (or no tasks match the current filter)
- When: The task list renders
- Then: The list area is empty (no error, no tasks rendered)

**AC-2.2.4 — Real-time updates**
- Given: The task list is visible
- When: A Firestore document is added, updated, or deleted (from same or another session)
- Then: The UI reflects the change without a page reload (onSnapshot listener)

#### FR-2.3: Toggle Task Completion

**AC-2.3.1 — Checkbox toggles completed state**
- Given: A task item is rendered with `completed = false`
- When: The user clicks the checkbox
- Then: `updateDoc` is called with `{ completed: true }`; the checkbox reflects the new state

**AC-2.3.2 — Toggle works bidirectionally**
- Given: A task item is rendered with `completed = true`
- When: The user clicks the checkbox
- Then: `updateDoc` is called with `{ completed: false }`

#### FR-2.4: Delete Task

**AC-2.4.1 — Delete button removes the task**
- Given: A task item is rendered
- When: The user clicks the delete button for that task
- Then: `deleteDoc` is called for that document; the task disappears from the list

#### FR-2.5: Inline Edit Task Title

**AC-2.5.1 — Clicking the edit icon enters edit mode**
- Given: A task item is in view mode
- When: The user clicks the edit (pencil) icon
- Then: The title text is replaced by an input field pre-filled with the current title; the input receives focus

**AC-2.5.2 — Enter saves the edited title**
- Given: The task item is in edit mode and the user has changed the title
- When: The user presses Enter
- Then: `updateDoc` is called with `{ title: trimmedNewTitle }`; the item returns to view mode showing the new title

**AC-2.5.3 — Blur saves the edited title**
- Given: The task item is in edit mode
- When: The input loses focus (blur event)
- Then: The same save logic as Enter fires (trim + guard + updateDoc if changed)

**AC-2.5.4 — Empty title is a no-op on save**
- Given: The task item is in edit mode and the user clears the input
- When: The user presses Enter or blurs
- Then: No Firestore write is made; the item returns to view mode with the original title unchanged

**AC-2.5.5 — Unchanged title is a no-op on save**
- Given: The task item is in edit mode and the user has not modified the title
- When: The user presses Enter or blurs
- Then: No Firestore write is made (optimization: skip DB round-trip for identical values)
- Note: This preserves the legacy `title !== this.task.title` guard

**AC-2.5.6 — Title is trimmed before save**
- Given: The user edits the title to `"  new title  "`
- When: Enter is pressed
- Then: `updateDoc` is called with `{ title: "new title" }` (trimmed)

#### FR-2.6: Filter Tasks

**AC-2.6.1 — Filter state is stored in URL search params**
- Given: The user is on the task list
- When: They click a filter tab ("All", "Active", "Completed")
- Then: The URL search param `?filter=all|active|completed` is updated; the browser back button restores the previous filter

**AC-2.6.2 — "All" tab shows all tasks**
- Given: The filter is "All" (default, no search param or `?filter=all`)
- When: The task list renders
- Then: All tasks for the current user are displayed regardless of `completed` state

**AC-2.6.3 — "Active" tab shows only incomplete tasks**
- Given: The filter is "Active" (`?filter=active`)
- When: The task list renders
- Then: Only tasks with `completed = false` are shown

**AC-2.6.4 — "Completed" tab shows only completed tasks**
- Given: The filter is "Completed" (`?filter=completed`)
- When: The task list renders
- Then: Only tasks with `completed = true` are shown

**AC-2.6.5 — Default filter is "All"**
- Given: The user navigates to `/tasks` with no search params
- When: The task list renders
- Then: The "All" tab is active and all tasks are shown

**AC-2.6.6 — Active filter tab is visually indicated**
- Given: A filter tab is selected
- When: The tab bar renders
- Then: The active tab has a distinct visual style (e.g., underline or highlight)

#### FR-2.7: Bulk Actions

No bulk "mark all as..." action is required. This feature was prototyped in the legacy codebase (`feat(tasks): mark all as...` commit) but was not carried forward into the stable Angular CLI version and is explicitly out of scope for this migration.

---

### EP-3: Data Isolation

#### FR-3.1: Per-User Task Isolation

**AC-3.1.1 — Tasks are scoped to the authenticated user**
- Given: User A and User B are each authenticated
- When: Both users load the task list
- Then: User A sees only their tasks (`/tasks/{uidA}`); User B sees only their tasks (`/tasks/{uidB}`)

**AC-3.1.2 — Firestore security rules enforce ownership server-side**
- Given: A malicious client attempts to read `/tasks/{otherUid}`
- When: The Firestore request is evaluated by security rules
- Then: The request is denied (HTTP 403); no data is returned

**AC-3.1.3 — Anonymous users are fully supported**
- Given: An anonymous user is signed in
- When: They create, read, update, or delete tasks
- Then: All operations succeed under `/tasks/{anonymousUid}` with the same behavior as social auth users

#### FR-3.2: Auth Guard

**AC-3.2.1 — Unauthenticated users are redirected to sign-in**
- Given: The user is not authenticated and navigates to `/tasks`
- When: The route guard evaluates
- Then: The user is redirected to `/` (sign-in page)

**AC-3.2.2 — Authenticated users are redirected away from sign-in**
- Given: The user is already authenticated and navigates to `/`
- When: The route guard evaluates
- Then: The user is redirected to `/tasks`

---

### EP-4: PWA / Offline

#### FR-4.1: Installable App

**AC-4.1.1 — Web App Manifest is present**
- Given: The app is served over HTTPS
- When: The browser evaluates the manifest
- Then: The app meets PWA installability criteria (name, icons, start_url, display)

**AC-4.1.2 — Service worker is registered**
- Given: The production build is served
- When: The page loads
- Then: A service worker is registered and active

#### FR-4.2: Offline Asset Caching

**AC-4.2.1 — Static assets are cached after first visit**
- Given: The user has visited the app at least once while online
- When: The user goes offline and reloads the page
- Then: The shell (HTML, JS, CSS) loads from the service worker cache without a network request

**AC-4.2.2 — Firestore data is not guaranteed offline**
- Given: The user is offline
- When: They attempt to create or modify tasks
- Then: Firestore's built-in offline persistence handles the operation (queued for sync); this is not the service worker's responsibility

---

## 2. Non-Functional Requirements

### NFR-1: TypeScript Strict Mode
- `strict: true` in `tsconfig.json` (implies `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`, etc.)
- No `any` casts without explicit comment justification
- All Firebase return types are fully typed

### NFR-2: Zero Console Errors in Production
- No unhandled Promise rejections
- No React key warnings
- No Firebase permission-denied errors for valid authenticated operations
- Auth errors are caught and surfaced in UI (not swallowed to console)

### NFR-3: Responsive Design
- App is usable on viewport widths from 320px (iPhone SE) to 1440px (desktop)
- Tailwind CSS utility classes are used; no custom breakpoints unless necessary
- Touch targets (buttons, checkboxes) are at minimum 44×44px

### NFR-4: Performance
- Vite production build with code splitting
- Lighthouse Performance score ≥ 80 on mobile simulation

---

## 3. Out of Scope

The following features are explicitly NOT part of this migration:

| Item | Reason |
|---|---|
| Server-side rendering (SSR/SSG) | Not in the legacy app; adds complexity without clear need |
| Multi-user collaboration / sharing | Legacy app is strictly single-user per UID |
| Task due dates, priorities, tags, subtasks | Not in legacy; out of scope per product decision |
| Task reordering (drag-and-drop) | Not in legacy |
| Pagination / infinite scroll | Legacy loads all tasks; acceptable for a personal todo app |
| Backend beyond Firebase | Legacy used Firebase-only; no custom API server |
| Push notifications | Not in legacy |
| "Mark all as..." bulk action | Prototyped in legacy but dropped; not required |
| Email/password auth | Legacy did not include it |
| Account deletion or data export | Out of scope |

---

## 4. Data Model

### Firestore Collection Path

```
/tasks/{uid}/{taskId}
```

Where `uid` is the Firebase Auth user UID (string), and `taskId` is a Firestore auto-generated document ID.

### Task Document Fields

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `id` | `string` | virtual | (doc.id) | Not stored in document; taken from `DocumentSnapshot.id` at read time |
| `title` | `string` | Yes | — | Trimmed before write; never empty |
| `completed` | `boolean` | Yes | `false` | Set at creation; toggled via update |
| `createdAt` | `Timestamp` | Yes | `serverTimestamp()` | Server-assigned sentinel; used for ordering |

### TypeScript Type (canonical)

```typescript
// src/types/task.ts
import { Timestamp } from 'firebase/firestore';

export interface Task {
  id: string;           // Firestore doc.id — not stored in document
  title: string;
  completed: boolean;
  createdAt: Timestamp | null;  // null transiently before server write confirms
}

export type NewTask = Omit<Task, 'id' | 'createdAt'> & {
  createdAt: ReturnType<typeof import('firebase/firestore').serverTimestamp>;
};
```

---

## 5. API Surface (Firebase Operations)

All Firebase interactions are enumerated below. No REST API exists; all backend calls go through the Firebase JS SDK v10 (modular).

### 5.1 Auth Operations (`firebase/auth`)

| Operation | SDK Call | Trigger | Notes |
|---|---|---|---|
| Observe auth state | `onAuthStateChanged(auth, callback)` | App mount (once, persistent listener) | Central auth gate; drives routing and UID for task queries |
| Sign in anonymously | `signInAnonymously(auth)` | `onAuthStateChanged` fires with `null` on first visit | Auto-triggered; not user-initiated |
| Sign in with Google | `signInWithPopup(auth, new GoogleAuthProvider())` | User clicks "Google" button | |
| Sign in with GitHub | `signInWithPopup(auth, new GithubAuthProvider())` | User clicks "GitHub" button | |
| Sign in with Twitter | `signInWithPopup(auth, new TwitterAuthProvider())` | User clicks "Twitter" button | |
| Sign in with Facebook | `signInWithPopup(auth, new FacebookAuthProvider())` | User clicks "Facebook" button | |
| Sign out | `signOut(auth)` | User clicks "Sign Out" in header | |

### 5.2 Firestore Operations (`firebase/firestore`)

All operations target the collection `tasks/{uid}` where `uid` is the authenticated user's UID.

| Operation | SDK Call | Trigger | Notes |
|---|---|---|---|
| Subscribe to all tasks | `onSnapshot(collection(db, 'tasks', uid))` | `useTasks` hook mounts | Real-time listener; auto-unsubscribed on unmount |
| Subscribe to active tasks | `onSnapshot(query(collection(...), where('completed', '==', false), orderBy('createdAt')))` | Filter = "Active" | |
| Subscribe to completed tasks | `onSnapshot(query(collection(...), where('completed', '==', true), orderBy('createdAt')))` | Filter = "Completed" | |
| Create task | `addDoc(collection(db, 'tasks', uid), { title, completed: false, createdAt: serverTimestamp() })` | User submits task form | Auto-generates document ID |
| Update task (toggle / edit title) | `updateDoc(doc(db, 'tasks', uid, taskId), changes)` | Checkbox click or inline edit save | `changes` is partial: `{ completed }` or `{ title }` |
| Delete task | `deleteDoc(doc(db, 'tasks', uid, taskId))` | User clicks delete button | Hard delete; no soft-delete |

### 5.3 Composite Query for Ordering

When filter = "All", all tasks are fetched with `orderBy('createdAt', 'asc')`. Firestore requires a composite index on `(completed, createdAt)` for the filtered + ordered queries — this index must be defined in `firestore.indexes.json`.

---

## 6. Acceptance Test Matrix

The following table cross-references each FR with its ACs and the minimum test type required:

| FR | AC | Test Type | Priority |
|---|---|---|---|
| FR-1.1 | AC-1.1.1, AC-1.1.2, AC-1.1.3 | Unit (useAuth hook) | High |
| FR-1.2 | AC-1.2.1–1.2.5 | Unit (useAuth + AuthPanel) | High |
| FR-1.3 | AC-1.3.1, AC-1.3.2 | Integration | Medium |
| FR-1.4 | AC-1.4.1, AC-1.4.2 | Unit (useAuth + header) | Low |
| FR-2.1 | AC-2.1.1–2.1.7 | Unit (TaskForm) | High |
| FR-2.2 | AC-2.2.1–2.2.4 | Unit (TaskList) | High |
| FR-2.3 | AC-2.3.1, AC-2.3.2 | Unit (TaskItem) | High |
| FR-2.4 | AC-2.4.1 | Unit (TaskItem) | Medium |
| FR-2.5 | AC-2.5.1–2.5.6 | Unit (TaskItem) | High |
| FR-2.6 | AC-2.6.1–2.6.6 | Unit (FilterTabs + useTasks) | High |
| FR-3.1 | AC-3.1.1–3.1.3 | Firestore rules test + Unit | High |
| FR-3.2 | AC-3.2.1, AC-3.2.2 | Unit (route guard / App) | Medium |
| FR-4.1 | AC-4.1.1, AC-4.1.2 | Build artifact check | Low |
| FR-4.2 | AC-4.2.1, AC-4.2.2 | Manual / Lighthouse | Low |
