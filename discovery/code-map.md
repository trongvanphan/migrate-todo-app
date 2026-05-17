# Discovery: Code Map
> Phase 0 — todo-angular-firebase-demo

---

## 1. LOC by Module/Package

All counts are non-spec TypeScript lines. HTML/SCSS are noted separately.

### TypeScript (src/)

| File / Group | LOC |
|---|---|
| `src/polyfills.ts` | 72 |
| `src/test.ts` | 32 |
| `src/main.ts` | 21 |
| **TasksModule total** | **~180** |
| `tasks/tasks.service.ts` | 68 |
| `tasks/components/tasks/tasks.component.ts` | 41 |
| `tasks/components/task-item/task-item.component.ts` | 44 |
| `tasks/components/task-form/task-form.component.ts` | 40 |
| `tasks/components/task-list/task-list.component.ts` | 33 |
| `tasks/tasks.module.ts` | 38 |
| `tasks/tasks.routes.ts` | 17 |
| `tasks/models/task.ts` | 20 |
| `tasks/directives/auto-focus.directive.ts` | 13 |
| `tasks/models/index.ts` + barrel files | ~6 |
| **AuthModule total** | **~145** |
| `auth/components/sign-in/sign-in.component.ts` | 53 |
| `auth/auth.service.ts` | 48 |
| `auth/guards/require-auth.guard.ts` | 23 |
| `auth/guards/require-unauth.guard.ts` | 24 |
| `auth/auth.module.ts` | 29 |
| `auth/auth.routes.ts` | 17 |
| `auth/index.ts` + barrel files | ~3 |
| **FirebaseModule total** | **~20** |
| `firebase/firebase.module.ts` | 15 |
| `firebase/index.ts` | 4 |
| **AppModule / root** | **~47** |
| `app/app.module.ts` | 32 |
| `app/app.component.ts` | 20 |
| `app/app-header.component.ts` | 27 |
| **Environments** | **13** |
| `environments/environment.ts` | 7 |
| `environments/environment.prod.ts` | 7 |
| `environments/firebase.ts` | 6 |
| **TOTAL (non-test TS)** | **~530** |

### HTML Templates

| File | LOC |
|---|---|
| `task-item.component.html` | 64 |
| `src/index.html` | 24 |

### SCSS Styles

| File | LOC |
|---|---|
| `task-item.component.scss` | 143 |
| `app-header.component.scss` | 73 |
| `task-form.component.scss` | 52 |
| `task-list.component.scss` | 46 |
| `sign-in.component.scss` | 38 |
| `styles/styles.scss` + partials | ~31 |
| `app.component.scss` | 3 |
| **TOTAL SCSS** | **~386** |

---

## 2. NPM Dependencies (categorized)

### UI / Framework

| Package | Version | Purpose |
|---|---|---|
| `@angular/core` | ^4.2.6 | Framework core |
| `@angular/common` | ^4.2.6 | CommonModule, NgIf, NgFor, async pipe |
| `@angular/forms` | ^4.2.6 | FormsModule, ngModel |
| `@angular/router` | ^4.2.6 | Client-side routing |
| `@angular/animations` | ^4.2.6 | Animation support (declared, not actively used) |
| `@angular/http` | ^4.2.6 | HTTP (declared but not used — only Firebase) |
| `@angular/platform-browser` | ^4.2.6 | BrowserModule |
| `@angular/platform-browser-dynamic` | ^4.2.6 | Bootstrap |

### State / Reactivity

| Package | Version | Purpose |
|---|---|---|
| `rxjs` | ^5.4.2 | Observable streams; RxJS 5 operator patching pattern |
| `zone.js` | ^0.8.12 | Angular change detection |

### Backend / Cloud

| Package | Version | Purpose |
|---|---|---|
| `firebase` | ^4.1.3 | Firebase client SDK (Auth providers, ServerValue.TIMESTAMP) |
| `angularfire2` | ^4.0.0-rc.1 | Angular bindings for Firebase (AngularFireAuth, AngularFireDatabase) |

### Testing

| Package | Version | Purpose |
|---|---|---|
| `jasmine-core` | ^2.6.4 | Test framework |
| `karma` | ^1.7.0 | Test runner |
| `karma-chrome-launcher` | ^2.2.0 | Chrome headless runner |
| `karma-jasmine` | ^1.1.0 | Karma + Jasmine bridge |
| `karma-coverage-istanbul-reporter` | ^1.3.0 | Coverage |
| `protractor` | ^5.1.2 | E2E (Selenium/WebDriver) |
| `@types/jasmine` | ^2.5.53 | Jasmine TypeScript typings |

### Build / Dev Tools

| Package | Version | Purpose |
|---|---|---|
| `@angular/cli` | 1.2.0 | Build, serve, test orchestration |
| `typescript` | ^2.4.1 | TypeScript compiler |
| `tslint` | ^5.5.0 | Linting |
| `sw-precache` | ^5.2.0 | Service worker generation post-build |
| `firebase-tools` | ^3.9.1 | Firebase CLI for deployment |
| `minx` | r-park/minx.git | Custom CSS micro-grid (private GitHub package) |
| `ts-node` | ^3.2.0 | TypeScript execution for configs |
| `codelyzer` | ^3.1.2 | Angular TSLint rules |

---

## 3. External System Integrations

| System | Module/Package | Usage |
|---|---|---|
| **Firebase Auth** | `angularfire2/auth`, `firebase/app` | Anonymous, Google, GitHub, Twitter, Facebook sign-in via popup |
| **Firebase Realtime Database** | `angularfire2/database` | Task CRUD for each user at `/tasks/{uid}` |
| **Firebase Hosting** | `firebase.json`, `firebase-tools` | Static hosting deployment |
| **Service Worker** | `sw-precache` | Offline asset caching post-build |
| **CircleCI** | `circle.yml` | Continuous integration pipeline |
| **Material Icons** | CDN (referenced in templates) | UI icons (done, edit, delete) |

---

## 4. High-Churn Files (git log)

Based on `git log --format=format: --name-only | sort | uniq -c | sort -rn`:

| Commits | File |
|---|---|
| 3 | `package.json` |
| 3 | `package-lock.json` |
| 2 | `src/app/app-header.component.ts` |
| 2 | `README.md` |
| 2 | `.angular-cli.json` |
| 1 | `sw-precache.config.js` |
| 1 | `src/main.ts` |
| 1 | `src/index.html` |
| 1 | `karma.conf.js` |
| 1 | `firebase.json` |
| 1 | `e2e/app.po.ts` |
| 1 | `CLAUDE.md` |

Note: Low overall churn (50 commits total, most are `chore`/`deps` bumps). The app is stable. `app-header.component.ts` had the most feature-level churn (repo URL fix), which is trivial.

---

## 5. Environment Variables / Config Keys

All config lives in `src/environments/firebase.ts` — no `.env` files or `process.env` references found.

| Key | Value (placeholder) | Used In |
|---|---|---|
| `apiKey` | `AIzaSy...` | `firebase.ts` → `environment.ts` → `FirebaseModule` |
| `authDomain` | `ng2-todo-app.firebaseapp.com` | Same |
| `databaseURL` | `https://ng2-todo-app.firebaseio.com` | Same |
| `storageBucket` | `ng2-todo-app.appspot.com` | Same |

No `messageId` (FCM) or `projectId` key present — this is a minimal Realtime Database config from Firebase SDK v4.

---

## 6. Module Import Dependency Diagram

```
AppModule (app.module.ts)
├── BrowserModule           (Angular platform)
├── RouterModule.forRoot    (routing shell)
├── FirebaseModule          (app/firebase/)
│   ├── AngularFireModule.initializeApp(environment.firebase)
│   ├── AngularFireAuthModule
│   └── AngularFireDatabaseModule
├── AuthModule              (app/auth/)
│   ├── CommonModule
│   ├── AuthRoutesModule    → SignInComponent @ path ''
│   │   └── [guard] RequireUnauthGuard
│   ├── AuthService         (wraps AngularFireAuth)
│   ├── RequireAuthGuard
│   └── RequireUnauthGuard
└── TasksModule             (app/tasks/)
    ├── CommonModule
    ├── FormsModule
    ├── TasksRoutesModule   → TasksComponent @ path 'tasks'
    │   └── [guard] RequireAuthGuard
    ├── TasksService        (wraps AngularFireDatabase)
    ├── TaskFormComponent
    ├── TaskListComponent
    ├── TaskItemComponent
    ├── TasksComponent      (container, reads route params)
    └── AutoFocusDirective

AppComponent (root)
├── uses AuthService (authenticated$, signOut)
└── renders AppHeaderComponent + <router-outlet>

AppHeaderComponent
├── @Input() authenticated: boolean
└── @Output() signOut: EventEmitter

TasksComponent
├── ActivatedRoute (reads :completed param)
└── TasksService (filterTasks, createTask, removeTask, updateTask)

TaskListComponent
├── @Input() filter: string
├── @Input() tasks: FirebaseListObservable<ITask[]>
├── @Output() remove
└── @Output() update

TaskItemComponent
├── @Input() task: ITask
├── @Output() remove
└── @Output() update
    (inline edit form with AutoFocusDirective)

TaskFormComponent
└── @Output() createTask (emits trimmed title string)
```

---

## 7. Feature Coverage Estimate

### Distinct Features

1. **Multi-provider authentication** — Anonymous, Google, GitHub, Twitter, Facebook (5 providers)
2. **Auth-gated routing** — RequireAuth + RequireUnauth guards
3. **Task creation** — form with trimming and enter-to-submit
4. **Task completion toggle** — checkbox-style button per task
5. **Task inline edit** — click edit icon → inline input → save on submit or blur
6. **Task title validation** — empty title blocked; unchanged title skips DB write
7. **Task deletion** — per-task delete button
8. **Task filtering** — All / Active (completed=false) / Completed (completed=true) via URL param + Firebase server-side query
9. **Per-user data isolation** — tasks stored under `/tasks/{uid}`, Firebase rules enforce ownership
10. **Offline / Service Worker** — `sw-precache` generates offline cache for static assets
11. **Sign-out** — available in app header when authenticated
12. **Auto-redirect** — authenticated user sent to `/tasks`; unauthenticated user sent to `/`
13. **Server timestamp on create** — `createdAt` = `firebase.database.ServerValue.TIMESTAMP`
14. **AutoFocus directive** — focuses edit input when entering edit mode

### Top Modules by LOC

| Module | TS LOC | Notes |
|---|---|---|
| TasksModule | ~180 | Core business logic |
| AuthModule | ~145 | All auth providers + guards |
| FirebaseModule | ~20 | Thin bootstrap wrapper |
| App shell | ~47 | Root component + header |

### Recommended Migration Order

1. **FirebaseModule equivalent** — Initialize new backend (e.g., Firebase v9 modular SDK or Supabase). Unblocks everything else.
2. **AuthModule** — Migrate auth providers; implement route guards equivalent.
3. **Task data model** — Define the Task type/schema in the new framework.
4. **TasksService** — Migrate CRUD and filtering logic; most complex business logic lives here.
5. **UI components** — TaskFormComponent → TaskListComponent → TaskItemComponent (in dependency order).
6. **TasksComponent** (container) — Wire new service to new UI.
7. **AppHeaderComponent + AppComponent** — Shell; trivial.
8. **Service Worker** — Last; handled by build tooling in modern stacks (Vite PWA plugin, etc.).

### Surprises / Red Flags

- **`minx` CSS grid is a private GitHub package** (`r-park/minx.git`). It is not on npm. Any migration must either reproduce the grid classes or replace with Tailwind/Bootstrap/CSS Grid. This is a hidden build dependency that will break `npm install` in a clean environment without GitHub access to that repo.
- **RxJS 5 operator patching** — The code uses `import 'rxjs/add/operator/...'` (side-effect imports). Migrating to RxJS 6+ requires switching to pipeable operators (`pipe(switchMap(...))` etc.).
- **`angularfire2` v4 RC** — This is a release candidate from ~2017. The API (`FirebaseListObservable`, `.push()`, `.remove()`, `.update()` on list) is entirely different from modern AngularFire (v7+) or the Firebase v9 modular SDK.
- **`@angular/http` is in dependencies but never used** — Firebase handles all network calls directly.
- **Filter is passed as string `'true'`/`'false'` from URL params** — The service does an explicit `switch` on these string values before passing booleans to Firebase. The new implementation must preserve this `completed: boolean` semantics.
- **`auth.uid$` is consumed with `.take(1)` in `TasksService` constructor** — meaning the UID is read only once at service instantiation. If auth state changes, the service is not re-initialized. This is a design constraint to carry forward or explicitly fix.
- **No loading/error states** — The app has zero error handling UI and no loading spinners. Firebase observables emit immediately (empty array), so this was acceptable. A new async stack may need explicit loading state.
