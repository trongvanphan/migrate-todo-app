# Discovery — todo-angular-firebase-demo

Single Angular 4 SPA, ~1,267 LOC across .ts/.html/.scss. No backend — Firebase Realtime Database accessed directly from the browser.

## Modules

| Module | Path | Purpose |
|---|---|---|
| `FirebaseModule` | `src/app/firebase/` | Initializes AngularFireModule with creds from `environments/firebase.ts`. |
| `AuthModule` | `src/app/auth/` | `AuthService` wraps `AngularFireAuth`. Anonymous + Google/GitHub/Twitter/Facebook popup sign-in. `RequireAuthGuard`, `RequireUnauthGuard`. |
| `TasksModule` | `src/app/tasks/` | `TasksService` reads/writes `/tasks/{uid}` in Firebase RTDB. Filter via `ReplaySubject` + `switchMap`. CRUD: create, remove, update. |

## Data model

`/tasks/{uid}/{taskKey}`: `{ title: string, completed: boolean }`. Filter uses `orderByChild('completed')` with security rule `.indexOn: ["completed"]`.

## Routes

- `/` → `SignInComponent` (requires unauth)
- `/tasks` → `TasksComponent` (requires auth)

## API surface (to replicate in FastAPI)

| Operation | Source (Firebase) | Target (REST) |
|---|---|---|
| Sign up / sign in | `signInWithPopup`, `signInAnonymously` | `POST /auth/register`, `POST /auth/login` (JWT) |
| List tasks | `afDb.list('/tasks/{uid}')` | `GET /tasks?filter=all\|active\|completed` |
| Create task | `tasks$.push(new Task(title))` | `POST /tasks` |
| Update task | `tasks$.update(key, changes)` | `PATCH /tasks/{id}` |
| Delete task | `tasks$.remove(key)` | `DELETE /tasks/{id}` |

## Tests

- Karma unit-test scaffold present (`npm test`), Protractor e2e (`npm run e2e`). No meaningful test coverage in source.

## Decision

Single domain `todo` with two features (`auth`, `tasks`). No split needed. Full v2 pipeline (strangler-fig, canary, api-diff, decommission) **does not apply** — no production traffic, this is a clean rewrite.
