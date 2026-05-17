# Design — todo

## Backend layout (`todo-app-migrated/backend/`)

```
backend/
├── app/
│   ├── main.py          FastAPI app, CORS, router includes
│   ├── database.py      SQLAlchemy engine + SessionLocal + get_db
│   ├── models.py        User, Task ORM models
│   ├── schemas.py       Pydantic request/response models
│   ├── security.py      password hash, JWT encode/decode, current-user dep
│   ├── auth.py          /auth router
│   └── tasks.py         /tasks router
├── tests/
│   └── test_api.py      pytest + TestClient end-to-end
├── requirements.txt
├── .env.example
└── README.md
```

### Data model

```sql
users(id PK, email UNIQUE NOT NULL, hashed_password NOT NULL, created_at)
tasks(id PK, owner_id FK->users.id, title NOT NULL, completed BOOL NOT NULL DEFAULT FALSE, created_at)
INDEX tasks(owner_id, completed)   -- matches source `.indexOn: ["completed"]`
```

### Auth

- bcrypt via `passlib[bcrypt]`.
- JWT via `python-jose`, HS256, `SECRET_KEY` from env, 24h expiry.
- `get_current_user` dependency decodes token and loads user; raises 401 on fail.

## Frontend layout (`todo-app-migrated/frontend/`)

```
frontend/
├── app/
│   ├── layout.tsx           Root layout, AuthProvider
│   ├── page.tsx             redirects to /sign-in or /tasks
│   ├── sign-in/page.tsx     login/register form
│   └── tasks/page.tsx       task list, filter, add, toggle, delete
├── components/
│   ├── TaskItem.tsx
│   └── TaskForm.tsx
├── lib/
│   ├── api.ts               fetch wrapper, attaches bearer token
│   └── auth.ts              token storage (localStorage), AuthContext
├── package.json
├── tsconfig.json
├── next.config.mjs
└── README.md
```

- Client-side React; token in `localStorage` (acceptable for demo; production would use httpOnly cookie via API route).
- `NEXT_PUBLIC_API_URL` env var points to backend.

## Mapping legacy → new

| Legacy (Angular/Firebase) | New |
|---|---|
| `AngularFireAuth.signInWithPopup` | `POST /auth/login` |
| `AngularFireDatabase.list('/tasks/{uid}')` | `GET /tasks` |
| `tasks$.push(new Task(title))` | `POST /tasks` |
| `tasks$.update(key, {completed})` | `PATCH /tasks/{id}` |
| `tasks$.remove(key)` | `DELETE /tasks/{id}` |
| `orderByChild('completed').equalTo(bool)` | `GET /tasks?filter=active\|completed` |
| `RequireAuthGuard` | `useEffect` redirect when no token |
| `firebase.rules.json` per-uid isolation | `WHERE owner_id = current_user.id` in queries |
