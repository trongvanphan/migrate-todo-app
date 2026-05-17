# Tasks — auth domain

## Bundle A: backend-auth
- A1. Scaffold FastAPI project under `todo-app-migrated/backend/` (pyproject.toml, app/main.py, app/core/__init__.py).
- A2. Add `firebase-admin` dependency; implement `app/core/firebase.py` initializer.
- A3. Implement `app/core/auth.py` with `get_current_user` dependency + `User` Pydantic model.
- A4. Add a smoke route `GET /api/me` that returns the current user (sanity for auth dep).
- A5. CORS middleware allowing the frontend origin.

## Bundle B: frontend-auth
- B1. Scaffold Next.js app under `todo-app-migrated/frontend/` (App Router, TS, Tailwind optional).
- B2. Add `firebase` JS SDK; create `lib/firebase.ts`.
- B3. Create `lib/auth-context.tsx` + `useAuth` hook; mount provider in `app/layout.tsx`.
- B4. Build `app/sign-in/page.tsx` with Google / GitHub / Anonymous buttons.
- B5. Create `lib/api.ts` fetch wrapper with bearer-token injection.
- B6. Protected layout group `app/(protected)/layout.tsx` with redirect-to-sign-in.
