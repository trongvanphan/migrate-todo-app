# Spec — auth domain

## Goal
Replace the legacy AngularFireAuth client-only wrapper with a frontend (Next.js) sign-in flow + a backend (FastAPI) ID-token verifier so that protected API calls carry a verified Firebase user.

## Functional Requirements
- FR1: User can sign in via Google, GitHub, anonymous (drop Twitter/Facebook — legacy bit-rot, not core).
- FR2: User can sign out.
- FR3: Frontend exposes a hook `useAuth()` returning `{ user, loading, signInWithGoogle, signInWithGithub, signInAnonymously, signOut }`.
- FR4: Backend exposes a FastAPI dependency `get_current_user` returning a `User { uid, email?, provider }` from a verified Firebase ID token in `Authorization: Bearer <token>`.
- FR5: Unauthenticated requests to protected routes return 401.
- FR6: Frontend route `/sign-in` is shown when no user; `/tasks` redirects to `/sign-in` if unauthenticated.

## Non-Functional
- Token verification adds <50ms to request path (firebase-admin caches public keys).
- No persisted server-side session — JWT-bearer only.

## Out of Scope
- Twitter, Facebook providers.
- Email/password (firebase supports, not used in legacy).
- Server-side rendering of authenticated state (use client-side gating).

## Acceptance
- Sign in with Google → frontend has `user.uid`, can call `GET /api/tasks` and receive 200.
- Call `GET /api/tasks` without token → 401.
- Sign out → next `GET /api/tasks` returns 401.
