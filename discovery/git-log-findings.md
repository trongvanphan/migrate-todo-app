# Discovery: Git Log Findings
> Phase 0 — todo-angular-firebase-demo

---

## Git Log (all branches, last 50 commits)

```
2c3f70e create the claude.md
07f6fd4 docs: add Scrum agile estimation guide (FHM-6)
697e757 fix(AppHeaderComponent): repo url is incorrect
7e1fc78 feat(service-worker): add sw-precache for offline
382c71d chore(package): rename project
3e55b27 chore(*): switch to angular-cli
108c48e chore(docs): update readme
ff9eda1 chore(deps): update versions
a0b777c chore(deps): update to angularfire2 4.x
109d986 chore(deps): replace `ts-loader` with `awesome-typescript-loader`
81c6f09 chore(deps): update webpack
cd3b9a8 fix(build): tsconfig should be configured for es6
9c06eec chore(deps): update typescript version
247dadc chore(test): remove coverage reporting
e1c566c chore(build): use webpack to copy assets to target folder
982f088 chore(package): add contributor
1818185 Adding Facebook Auth
2fe62d0 chore: update dependencies
31a60ca chore(package): update contributors
ac7844f chore(docs): update express server port
302c254 chore(favicon): added basic favicon and postbuild script to copy to t...
a675c13 chore(readme): update cited angular versions
b692882 remove trainling space (webstorm was hiding it)
231d076 trying to fix the trailing space issue.
ce9e92b chore(package): updated dependencies
ef0b0c0 chore(package): lock node version to 6.8, update devDependencies
c57b67a chore(package): update dependencies/devDependencies.
13d93f4 Adjusted README to state 2.1.0
29a6c62 Upgraded to Angular 2.1.0
0ae1d4e Added support for Anonymous signIn
0ae832d chore(build): update tsconfig
f22dcf0 chore(build): update webpack config
e51bcf2 chore(server): set host to `0.0.0.0`
d4c5d25 chore(docs): update readme
3ee7758 chore(lock-node): locks node to 6.5 in package.json, circle.yml
3dd9e2d chore(pr-review): removes keep_fname in webpack.config uglify; removes
53b8dbc fix(issues/96): fixes angular >=rc7 dependency warning in webpack build
e5937d5 fix(auth): change absolute path for auth component import to relative
3670f1b fix(webpack): upgrade webpack to webpack2-beta22, remove angularfire2
e825707 chore(package): angular v2.0.0, fix spec; update devDependencies
d0bd4c8 fix(ci): don't run coveralls for forked pull requests
7935b74 chore(update): devDependencies css-loader, node-sass, postcss-loader.
ac6632f chore(test): integrate with coveralls service
0ad1da1 feat(tasks): `mark all as...` example
d1e0db3 chore(test): add coverage reporting
4ae2108 chore(webpack): clean up config
4a4e224 chore(package): update scripts
5fc85bb chore(deps): update versions
6154831 chore(package): list contributors
471165b Updated dependencies.
```

---

## Findings by Domain

### Auth Domain

| Commit | Finding |
|---|---|
| `0ae1d4e` Added support for Anonymous signIn | Anonymous auth was **added after** the initial implementation, not designed in from the start. It's a feature addition, not a foundational concern. The migration should treat it as one of five equal providers. |
| `1818185` Adding Facebook Auth | Facebook auth was also **added later** (same pattern as anonymous). Five providers were not all in the initial design. |
| `e5937d5` fix(auth): change absolute path for auth component import to relative | Indicates the auth module had an import path issue during an early refactor. No functional impact for migration. |

### Tasks Domain

| Commit | Finding |
|---|---|
| `0ad1da1` feat(tasks): `mark all as...` example | A "mark all as" feature was **experimentally added** at some point. However, this commit is in older history and the feature is **not present in the current codebase** — it was not carried forward to the Angular CLI refactor. This means: (a) the feature was dropped, or (b) it exists in a branch that was never merged. The current code has no bulk-action functionality. |
| `a0b777c` chore(deps): update to angularfire2 4.x | The app was migrated from AngularFire2 v2/v3 to v4-RC. The API changed significantly at that point (from `FirebaseObjectObservable`/`FirebaseListObservable` to the current API). This is why the service uses `afDb.list()` with the v4 query config object. |

### Build / Infrastructure Domain

| Commit | Finding |
|---|---|
| `3e55b27` chore(*): switch to angular-cli | The entire build system was migrated from a custom Webpack config to Angular CLI. This explains why `karma.entry.js`, `server/main.js` appear in churn but don't exist in the current codebase. |
| `7e1fc78` feat(service-worker): add sw-precache for offline | Service worker (offline support) was a deliberate feature addition. The `postbuild` script in `package.json` reflects this. The migration target should carry forward offline capability. |
| `cd3b9a8` fix(build): tsconfig should be configured for es6 | Early build required explicit ES6 target fix. Not relevant to migration, but confirms the codebase was initially in ES5 territory. |

### Documentation / Meta

| Commit | Finding |
|---|---|
| `b692882` / `231d076` remove trailing space (webstorm was hiding it) | Two commits to fix a single trailing space indicates this was a linting or formatting issue that broke the build or tests. Shows attention to code style. |
| `07f6fd4` docs: add Scrum agile estimation guide (FHM-6) | This commit is in the `todo-angular-firebase-demo` git history but appears to be a documentation artifact from the parent migration repo, not from the original open-source project. It references an internal ticket (`FHM-6`). Not relevant to the app's functionality. |

---

## Inline Code Comments Revealing Requirements

The source code is largely comment-free. No business-logic comments were found in TypeScript files beyond section labels (`// components`, `// services`, etc. in module files).

Meaningful code patterns that reveal implicit requirements:

### `tasks.service.ts` — filter logic
```typescript
case 'false':
  this.filter$.next(false);
  break;
case 'true':
  this.filter$.next(true);
  break;
default:
  this.filter$.next(null);
  break;
```
The `default` branch (null → show all) means any route param value other than `'true'`/`'false'` is treated as "show all". This is intentional defensive behavior — the "All" tab navigates to `/tasks` with no param, so `undefined` hits the default.

### `task-item.component.ts` — title save guard
```typescript
if (title.length && title !== this.task.title) {
  this.update.emit({title});
}
```
An update is only emitted if (1) the new title is non-empty AND (2) the title actually changed. **Saving the same title is a no-op at the DB level.** This is a deliberate optimization that must be preserved.

### `auth.service.ts` — silent error swallowing
```typescript
.catch(error => console.log('ERROR @ AuthService#signIn() :', error));
```
All auth errors are swallowed — the `Promise` resolves to `undefined` on error, and `postSignIn()` in `SignInComponent` is still called (`.then(() => this.postSignIn())`). However, since `signInAnonymously` / `signInWithPopup` reject on failure, and the `.catch()` returns `undefined`, the `.then()` would fire on the resolved (error-caught) promise. This is a **latent bug**: if a sign-in fails, the user may be incorrectly navigated to `/tasks` before auth succeeds.

---

## Summary: Hidden Requirements from Git History

1. **Anonymous sign-in must be supported** — it was explicitly added as a feature (`0ae1d4e`).
2. **Facebook is a required auth provider** — added explicitly (`1818185`).
3. **Offline support (service worker) is a product requirement**, not just a nice-to-have — added as a named feature (`7e1fc78`).
4. **A "mark all as..." bulk action was prototyped but dropped** — not required in the migration unless intentionally re-added.
5. **Auth error handling is currently broken/silent** — the migration is an opportunity to fix this properly with user-facing error messages.
