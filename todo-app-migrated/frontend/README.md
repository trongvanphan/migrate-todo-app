# Todo Frontend (Next.js 14)

## Setup

```bash
cd frontend
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL if backend is not localhost:8000
npm install
npm run dev
```

App at http://localhost:3000.

## Build / typecheck

```bash
npm run typecheck
npm run build
```

## Architecture

- App Router (`app/`). Client components mark with `"use client"`.
- `lib/auth.tsx` — `AuthContext` holds JWT in `localStorage`. (For production, swap to httpOnly cookie via a Next.js Route Handler.)
- `lib/api.ts` — fetch wrapper, attaches `Authorization: Bearer`.
- `app/page.tsx` — redirects to `/tasks` if authed, else `/sign-in`.
- `app/sign-in/page.tsx` — email+password register/login, stores returned JWT.
- `app/tasks/page.tsx` — list, filter (all/active/completed), add, toggle, delete.

## Mapping from Angular source

| Angular | Next.js |
|---|---|
| `AuthService` (AngularFireAuth) | `lib/auth.tsx` (`AuthContext`) |
| `TasksService` (AngularFireDatabase) | `lib/api.ts` (REST calls) |
| `RequireAuthGuard` | `useEffect` redirect in `app/tasks/page.tsx` |
| `TaskListComponent` / `TaskItemComponent` | `components/TaskItem.tsx` |
| `TaskFormComponent` + `AutoFocusDirective` | `components/TaskForm.tsx` (uses `autoFocus`) |
