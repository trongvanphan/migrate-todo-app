# Discovery: Tests as Specifications
> Phase 0 — todo-angular-firebase-demo

---

## Test Files Found

| File | Type | Framework |
|---|---|---|
| `src/app/tasks/models/task.spec.ts` | Unit test | Jasmine / Karma |
| `e2e/app.e2e-spec.ts` | End-to-end test | Protractor / Jasmine |

No additional spec files were found. The test suite is minimal — only the `Task` model and a single E2E smoke test are covered.

---

## Unit Tests: `task.spec.ts`

### Raw describe/it blocks

```
describe('Tasks')
  describe('Task')
    it('should set title')
    it('should set completed to false by default')
```

### Converted to Given/When/Then Requirements

#### REQ-T001: Task title is set from constructor argument

- **Domain:** Tasks
- **Given:** A new Task is created with the title `"test"`
- **When:** The title property is accessed
- **Then:** It equals `"test"`

> Implies: The `title` constructor argument is stored verbatim on the model. No trimming or validation at the model level (trimming happens in `TaskFormComponent` and `TaskItemComponent` before calling the service).

#### REQ-T002: Task completed defaults to false

- **Domain:** Tasks
- **Given:** A new Task is created with any title
- **When:** The `completed` property is accessed
- **Then:** It equals `false`

> Implies: Every new task starts in the "active" (not completed) state. This is a business rule, not just a code default.

---

## E2E Tests: `app.e2e-spec.ts`

### Raw describe/it blocks

```
describe('App')
  it('should display welcome message')
```

### Converted to Given/When/Then Requirements

#### REQ-E001: Application renders with expected heading

- **Domain:** App shell / Navigation
- **Given:** The user navigates to the application root URL
- **When:** The page loads
- **Then:** The heading text `"Todo Angular Firebase"` is visible

> Note: This E2E test is a smoke test only. It verifies the app renders but does not test any auth or task flows. In the migration, this should be expanded to verify the sign-in page renders for unauthenticated users.

---

## Coverage Gaps (No Tests Found For)

The following features have **zero test coverage** in the existing suite:

| Feature | Where Implemented | Risk |
|---|---|---|
| Auth sign-in (all 5 providers) | `auth.service.ts`, `sign-in.component.ts` | High — core entry point |
| RequireAuthGuard redirect behavior | `require-auth.guard.ts` | Medium |
| RequireUnauthGuard redirect behavior | `require-unauth.guard.ts` | Medium |
| Task creation (form submit + trim) | `task-form.component.ts` | Medium |
| Task title save-on-blur / escape-cancels | `task-item.component.ts` | Medium — has edge cases |
| Task title unchanged → no DB write | `task-item.component.ts` | High — non-obvious business rule |
| Task empty title → blocked | `task-form.component.ts`, `task-item.component.ts` | Medium |
| Task toggle completed | `task-item.component.ts` | High |
| Task deletion | `task-item.component.ts` | Medium |
| Filter navigation (All/Active/Completed) | `task-list.component.ts`, `tasks.component.ts` | High |
| Firebase database CRUD | `tasks.service.ts` | High |
| Per-user data isolation | Firebase rules + `tasks.service.ts` | High |
| Sign-out from header | `app-header.component.ts`, `app.component.ts` | Low |
| AutoFocus on edit mode | `auto-focus.directive.ts` | Low |
| Escape key clears create-task input | `task-form.component.ts` | Low |

---

## Non-Obvious Business Rules Revealed by Tests

1. **Model-level `completed` default is `false`** (REQ-T002) — This must be enforced at the data layer in the migration, not just the UI.
2. **Title is stored as passed to constructor** — Trimming is a UI responsibility (both `TaskFormComponent.submit()` and `TaskItemComponent.saveTitle()` call `.trim()` before emitting). The model itself does no sanitization.
3. **Implied: `createdAt` uses server timestamp** — The `Task` constructor sets `createdAt = firebase.database.ServerValue.TIMESTAMP`. This sentinel is replaced server-side. The migration must use the equivalent server-side timestamp mechanism to avoid client clock skew.
