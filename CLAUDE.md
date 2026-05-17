# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This repo is a migration project. `todo-angular-firebase-demo/` is the **source** app (Angular 4 + AngularFire2 + Firebase) being migrated to a modern stack in `todo-app-migrated/` (currently scaffolded with only a LICENSE).

## Source App: `todo-angular-firebase-demo/`

### Commands (run from `todo-angular-firebase-demo/`)

```bash
npm install          # Install dependencies
npm start            # Dev server at localhost:4200
npm run build        # Production build to ./dist (runs sw-precache after)
npm run lint         # Lint TypeScript files
npm test             # Run unit tests via Karma
npm run e2e          # Run Protractor end-to-end tests
```

### Architecture

The app is an Angular 4 module-based SPA with three feature modules:

- **`FirebaseModule`** (`src/app/firebase/`) — Initializes AngularFire2 (`AngularFireModule`, `AngularFireAuthModule`, `AngularFireDatabaseModule`) using config from `src/environments/firebase.ts`. Firebase credentials live here; swap them in `.firebaserc` and `src/environments/firebase.ts` for a different project.

- **`AuthModule`** (`src/app/auth/`) — `AuthService` wraps `AngularFireAuth` and exposes `authenticated$` and `uid$` observables. Supports anonymous, Google, GitHub, Twitter, and Facebook sign-in via popup. Guards and routes are defined in `auth.routes.ts`.

- **`TasksModule`** (`src/app/tasks/`) — `TasksService` reads/writes tasks at the Firebase Realtime Database path `/tasks/{uid}`. Supports create, remove, update, and filter (all / active / completed) via a `ReplaySubject<filter>` + `switchMap`. Components: `TasksComponent`, `TaskListComponent`, `TaskItemComponent`, `TaskFormComponent`. The `AutoFocusDirective` handles input focus.

Data model: tasks stored per-user under `/tasks/{uid}/{taskKey}` with at minimum a `completed: boolean` field (used for server-side filtering via `orderByChild`).

### Firebase configuration

To point the app at a different Firebase project, update:
- `.firebaserc` — `projects.default` value
- `src/environments/firebase.ts` — API key, auth domain, database URL, storage bucket
- `firebase.rules.json` — security rules

### Service Worker

`npm run build` automatically runs `sw-precache` using `sw-precache.config.js` to generate a service worker for offline caching.

## Migration Target: `todo-app-migrated/`

Only a LICENSE file exists. The migration work (choosing a new stack and implementing it) is the primary task in this repo.
