# Tasks — tasks domain

## Bundle C: backend-tasks
- C1. Add `sqlalchemy` dependency; create `app/db.py` (SQLite engine, session factory, `get_db` dep).
- C2. Implement `app/domains/tasks/models.py` (Task ORM).
- C3. Implement `app/domains/tasks/schemas.py` (Pydantic).
- C4. Implement `app/domains/tasks/repo.py` (CRUD + filter).
- C5. Implement `app/domains/tasks/router.py` (4 endpoints) and wire under `/api` in `app/main.py`.
- C6. Add `pytest` + `httpx` test for happy paths and 401/404 cases.

## Bundle D: frontend-tasks
- D1. Add typed `lib/api.ts` task helpers.
- D2. Build `components/tasks/{TasksView,TaskForm,TaskList,TaskItem,TaskFooter}.tsx`.
- D3. Wire `app/(protected)/tasks/page.tsx` with filter via search param.
- D4. Style minimally to match legacy (inputs, hover, strikethrough on completed).
- D5. Manual smoke: create/toggle/delete/filter in browser.
