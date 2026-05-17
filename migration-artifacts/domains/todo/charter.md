# Domain: todo

**LOC:** 1,267 (source)
**Features:** auth, tasks
**Owner:** solo
**Dependencies:** none

## Scope
Replace the Angular 4 + Firebase RTDB client-only app with:
- Backend: Python FastAPI + SQLAlchemy + SQLite (dev) / Postgres (prod), JWT auth.
- Frontend: Next.js 14 (App Router) + React 18 + TypeScript, calling REST API.

## Out of scope (v1)
- Social OAuth (Google/GitHub/Twitter/Facebook). Replaced with email+password for v1.
- Offline / service-worker caching (Angular source had `sw-precache`; out of scope).
- Data migration from existing Firebase RTDB (demo app, no real users).
