# Discovery: Database Schema (Firebase Realtime Database)
> Phase 0 — todo-angular-firebase-demo

---

## Database URL

```
https://ng2-todo-app.firebaseio.com
```

(Configured in `src/environments/firebase.ts`)

---

## Schema: Path Structure

The database has a single top-level collection:

```
/
└── tasks/
    └── {uid}/              ← Firebase Auth user ID (string)
        └── {taskKey}/      ← Auto-generated push key (Firebase unique ID)
            ├── title       : string
            ├── completed   : boolean
            └── createdAt   : number (Unix ms timestamp, ServerValue.TIMESTAMP)
```

---

## Entity: Task

**Path:** `/tasks/{uid}/{taskKey}`

| Field | Type | Required | Default | Source |
|---|---|---|---|---|
| `title` | `string` | Yes | — | User input (trimmed before write) |
| `completed` | `boolean` | Yes | `false` | Set at creation; toggled via update |
| `createdAt` | `number` (epoch ms) | Yes | `firebase.database.ServerValue.TIMESTAMP` | Server-assigned at creation |
| `$key` | `string` (virtual) | n/a | Firebase push key | AngularFire adds this to each list item at read time |

### TypeScript Interface (from `src/app/tasks/models/task.ts`)

```typescript
export interface ITask {
  $key?: string;        // virtual — not stored in DB, injected by AngularFire
  completed: boolean;
  createdAt: Object;    // typed as Object; actual value is number (epoch ms)
  title: string;
}

export class Task implements ITask {
  completed = false;
  createdAt = firebase.database.ServerValue.TIMESTAMP;  // replaced by server
  title: string;

  constructor(title: string) {
    this.title = title;
  }
}
```

---

## Entity-Relationship Diagram

```
┌─────────────────────────────────┐
│  Firebase Auth User             │
│  uid: string (auth token claim) │
└────────────┬────────────────────┘
             │ 1
             │ owns
             │ *
┌────────────▼────────────────────┐
│  Task                           │
│  ─────────────────────────────  │
│  $key      : string (push key)  │
│  title     : string             │
│  completed : boolean            │
│  createdAt : number (epoch ms)  │
└─────────────────────────────────┘
```

- One user owns zero or more tasks.
- Tasks are physically nested under the user's UID in the DB path, enforcing isolation at the data layer.
- No foreign keys, no joins — flat document model.

---

## Index

```json
"tasks": {
  "$uid": {
    ".indexOn": ["completed"]
  }
}
```

The `completed` field is indexed to support efficient server-side filtering:
- `orderByChild('completed').equalTo(false)` → active tasks
- `orderByChild('completed').equalTo(true)` → completed tasks

Without this index, Firebase would warn and do a full-scan on the client.

---

## Security Rules

```json
"tasks": {
  "$uid": {
    ".read": "auth !== null && auth.uid === $uid",
    ".write": "auth !== null && auth.uid === $uid"
  }
}
```

- Any authenticated user (including anonymous) can read and write only their own subtree.
- No unauthenticated access is allowed.
- No cross-user access is allowed (the `auth.uid === $uid` check enforces this).

---

## Notes for Migration

1. **`$key` is AngularFire-injected** — In the Firebase JS SDK v9 modular API, the key is `doc.id` (Firestore) or the push key from a snapshot `.key` property. The migration must map `$key` → the new primary key field.
2. **`createdAt` is `ServerValue.TIMESTAMP`** — This is a write-time sentinel; the actual stored value is a Unix millisecond integer. In Firestore, the equivalent is `serverTimestamp()` which stores a `Timestamp` object. The filter and sort logic may need to account for this.
3. **No `updatedAt` field** — Tasks have no "last modified" timestamp. The migration can add one if needed.
4. **No soft-delete** — Tasks are hard-deleted via `remove()`. No `deletedAt` or `isDeleted` flag exists.
5. **No pagination** — The service loads all tasks for a user in a single list observable. For large task counts, the migration should consider pagination or virtualized lists.
6. **No task ordering beyond insert order** — Firebase push keys are time-sortable lexicographically, so tasks naturally appear in creation order. If the migration uses a different key strategy (e.g., UUID v4), explicit ordering by `createdAt` will be needed.
