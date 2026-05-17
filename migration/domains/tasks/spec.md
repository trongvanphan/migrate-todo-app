# Spec — tasks domain

## Goal
Replace direct AngularFire RTDB access with a FastAPI REST API for tasks, owned per-user, with a Next.js UI matching legacy behavior (list, add, toggle complete, delete, filter all/active/completed).

## Functional Requirements
- FR1: `GET /api/tasks?filter=all|active|completed` — returns the authenticated user's tasks. `all` (default) returns everything; `active` returns `completed=false`; `completed` returns `completed=true`. Ordered by `created_at` ascending.
- FR2: `POST /api/tasks` body `{ title: string }` → 201 with the created task. `title` required, 1–500 chars.
- FR3: `PATCH /api/tasks/{id}` body `{ title?: string, completed?: boolean }` → 200 with updated task. 404 if not owned by user.
- FR4: `DELETE /api/tasks/{id}` → 204. 404 if not owned by user.
- FR5: All endpoints require auth (401 if missing/invalid token).
- FR6: Frontend `/tasks`, `/tasks/active`, `/tasks/completed` show filtered lists; identical UX to legacy (input at top, list with toggle + delete, footer with counts and filter links).

## Data Model
`Task { id: string (uuid), uid: string, title: string, completed: bool, created_at: datetime }`

## Storage
SQLite via SQLAlchemy for v1 (single-file, zero-ops). Schema migratable to Postgres later. **Not** Firebase RTDB — the goal is to eliminate that dependency for data.

## Non-Functional
- p95 latency <100ms for list endpoint with <10K tasks.
- No realtime push in v1; client refetches on mutation.

## Acceptance
- Create 3 tasks, toggle one, filter active → 2 returned; filter completed → 1.
- Delete a task → list endpoint omits it.
- A second user signed in cannot read user A's tasks (403/404 — endpoint scoped by uid).
