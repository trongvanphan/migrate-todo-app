# Tasks — todo

## Bundle B1: Backend (FastAPI)
- T1.1 Project skeleton: `requirements.txt`, `app/main.py`, CORS.
- T1.2 `database.py`, `models.py` (User, Task), table create on startup.
- T1.3 `security.py` (bcrypt, JWT, current_user dep).
- T1.4 `auth.py`: register, login, me.
- T1.5 `tasks.py`: list+filter, create, patch, delete; owner-scoped queries.
- T1.6 `tests/test_api.py`: register→login→CRUD→cross-user isolation.
- T1.7 README with run instructions.

## Bundle B2: Frontend (Next.js)
- T2.1 `package.json`, `tsconfig.json`, `next.config.mjs`.
- T2.2 `lib/api.ts`, `lib/auth.ts` (AuthContext + token storage).
- T2.3 `app/layout.tsx`, `app/page.tsx` (router redirect).
- T2.4 `app/sign-in/page.tsx` — login/register tabs.
- T2.5 `app/tasks/page.tsx` + `TaskItem`, `TaskForm` components.
- T2.6 README.

## Critical path
B1 → B2 (frontend needs API live to test). Within B1: T1.1 → T1.2 → T1.3 → T1.4/T1.5 (parallel) → T1.6.
