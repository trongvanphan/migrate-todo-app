# Design — auth domain

## Frontend (Next.js App Router)
- `lib/firebase.ts` — initialize Firebase JS SDK from `NEXT_PUBLIC_FIREBASE_*` env vars; export `auth`, `signInWithPopup`, providers, `signInAnonymously`, `signOut`.
- `lib/auth-context.tsx` — `AuthProvider` wraps app in `app/layout.tsx`; subscribes to `onAuthStateChanged`; exposes `useAuth()` returning the context value.
- `lib/api.ts` — `apiFetch(path, init)` injects `Authorization: Bearer ${await user.getIdToken()}` if signed in; throws on 401.
- `app/sign-in/page.tsx` — client component with provider buttons.
- `app/(protected)/layout.tsx` — client guard redirecting to `/sign-in` when `!user && !loading`.

## Backend (FastAPI)
- `app/core/firebase.py` — initialize `firebase_admin` once at startup from `GOOGLE_APPLICATION_CREDENTIALS` env var.
- `app/core/auth.py` — `get_current_user` dependency:
  - Read `Authorization` header → strip `Bearer `.
  - `firebase_admin.auth.verify_id_token(token)` → returns dict.
  - Map to Pydantic `User(uid: str, email: str | None, provider: str | None)`.
  - On failure raise `HTTPException(401, "Invalid or expired token")`.

## Why not server sessions
Single-page client already holds the Firebase JS session; introducing cookies adds CSRF surface and a second source of truth. Bearer-token-on-each-request is simplest for an SPA→API migration.

## Why drop Twitter/Facebook
Legacy code imports them but they were demo-only. Re-adding is cheap later; carrying dead provider buttons isn't.
