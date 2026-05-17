# Discovery Summary — todo-angular-firebase-demo

**Scanned at**: 2026-05-17
**Total LOC**: ~1267 (TS/HTML/SCSS under `src/`)
**Primary language**: TypeScript (Angular 4)
**Modules**: 1 top-level (`src/app/`) with 3 feature sub-modules

## Feature Modules

| Module | Path | Role | LOC est. |
|--------|------|------|----------|
| auth | `src/app/auth/` | AngularFireAuth wrapper, sign-in component, route guards | ~250 |
| tasks | `src/app/tasks/` | CRUD over `/tasks/{uid}` in Firebase RTDB, filter (all/active/completed) | ~600 |
| firebase | `src/app/firebase/` | AngularFire2 module bootstrap + env config | ~50 |
| shell | `src/app/` (root) | AppModule, AppComponent, header | ~100 |

## Entry Points
- `src/main.ts` — bootstrap
- `src/app/app.module.ts` — root NgModule
- `src/app/app.component.ts` — root component, hosts `<router-outlet>`

## API / Data Surface
- **No backend HTTP API** — direct Firebase Realtime Database access from client via AngularFireDatabase
- **Data path**: `/tasks/{uid}/{taskKey}` with shape `{ completed: bool, createdAt: timestamp, title: string }`
- **Auth providers**: anonymous, Google, GitHub, Twitter, Facebook (Firebase popup)
- **Security**: `firebase.rules.json` restricts read/write to owning UID; `.indexOn: ["completed"]` for filter

## External Dependencies (top)
- `@angular/*` 4.2.6 (core, common, forms, router, http, animations)
- `angularfire2` 4.0.0-rc.1
- `firebase` 4.1.3
- `rxjs` 5.4.2
- `zone.js`, `core-js`

## Tests
- Unit: Karma + Jasmine (`*.spec.ts`) — minimal coverage (e.g., `task.spec.ts`)
- E2E: Protractor (`e2e/`)

## UI Screens
1. Sign-in (`/sign-in`) — provider buttons
2. Tasks list (`/tasks`, `/tasks/active`, `/tasks/completed`) — list + form + filter footer

## Risks / Notes for Migration
- **No existing REST API** — the new FastAPI backend defines a brand-new contract; no legacy API to mirror.
- **Realtime subscriptions** — Angular code relies on observable streams from RTDB. Next.js client must either keep Firebase JS SDK for realtime, or migrate to polling/WebSocket via FastAPI.
- **Auth state** — currently entirely client-side (Firebase JS). FastAPI must verify Firebase ID tokens via `firebase-admin` if backend owns the data path.
- **Decision required**: does the new stack continue using Firebase as the data store (FastAPI proxies/validates) or migrate data to Postgres? Greenfield scope assumes the simplest path — keep Firebase Auth, but move task storage to FastAPI + SQLite/Postgres (recorded in design).
