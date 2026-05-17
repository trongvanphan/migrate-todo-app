# Specification: Todo App Migration — FastAPI + Next.js

**Slug:** `todo-app-migration-fastapi-nextjs`
**Version:** 1.0
**Status:** Draft
**Created:** 2026-05-16

---

## Overview

### Current State

A functional Angular 4 + Firebase SPA (`todo-angular-firebase-demo/`) that allows authenticated users to create, view, filter, edit, and delete personal todo tasks. Authentication is provided by Firebase Auth (Google, GitHub, Twitter, Facebook, Anonymous). Task data is stored in Firebase Realtime Database at `/tasks/{uid}` with per-user isolation enforced by Firebase Security Rules.

### Problem Statement

The app depends on Angular 4 (EOL), AngularFire2 (legacy), and Firebase (vendor lock-in). The goal is to reproduce all existing functionality on a modern, independently deployable stack: **Python FastAPI** backend + **Next.js 14 (App Router)** frontend.

### Primary Goal

Achieve full functional parity with the legacy app on the new stack, with zero dependency on Firebase or Angular.

---

## Users

| User | Description |
|---|---|
| Authenticated user | Signs in via OAuth (Google / GitHub / Twitter / Facebook) or as a guest and manages their personal task list |
| Anonymous/guest user | Signs in without a named account; has their own session-scoped task data |

---

## Scope

### In Scope

- Full authentication flow: sign-in (5 providers), route protection, sign-out
- Complete task CRUD: create, list, toggle completion, inline edit title, delete
- Filter tasks by status: All / Active / Completed (URL-reflected)
- Per-user data isolation (each user sees only their own tasks)
- Responsive UI (mobile + desktop, matching original breakpoints)
- Monorepo structure: `todo-app-migrated/frontend/` (Next.js) + `todo-app-migrated/backend/` (FastAPI)

### Out of Scope / Non-Goals

- **Data migration:** Existing Firebase task data will NOT be imported into SQLite. Fresh start.
- **CI/CD pipeline:** No CircleCI, GitHub Actions, or deployment configuration.
- **Real-time sync:** No WebSockets or live cross-tab updates. REST polling only.
- **Service Worker / PWA:** No offline caching (original used sw-precache).
- **Email/password auth:** Only OAuth + anonymous sign-in supported.

---

## Constraints

- Backend: Python FastAPI, SQLite (via SQLAlchemy), JWT (HS256, 30-day expiry)
- Frontend: Next.js 14 App Router, NextAuth.js, Tailwind CSS, TypeScript
- Auth: NextAuth.js handles OAuth; exchanges provider identity with FastAPI for app-level JWT
- No Firebase SDK on either side

---

## Assumptions

- OAuth app credentials (Google, GitHub, Twitter, Facebook) will be provisioned by the developer and stored in `.env.local` / `.env`
- SQLite is sufficient for the target environment (single-file, no separate DB server needed)
- Anonymous sign-in is implemented via NextAuth.js `CredentialsProvider` calling `POST /auth/anonymous`

---

## Functional Requirements

### FR-1: User Authentication — Sign In (Must Have)

Users can sign in using any of five methods: Google, GitHub, Twitter, Facebook (OAuth via NextAuth.js), or anonymously (guest session via CredentialsProvider → `POST /auth/anonymous`).

**Acceptance Criteria:**

- **AC-1.1:** Given I am on `/` (unauthenticated), when I click a named provider button (Google, GitHub, Twitter, or Facebook), then the OAuth popup opens and upon success I am navigated to `/tasks`.
- **AC-1.2:** Given I click "Continue as guest," when the anonymous session is created, then I am navigated to `/tasks` with a valid JWT session.
- **AC-1.3:** Given the OAuth provider returns an error, when sign-in fails, then I remain on `/` and an error is shown.

---

### FR-2: User Authentication — Sign Out (Must Have)

Authenticated users can sign out from the header. On sign-out, the session is cleared and the user is redirected to `/`.

**Acceptance Criteria:**

- **AC-2.1:** Given I am authenticated and on `/tasks`, when I click "Sign out" in the header, then my session is cleared and I am redirected to `/`.
- **AC-2.2:** Given I have signed out, when I navigate to `/tasks`, then I am redirected to `/`.

---

### FR-3: Route Protection (Must Have)

- Unauthenticated users navigating to `/tasks` are redirected to `/`.
- Authenticated users navigating to `/` are redirected to `/tasks`.

**Acceptance Criteria:**

- **AC-3.1:** Given I am unauthenticated, when I navigate to `/tasks`, then I am redirected to `/`.
- **AC-3.2:** Given I am authenticated, when I navigate to `/`, then I am redirected to `/tasks`.
- **AC-3.3:** Given I am unauthenticated, when I navigate to `/tasks?completed=false`, then I am redirected to `/` (filter param not preserved).

---

### FR-4: Create Task (Must Have)

A text input is always visible at the top of `/tasks`. Submitting a non-empty title creates a new task for the current user.

**Acceptance Criteria:**

- **AC-4.1:** Given I am on `/tasks`, when I type a title and press Enter, then `POST /tasks` is called and the new task appears in the list without a page reload.
- **AC-4.2:** Given I type in the input, when I press Escape, then the input is cleared.
- **AC-4.3:** Given the input is blank or whitespace-only, when I press Enter, then no task is created and no API call is made.
- **AC-4.4:** Given I create a task, when it is saved, then the input field is cleared and focused.

---

### FR-5: View Tasks (Must Have)

The task list shows all tasks belonging to the authenticated user. Each task displays its title, completion status indicator, edit button, and delete button.

**Acceptance Criteria:**

- **AC-5.1:** Given I am authenticated, when I navigate to `/tasks`, then `GET /tasks` is called and only my tasks are rendered.
- **AC-5.2:** Given I have no tasks, when I view `/tasks`, then an empty list is rendered (no error state).
- **AC-5.3:** Given another user's tasks exist in the database, when I view `/tasks`, then I do not see them.

---

### FR-6: Filter Tasks (Must Have)

Three filter links (View All / Active / Completed) control which tasks are shown. The active filter is reflected in the URL as a query parameter (`?completed=false` or `?completed=true`).

**Acceptance Criteria:**

- **AC-6.1:** Given I click "Active," when tasks reload, then `GET /tasks?completed=false` is called and only incomplete tasks are shown. The "Active" link is styled as active.
- **AC-6.2:** Given I click "Completed," when tasks reload, then `GET /tasks?completed=true` is called and only completed tasks are shown.
- **AC-6.3:** Given I click "View All," when tasks reload, then `GET /tasks` is called (no filter) and all tasks are shown.
- **AC-6.4:** Given I am on `/tasks?completed=false` and I reload the page, then the Active filter is still applied.

---

### FR-7: Toggle Task Completion (Must Have)

Clicking the checkmark/done icon on a task toggles its `completed` state. Visual feedback (strikethrough on title) reflects the new state immediately.

**Acceptance Criteria:**

- **AC-7.1:** Given an incomplete task, when I click the checkmark icon, then `PATCH /tasks/{id}` is called with `{completed: true}` and the task title gains a strikethrough style.
- **AC-7.2:** Given a completed task, when I click the checkmark icon, then `PATCH /tasks/{id}` is called with `{completed: false}` and the strikethrough is removed.
- **AC-7.3:** Given I am on the "Active" filter and I mark a task complete, then the task disappears from the list after the update.

---

### FR-8: Edit Task Title Inline (Must Have)

Clicking the edit icon switches the task into edit mode with an autofocused input. Pressing Enter or blurring saves a valid change. Pressing Escape cancels.

**Acceptance Criteria:**

- **AC-8.1:** Given I click the edit icon, when edit mode activates, then the task title input is rendered and autofocused.
- **AC-8.2:** Given I am in edit mode with a non-empty, changed title, when I press Enter or blur the input, then `PATCH /tasks/{id}` is called with `{title}` and the updated title is displayed.
- **AC-8.3:** Given I am in edit mode, when I press Escape, then edit mode exits and the original title is preserved. No API call is made.
- **AC-8.4:** Given I clear the title input, when I press Enter or blur, then no save occurs and the original title is preserved.
- **AC-8.5:** Given the title is unchanged, when I blur the input, then no API call is made.

---

### FR-9: Delete Task (Must Have)

Clicking the delete icon permanently removes the task with no confirmation dialog.

**Acceptance Criteria:**

- **AC-9.1:** Given I click the delete icon on a task, then `DELETE /tasks/{id}` is called and the task is immediately removed from the list.
- **AC-9.2:** Given the delete succeeds, when the list re-renders, then the deleted task is not present.

---

### FR-10: Per-User Data Isolation (Must Have)

Tasks are private to each user. The FastAPI backend enforces ownership on every read and write operation.

**Acceptance Criteria:**

- **AC-10.1:** Given two authenticated users with separate accounts, when each views `/tasks`, then each sees only their own tasks.
- **AC-10.2:** Given user A's task ID, when user B calls `PATCH /tasks/{id}`, then a `403 Forbidden` response is returned and no change is made.
- **AC-10.3:** Given user A's task ID, when user B calls `DELETE /tasks/{id}`, then a `403 Forbidden` response is returned and the task is not deleted.

---

### FR-11: Responsive UI (Should Have)

The UI is usable on mobile (≥320px) and desktop (≥540px). Font sizes and spacing adjust at the 540px breakpoint, matching the original app's behavior.

**Acceptance Criteria:**

- **AC-11.1:** Given I access `/tasks` on a 375px-wide viewport, when the page renders, then all task interactions (create, toggle, edit, delete) are accessible without horizontal scrolling.
- **AC-11.2:** Given I access `/tasks` on a 768px viewport, when the page renders, then the task form input is larger (matching desktop breakpoint) and spacing is proportionally wider.

---

## Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | All FastAPI task CRUD endpoints respond within 200ms under local dev load |
| Security | JWT tokens use HS256, expire after 30 days, are verified on every authenticated request |
| Security | HTTPS enforced in production (TLS termination at reverse proxy or host) |

---

## Success Metrics

1. **Functional parity:** All 7 user flows from the legacy app operate identically in the migrated app (sign-in, view, create, toggle, edit, delete, filter).
2. **API correctness:** All endpoints (`GET`, `POST`, `PATCH`, `DELETE` on `/tasks`) return correct data with proper per-user scoping.
3. **Auth coverage:** Sign-in via Google, GitHub, Twitter, Facebook, and anonymous all complete end-to-end successfully.
4. **Spec verification:** Migration passes `sds.verify` against this specification.

---

## Open Questions

*(None — all questions resolved during elicitation)*

---

## Technical Context (for Design Phase)

### Legacy Data Model
```typescript
interface ITask {
  $key?: string;      // → maps to: id (INTEGER PK)
  title: string;      // → maps to: title (VARCHAR NOT NULL)
  completed: boolean; // → maps to: completed (BOOLEAN DEFAULT false)
  createdAt: Object;  // → maps to: created_at (DATETIME)
}
```

### Legacy Auth Flow
- Firebase Auth → `uid` → task path scoped to `/tasks/{uid}`
- **Replacement:** NextAuth.js session → `accessToken` (FastAPI JWT) → `user_id` in `tasks` table

### Legacy Filter Mechanism
- Angular: `route.params.completed` → `filter$.next(value)` → `switchMap` over Firebase query
- **Replacement:** URL search param `?completed=` → `GET /tasks?completed=true/false`

### Legacy User Flows (all must be preserved)
1. Sign in → land on `/tasks`
2. View all / active / completed tasks (filter tabs)
3. Create task (Enter to submit, Escape to clear)
4. Toggle completion (checkmark icon, strikethrough animation)
5. Edit title inline (edit icon, autofocus, Enter/blur saves, Escape cancels)
6. Delete task (trash icon, no confirm)
7. Sign out → land on `/`

### Target Stack Summary
| Layer | Technology |
|---|---|
| Frontend framework | Next.js 14 (App Router), TypeScript |
| Frontend auth | NextAuth.js (OAuth + CredentialsProvider) |
| Frontend styling | Tailwind CSS |
| Frontend data | TanStack Query (React Query) |
| Backend framework | Python FastAPI |
| Backend ORM | SQLAlchemy (sync) |
| Backend DB | SQLite |
| Backend auth | JWT (python-jose, HS256, 30-day expiry) |
| Repo structure | Monorepo: `todo-app-migrated/frontend/` + `todo-app-migrated/backend/` |

### Target API Surface
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/oauth` | None | Upsert user from OAuth profile, return JWT |
| POST | `/auth/anonymous` | None | Create guest user, return JWT |
| GET | `/tasks` | Required | List user's tasks (optional `?completed=`) |
| POST | `/tasks` | Required | Create task |
| PATCH | `/tasks/{id}` | Required | Update title and/or completed |
| DELETE | `/tasks/{id}` | Required | Delete task (ownership check) |

### Target DB Schema
```sql
CREATE TABLE users (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  provider    VARCHAR NOT NULL,
  provider_id VARCHAR NOT NULL,
  email       VARCHAR,
  name        VARCHAR,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(provider, provider_id)
);

CREATE TABLE tasks (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title      VARCHAR NOT NULL,
  completed  BOOLEAN DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_tasks_user_completed ON tasks(user_id, completed);
```
