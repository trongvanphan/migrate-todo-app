# Design — tasks domain

## Backend (FastAPI)
- `app/domains/tasks/models.py` — SQLAlchemy `Task` ORM model.
- `app/domains/tasks/schemas.py` — Pydantic `TaskCreate`, `TaskUpdate`, `TaskOut`.
- `app/domains/tasks/repo.py` — query functions scoped to `uid`: `list_for_user(uid, filter)`, `create(uid, title)`, `update(uid, id, patch)`, `delete(uid, id)`.
- `app/domains/tasks/router.py` — FastAPI `APIRouter` with the four endpoints; all depend on `get_current_user`.
- `app/db.py` — SQLAlchemy session/engine factory; `Base.metadata.create_all()` on startup (good enough for v1; switch to Alembic later).
- `app/main.py` — wire CORS, include `tasks.router` under `/api`, include `me.router`.

## Frontend (Next.js)
- `lib/api.ts` — typed helpers: `listTasks(filter)`, `createTask(title)`, `updateTask(id, patch)`, `deleteTask(id)`.
- `app/(protected)/tasks/page.tsx` — server-redirects-to-client component that reads filter from search params and renders `TasksView`.
- `components/tasks/TasksView.tsx` — fetches via `useEffect` + manages local state; `useTransition` for optimistic-ish updates.
- `components/tasks/TaskForm.tsx`, `TaskList.tsx`, `TaskItem.tsx`, `TaskFooter.tsx` — mirror legacy components.
- Filter routes: use a single page with `?filter=` query param; nav links update the param (matches legacy `/tasks/active`-style URLs less literally but keeps shareability).

## Cross-cutting
- Errors: backend returns `{ detail: string }` on non-2xx; frontend `apiFetch` throws `ApiError`; `TasksView` surfaces via a toast/inline banner.
- IDs: server-generated UUIDv4 strings.

## Why SQLite + SQLAlchemy
Greenfield + single user dev. Migrating away from Firebase RTDB removes a vendor lock-in. Postgres swap is one URL change.
