# Spec — todo

## User stories

1. As a new user I can register with email + password.
2. As a returning user I can sign in with email + password and receive a JWT.
3. As an authenticated user I can list my own tasks, filter all/active/completed.
4. As an authenticated user I can create a task with a title.
5. As an authenticated user I can mark a task complete/incomplete.
6. As an authenticated user I can delete a task.
7. As an authenticated user I can sign out (clear local token).

## Acceptance criteria

- Tasks are isolated per user; user A cannot read/modify user B's tasks (verified by 401/404 on cross-user access).
- Passwords stored bcrypt-hashed; JWT signed HS256 with server secret.
- API responds <200ms p95 for CRUD operations on a local SQLite db with <10K tasks.
- Frontend renders sign-in page when unauthenticated, redirects to /tasks when authenticated.

## API contract (REST, JSON)

```
POST   /auth/register     {email, password}              -> {access_token, token_type}
POST   /auth/login        {email, password}              -> {access_token, token_type}
GET    /auth/me                                          -> {id, email}
GET    /tasks?filter=all|active|completed                -> [{id, title, completed, created_at}]
POST   /tasks             {title}                        -> {id, title, completed, created_at}
PATCH  /tasks/{id}        {title?, completed?}           -> {id, title, completed, created_at}
DELETE /tasks/{id}                                       -> 204
```

Auth: `Authorization: Bearer <jwt>` on all `/tasks/*` and `/auth/me`.
