# todo-app-migrated

Migration of `todo-angular-firebase-demo` (Angular 4 + Firebase RTDB) to:

- **Backend** — Python FastAPI + SQLAlchemy 2.0 + SQLite/Postgres, JWT auth
- **Frontend** — Next.js 14 (App Router) + React 18 + TypeScript

## Quick start

```bash
# Terminal 1 — backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload     # http://localhost:8000

# Terminal 2 — frontend
cd frontend
cp .env.local.example .env.local
npm install
npm run dev                       # http://localhost:3000
```

## Layout

```
backend/   FastAPI app (auth + tasks routers, SQLAlchemy models, pytest suite)
frontend/  Next.js app (sign-in + tasks pages, auth context, fetch client)
```

## Migration artifacts

See `../migration-artifacts/` and `../migration-state.json` for the SDS pipeline outputs (discovery, spec, design, tasks, verify).
