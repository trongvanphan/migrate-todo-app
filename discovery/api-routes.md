# Discovery: API Routes (Firebase Operations)
> Phase 0 — todo-angular-firebase-demo

---

## Summary

This is an Angular/Firebase app — there is no traditional REST API. All backend operations go through:
- **AngularFireDatabase** (Firebase Realtime Database) for task CRUD
- **AngularFireAuth** (Firebase Authentication) for identity

---

## Auth Operations

### Service: `src/app/auth/auth.service.ts`

| Operation | Firebase Method | Path / Object | Line(s) |
|---|---|---|---|
| Observe auth state | `afAuth.authState` (Observable) | Firebase Auth state stream | 15–16 |
| Sign in with provider (popup) | `afAuth.auth.signInWithPopup(provider)` | n/a (OAuth popup) | 20 |
| Sign in anonymously | `afAuth.auth.signInAnonymously()` | n/a | 25 |
| Sign in with GitHub | `new firebase.auth.GithubAuthProvider()` | OAuth → `signInWithPopup` | 29–31 |
| Sign in with Google | `new firebase.auth.GoogleAuthProvider()` | OAuth → `signInWithPopup` | 33–35 |
| Sign in with Twitter | `new firebase.auth.TwitterAuthProvider()` | OAuth → `signInWithPopup` | 37–39 |
| Sign in with Facebook | `new firebase.auth.FacebookAuthProvider()` | OAuth → `signInWithPopup` | 41–43 |
| Sign out | `afAuth.auth.signOut()` | n/a | 46 |

### Derived Observables from `authState`

| Observable | Derivation | Consumed By |
|---|---|---|
| `authenticated$` | `authState.map(user => !!user)` | `AppComponent`, `RequireAuthGuard`, `RequireUnauthGuard` |
| `uid$` | `authState.map(user => user.uid)` | `TasksService` constructor |

### Component: `src/app/auth/components/sign-in/sign-in.component.ts`

| UI Action | Method Called | Navigates After |
|---|---|---|
| Click "Anonymously" | `auth.signInAnonymously()` | `/tasks` |
| Click "GitHub" | `auth.signInWithGithub()` | `/tasks` |
| Click "Google" | `auth.signInWithGoogle()` | `/tasks` |
| Click "Twitter" | `auth.signInWithTwitter()` | `/tasks` |
| Click "Facebook" | `auth.signInWithFacebook()` | `/tasks` |

All sign-in methods call `postSignIn()` on resolution → `router.navigate(['/tasks'])`.

---

## Task CRUD Operations

### Service: `src/app/tasks/tasks.service.ts`

All database operations target the path `/tasks/{uid}` where `uid` is taken from `auth.uid$` on first subscription.

| Operation | AngularFire Method | Firebase Path | Method Return | Line |
|---|---|---|---|---|
| Initialize task list observable | `afDb.list(path)` | `/tasks/{uid}` | `FirebaseListObservable<ITask[]>` | 28 |
| Initialize filtered tasks observable | `afDb.list(path, { query: { orderByChild: 'completed', equalTo: filter$ } })` | `/tasks/{uid}` | `FirebaseListObservable<ITask[]>` | 30–33 |
| Create task | `this.tasks$.push(new Task(title))` | `/tasks/{uid}/<auto-key>` | `firebase.Promise<any>` | 57–59 |
| Remove task | `this.tasks$.remove(task.$key)` | `/tasks/{uid}/{taskKey}` | `firebase.Promise<any>` | 61–63 |
| Update task | `this.tasks$.update(task.$key, changes)` | `/tasks/{uid}/{taskKey}` | `firebase.Promise<any>` | 65–67 |
| Filter (all tasks) | `this.filter$.next(null)` → switch to `tasks$` | n/a (no query) | — | 52–54 |
| Filter (active tasks) | `this.filter$.next(false)` → `filteredTasks$` | `/tasks/{uid}?orderByChild=completed&equalTo=false` | — | 43–45 |
| Filter (completed tasks) | `this.filter$.next(true)` → `filteredTasks$` | `/tasks/{uid}?orderByChild=completed&equalTo=true` | — | 47–49 |

### Component: `src/app/tasks/components/tasks/tasks.component.ts`

| Route Param | Method Triggered | Behavior |
|---|---|---|
| `/tasks` (no param) | `tasksService.filterTasks(undefined)` | Shows all tasks |
| `/tasks;completed=false` | `tasksService.filterTasks('false')` | Shows active tasks |
| `/tasks;completed=true` | `tasksService.filterTasks('true')` | Shows completed tasks |

Note: Angular matrix URL syntax is used (`;completed=true` not `?completed=true`).

### Component: `src/app/tasks/components/task-list/task-list.component.ts`

| UI Event | Emits | Handled by TasksComponent as |
|---|---|---|
| `(remove)` on task-item | task object | `tasksService.removeTask($event)` |
| `(update)` on task-item | `{task, changes}` | `tasksService.updateTask($event.task, $event.changes)` |

### Component: `src/app/tasks/components/task-form/task-form.component.ts`

| UI Event | Emits | Handled by TasksComponent as |
|---|---|---|
| Form submit (Enter key) | trimmed title string | `tasksService.createTask($event)` |
| Escape key | — (clears input only, no emit) | n/a |

---

## Routing

| Path | Component | Guard | Behavior |
|---|---|---|---|
| `/` (empty) | `SignInComponent` | `RequireUnauthGuard` | Redirects to `/tasks` if already authenticated |
| `/tasks` | `TasksComponent` | `RequireAuthGuard` | Redirects to `/` if not authenticated |
| `/tasks;completed=false` | `TasksComponent` | `RequireAuthGuard` | Filters to active tasks |
| `/tasks;completed=true` | `TasksComponent` | `RequireAuthGuard` | Filters to completed tasks |

---

## Firebase Security Rules

Defined in `firebase.rules.json`:

```json
{
  "rules": {
    "tasks": {
      "$uid": {
        ".read": "auth !== null && auth.uid === $uid",
        ".write": "auth !== null && auth.uid === $uid",
        ".indexOn": ["completed"]
      }
    }
  }
}
```

- Users can only read/write their own tasks.
- The `completed` field is indexed server-side to allow efficient `orderByChild('completed').equalTo(...)` queries.
- Anonymous users are fully supported (Firebase assigns them a UID).
