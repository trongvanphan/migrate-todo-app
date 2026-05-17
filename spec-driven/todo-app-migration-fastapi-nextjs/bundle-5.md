# Bundle B-5: Frontend Task UI

> Stage: depth | Parallel: no (depends on B-4) | Files: frontend/app/tasks/page.tsx, frontend/app/tasks/layout.tsx, frontend/components/TasksContainer.tsx, frontend/components/TaskForm.tsx, frontend/components/TaskList.tsx, frontend/components/TaskItem.tsx, frontend/jest.config.ts, frontend/jest.setup.ts, frontend/components/__tests__/TaskForm.test.tsx, frontend/components/__tests__/TaskItem.test.tsx

**Bundle Verify**: Authenticated user can create, toggle, edit, and delete tasks; filter tabs change the visible task set.
- **Level**: e2e (manual)
- **Given**: Both servers running; user authenticated (guest session)
- **Action**: Create 3 tasks → toggle one complete → click "Completed" filter → edit another's title → delete the third
- **Outcome**: Only completed task shown in Completed filter; edited title persists; deleted task absent

---

## Context

**Architecture Decisions:** AD-6 (server page + client container), AD-7 (refetch-after-mutate), AD-8 (Link filter tabs)

**Findings:** F-16 (server searchParams → client prop), F-17 (TanStack Query v5 invalidateQueries), F-18 (Link tabs, no useSearchParams), F-19 (useRef + useEffect autoFocus), F-20 (TanStack Query v5 API)

**Standards:** S-3, S-4, S-7, S-8 (all mutations invalidate ['tasks']), S-9 (api.ts only)

**Relevant ACs:** AC-4.1–AC-4.4, AC-5.1–AC-5.3, AC-6.1–AC-6.4, AC-7.1–AC-7.3, AC-8.1–AC-8.5, AC-9.1–AC-9.2, AC-11.1–AC-11.2

---

## STEPs

### STEP-18: Tasks page (Server) + TasksContainer (Client)
**Trace:** `[FR-5 -> AC-5.1], [FR-5 -> AC-5.2], [FR-6 -> AC-6.1], [FR-6 -> AC-6.2], [FR-6 -> AC-6.3], [FR-6 -> AC-6.4]` | **Informed by:** AD-6, AD-8, F-16 | **Effort:** M

**Files:**
- `todo-app-migrated/frontend/app/tasks/page.tsx` — create
- `todo-app-migrated/frontend/app/tasks/layout.tsx` — create
- `todo-app-migrated/frontend/components/TasksContainer.tsx` — create

**Intent:** `page.tsx` reads `searchParams.completed` synchronously — only valid in Server Components (Next.js 14). Do NOT add 'use client'. `queryKey: ['tasks', completed]` ensures refetch on filter change.

**Implementation guidance:**
1. `page.tsx`: Server Component; `{ searchParams }: { searchParams: { completed?: string } }`; render `<TasksContainer completed={searchParams.completed} />`
2. `layout.tsx` (tasks): wraps children with `<Header />`
3. `TasksContainer.tsx`: `'use client'`; `useQuery({ queryKey: ['tasks', completed], queryFn: () => api.getTasks(completed) })`; pass mutation handlers to TaskForm + TaskList

**Verify:**
- Level: integration | Given: tasks in DB | Action: render with `completed="false"` | Outcome: getTasks("false") called; empty list renders without error

> **Standards:** S-3, S-4, S-7, S-8, S-9

**Dependencies:** Depends on STEP-14, STEP-15

---

### STEP-19: TaskForm component
**Trace:** `[FR-4 -> AC-4.1], [FR-4 -> AC-4.2], [FR-4 -> AC-4.3], [FR-4 -> AC-4.4]` | **Informed by:** AD-7, F-17 | **Effort:** S

**Files:**
- `todo-app-migrated/frontend/components/TaskForm.tsx` — create

**Intent:** Blank title guard must trim before check (`" ".trim().length === 0`). After create, clear AND re-focus input. No API call on empty title — no error toast (matches source behavior).

**Implementation guidance:**
1. `'use client'`; `useState('')` for title; `useRef<HTMLInputElement>` for input
2. Mutation `onSuccess`: `setTitle(''); inputRef.current?.focus(); queryClient.invalidateQueries({ queryKey: ['tasks'] })`
3. `onSubmit`: `if (!title.trim()) return; mutation.mutate()`
4. Escape: `setTitle('')`
5. Style: full-width, large font (`text-2xl sm540:text-3xl`), bottom border only

**Verify:**
- Level: unit | Given: TaskForm rendered | Action: submit empty | Outcome: createTask NOT called; valid submit → called; Escape → cleared

> **Standards:** S-3, S-4, S-7, S-8, S-9

**Dependencies:** Depends on STEP-15; parallel with STEP-20, STEP-21

---

### STEP-20: TaskList component + filter tabs
**Trace:** `[FR-5 -> AC-5.1], [FR-6 -> AC-6.1], [FR-6 -> AC-6.2], [FR-6 -> AC-6.3], [FR-6 -> AC-6.4], [FR-11 -> AC-11.1], [FR-11 -> AC-11.2]` | **Informed by:** AD-8, F-18 | **Effort:** S

**Files:**
- `todo-app-migrated/frontend/components/TaskList.tsx` — create

**Intent:** Filter tabs are `<Link>` — no `useSearchParams()`. Active state from prop. Responsive: `text-lg sm540:text-2xl` for task items, `py-3 sm540:py-4` spacing.

**Implementation guidance:**
1. `'use client'`; props: `tasks, completed, onUpdate, onDelete`
2. Three `<Link>` tabs: `/tasks`, `/tasks?completed=false`, `/tasks?completed=true`
3. Active: compare `completed` prop to tab value; apply highlight class
4. Empty state: `{tasks.length === 0 && <p>No tasks</p>}`

**Verify:**
- Level: inspection | Given: TaskList.tsx | Action: `grep -n "useSearchParams" components/TaskList.tsx` | Outcome: 0 matches

> **Standards:** S-3, S-4, S-7, S-9

**Dependencies:** Depends on STEP-18

---

### STEP-21: TaskItem component (toggle, inline edit, delete)
**Trace:** `[FR-7 -> AC-7.1], [FR-7 -> AC-7.2], [FR-7 -> AC-7.3], [FR-8 -> AC-8.1], [FR-8 -> AC-8.2], [FR-8 -> AC-8.3], [FR-8 -> AC-8.4], [FR-8 -> AC-8.5], [FR-9 -> AC-9.1], [FR-9 -> AC-9.2]` | **Informed by:** F-17, F-19, AD-7 | **Effort:** L

**Files:**
- `todo-app-migrated/frontend/components/TaskItem.tsx` — create

**Intent:** `useRef + useEffect([isEditing])` — not HTML autoFocus (SSR-unreliable). Blur saves only if `title changed AND non-empty`. Escape cancels without save. Strikethrough via Tailwind `line-through`. All mutations invalidate `['tasks']`.

**Implementation guidance:**
1. `isEditing` state; `editTitle` state; `inputRef` useRef; `useEffect(() => { if (isEditing) inputRef.current?.focus() }, [isEditing])`
2. Toggle: `onUpdate({ completed: !task.completed })`
3. `handleSave`: `if (editTitle.trim() && editTitle !== task.title) { onUpdate({ title: editTitle.trim() }) }; setIsEditing(false)`
4. Escape: `setEditTitle(task.title); setIsEditing(false)` — no onUpdate
5. `onBlur` calls `handleSave`; Escape `onKeyDown` must prevent blur-save via flag or `e.preventDefault()`
6. Completed styling: `line-through text-gray-500` when `task.completed`

**Verify:**
- Level: unit | Given: task with title "Buy milk" | Action: blur with empty title | Outcome: onUpdate NOT called; blur unchanged → NOT called; Escape → no call; blur changed → called

> **Standards:** S-3, S-4, S-7, S-8, S-9

**Dependencies:** Depends on STEP-18, STEP-15

---

### STEP-22: Frontend test suite
**Trace:** `MANUAL -> Test for STEP-18, STEP-19, STEP-20, STEP-21` | **Effort:** M

**Files:**
- `todo-app-migrated/frontend/jest.config.ts` — create
- `todo-app-migrated/frontend/jest.setup.ts` — create
- `todo-app-migrated/frontend/components/__tests__/TaskForm.test.tsx` — create
- `todo-app-migrated/frontend/components/__tests__/TaskItem.test.tsx` — create

**Intent:** Mock api.ts and next-auth/react. Test AC-8.3, AC-8.4, AC-8.5 (the non-obvious blur conditions) and AC-4.3 (empty submit).

**Implementation guidance:**
1. `jest.config.ts`: jsdom environment, @/ alias, setupFiles
2. `jest.mock('@/lib/api')` + `jest.mock('next-auth/react')`
3. `TaskForm.test.tsx`: empty submit (not called), valid submit (called), Escape (state reset)
4. `TaskItem.test.tsx`: blur empty (not called), blur unchanged (not called), Escape (no call), blur changed (called)

**Verify:**
- Level: unit | Given: `npm test` | Action: run | Outcome: all pass; TaskItem blur-unchanged test passes

> **Standards:** S-3

**Dependencies:** Depends on STEP-19, STEP-21
