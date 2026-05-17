# Shared Kernel

| Item | Legacy location | New location | Decision |
|------|-----------------|--------------|----------|
| Firebase config | `src/environments/firebase.ts` | Frontend env: `.env.local` (NEXT_PUBLIC_FIREBASE_*); backend env: `.env` (FIREBASE_SERVICE_ACCOUNT_JSON path) | extract |
| Firebase init | `src/app/firebase/firebase.module.ts` | Frontend: `lib/firebase.ts` (client SDK); Backend: `app/core/firebase.py` (firebase-admin) | split |
| ID token validation | (none — pure client) | Backend: `app/core/auth.py` FastAPI dependency | new |
| Task model | `src/app/tasks/models/task.ts` | Backend: `app/domains/tasks/schemas.py` (Pydantic); Frontend: `lib/types.ts` | duplicate (intentional, separate type systems) |
