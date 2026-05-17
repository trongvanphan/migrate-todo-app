# Bundle B-2: Backend Task Endpoints

> Stage: depth | Parallel: no (depends on B-1) | Files: backend/app/routers/tasks.py, backend/app/main.py, backend/tests/conftest.py, backend/tests/test_auth.py, backend/tests/test_tasks.py

**Bundle Verify**: All task CRUD endpoints enforce per-user isolation and the completion filter returns correct subsets.
- **Level**: integration
- **Given**: Two users with JWTs (via /auth/anonymous x2); user A has 3 tasks (2 incomplete, 1 complete)
- **Action**: User B calls GET /tasks — sees 0 tasks; user A calls GET /tasks?completed=false — sees 2 tasks; user B calls DELETE /tasks/{user_A_task_id} — gets 403
- **Outcome**: All three assertions pass with correct HTTP status codes

---

## Context

**Architecture Decisions:** AD-4 (sync SQLAlchemy), AD-5 (HTTPBearer), AD-7 (refetch-after-mutate — no server behavior change)

**Findings:** F-9 (sync get_db), F-10 (HTTPBearer), F-11 (inline ownership check), F-12 (Pydantic v2)

**Standards:** S-5, S-6, S-10

**Relevant ACs:** AC-4.1, AC-4.3, AC-5.1, AC-5.2, AC-5.3, AC-6.1, AC-6.2, AC-6.3, AC-7.1, AC-7.2, AC-7.3, AC-8.1, AC-8.2, AC-9.1, AC-10.1, AC-10.2, AC-10.3

---

## STEPs

### STEP-7: Task GET + POST endpoints
**Trace:** `[FR-4 -> AC-4.1], [FR-4 -> AC-4.3], [FR-5 -> AC-5.1], [FR-5 -> AC-5.2], [FR-5 -> AC-5.3], [FR-6 -> AC-6.1], [FR-6 -> AC-6.2], [FR-6 -> AC-6.3]` | **Informed by:** AD-4, F-11 | **Effort:** M

**Files:**
- `todo-app-migrated/backend/app/routers/tasks.py` — create
- `todo-app-migrated/backend/app/main.py` — modify (mount tasks router)

**Intent:** `GET /tasks` filters by `user_id` always — scoping is at query level. Optional `?completed=` param converts string to bool. `POST /tasks` validates title via Pydantic. `created_at` is server-set.

**Implementation guidance:**
1. `GET /tasks`: `completed: str | None = Query(None)`; base query `filter(Task.user_id == current_user.id)`; add `.filter(Task.completed == (completed.lower() == "true"))` when completed is not None
2. `POST /tasks`: `Task(user_id=current_user.id, title=body.title)`; `db.add(); db.commit(); db.refresh(task)`; return `TaskOut.model_validate(task)`
3. Mount: `app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])` in main.py

**Verify:**
- Level: integration | Given: user A creates 2 tasks; user B authenticated | Action: user B calls GET /tasks | Outcome: empty list; user A calls GET /tasks?completed=false → only incomplete tasks

> **Standards:** S-5, S-6

**Dependencies:** Depends on B-1; enables STEP-8

---

### STEP-8: Task PATCH + DELETE with ownership
**Trace:** `[FR-7 -> AC-7.1], [FR-7 -> AC-7.2], [FR-7 -> AC-7.3], [FR-8 -> AC-8.1], [FR-8 -> AC-8.2], [FR-8 -> AC-8.3], [FR-8 -> AC-8.4], [FR-8 -> AC-8.5], [FR-9 -> AC-9.1], [FR-9 -> AC-9.2], [FR-10 -> AC-10.2], [FR-10 -> AC-10.3]` | **Informed by:** AD-5, F-11 | **Effort:** S

**Files:**
- `todo-app-migrated/backend/app/routers/tasks.py` — modify

**Intent:** Ownership check order: 404 first (task not found), then 403 (wrong owner) — prevents task ID enumeration. PATCH applies only non-None fields. DELETE returns 204.

**Implementation guidance:**
1. `PATCH /tasks/{task_id}`: fetch → 404; ownership → 403; apply non-None fields; commit; return TaskOut
2. `DELETE /tasks/{task_id}`: fetch → 404; ownership → 403; `db.delete(task); db.commit()`; return `Response(status_code=204)`
3. Inline check: `if task.user_id != current_user.id: raise HTTPException(403)`
4. PATCH partial: `if update.title is not None: task.title = update.title`; `if update.completed is not None: task.completed = update.completed`

**Verify:**
- Level: integration | Given: user A owns task_id=1 | Action: user B calls PATCH /tasks/1 | Outcome: 403; user A calls PATCH /tasks/1 `{completed:true}` → 200; DELETE /tasks/1 → 204

> **Standards:** S-6

**Dependencies:** Depends on STEP-7

---

### STEP-9: Backend test suite
**Trace:** `MANUAL -> Test for STEP-6, STEP-7, STEP-8` | **Effort:** M

**Files:**
- `todo-app-migrated/backend/tests/__init__.py` — create
- `todo-app-migrated/backend/tests/conftest.py` — create
- `todo-app-migrated/backend/tests/test_auth.py` — create
- `todo-app-migrated/backend/tests/test_tasks.py` — create

**Intent:** Override `get_db` dependency with in-memory SQLite. Test upsert idempotency, per-user scoping, ownership 403, completion filter.

**Implementation guidance:**
1. `conftest.py`: `app.dependency_overrides[get_db]` with in-memory session; `client = TestClient(app)` fixture
2. `test_auth.py`: upsert idempotency, anonymous user creation, invalid JWT → 401
3. `test_tasks.py`: task scoping, ownership 403, completion filter, 204 on delete
4. Run: `pytest tests/` from `backend/`

**Verify:**
- Level: unit | Given: `pytest tests/` | Action: run | Outcome: all pass; covers scoping and ownership

> **Standards:** S-6, S-10

**Dependencies:** Depends on STEP-7, STEP-8
