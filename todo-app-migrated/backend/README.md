# Todo API (FastAPI)

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit SECRET_KEY
uvicorn app.main:app --reload
```

API at http://localhost:8000 · OpenAPI docs at http://localhost:8000/docs.

## Test

```bash
pytest -q
```

## Endpoints

```
POST   /auth/register   {email, password} -> {access_token}
POST   /auth/login      {email, password} -> {access_token}
GET    /auth/me                                (Bearer)
GET    /tasks?filter=all|active|completed      (Bearer)
POST   /tasks           {title}                (Bearer)
PATCH  /tasks/{id}      {title?, completed?}   (Bearer)
DELETE /tasks/{id}                             (Bearer)
```

## Notes

- Dev DB: SQLite (`./todo.db`). For Postgres, set `DATABASE_URL=postgresql+psycopg://user:pass@host/db`.
- JWT HS256, 24h default expiry, secret from `SECRET_KEY`.
- Tables created on app startup via `Base.metadata.create_all`. Swap for Alembic in production.
