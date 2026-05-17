# Bundle B-1: Backend Foundation

> Stage: skeleton + depth | Parallel: yes (with B-3 — no shared files) | Files: backend/requirements.txt, backend/.env.example, backend/app/config.py, backend/app/database.py, backend/app/models.py, backend/app/main.py, backend/app/schemas.py, backend/app/dependencies.py, backend/app/routers/auth.py, backend/app/routers/__init__.py

**Bundle Verify**: A running FastAPI instance accepts POST /auth/anonymous and returns a JWT that GET /tasks accepts as a Bearer token.
- **Level**: integration
- **Given**: FastAPI running on localhost:8000 with todo.db initialized
- **Action**: `curl -X POST http://localhost:8000/auth/anonymous` → extract token; `curl -H "Authorization: Bearer <token>" http://localhost:8000/tasks`
- **Outcome**: /auth/anonymous returns `{ access_token, user_id }`; /tasks returns `[]` with 200

---

## Context

**Architecture Decisions:** AD-2 (JWT exchange returns {access_token, user_id}), AD-4 (sync SQLAlchemy + create_all in lifespan), AD-5 (HTTPBearer + python-jose)

**Key Findings:** F-8 (flat app/ layout), F-9 (sync SQLAlchemy, check_same_thread=False), F-10 (HTTPBearer not OAuth2PasswordBearer), F-12 (Pydantic v2, from_attributes=True), F-13 (CORS: allow_credentials + explicit origins), F-14 (create_all in lifespan), F-15 (upsert by provider+provider_id)

**Standards:** S-1 (no Firebase), S-2 (secrets in .env), S-5 (Pydantic v2), S-6 (get_db dependency), S-10 (JWT sub as str)

**Constraints:** C-1 (SQLite writes serialized — acceptable at this scale)

**Relevant ACs:** AC-1.1, AC-1.2, AC-1.3, AC-4.1, AC-5.1, AC-10.1

---

## STEPs

### STEP-1: FastAPI project scaffold + config
**Trace:** `MANUAL -> project scaffold` | **Effort:** S

**Files:**
- `todo-app-migrated/backend/requirements.txt` — create
- `todo-app-migrated/backend/.env` — create
- `todo-app-migrated/backend/.env.example` — create
- `todo-app-migrated/backend/app/__init__.py` — create
- `todo-app-migrated/backend/app/config.py` — create

**Intent:** Establish environment-driven configuration via pydantic-settings. Hardcoded secrets are the primary risk. `DATABASE_URL` defaults to `sqlite:///./todo.db`. `CORS_ORIGINS` is a `list[str]`.

**Implementation guidance:**
1. `requirements.txt`: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `python-jose[cryptography]`, `pydantic-settings`, `python-dotenv`, `pytest`, `httpx`
2. `config.py`: `class Settings(BaseSettings)` with `secret_key: str`, `algorithm: str = "HS256"`, `access_token_expire_days: int = 30`, `database_url: str = "sqlite:///./todo.db"`, `cors_origins: list[str] = ["http://localhost:3000"]`, `model_config = SettingsConfigDict(env_file=".env")`
3. Export `settings = Settings()` singleton
4. `.env.example`: all keys with placeholder values; `.env` gitignored
5. `app/__init__.py`: empty

**Verify:**
- Level: inspection | Given: `.env` with `SECRET_KEY=test` | Action: `from app.config import settings; assert settings.secret_key == "test"` | Outcome: import succeeds

> **Standards:** S-2, S-5

**Dependencies:** Enables STEP-2, STEP-3

---

### STEP-2: Database engine + ORM models
**Trace:** `[FR-4 -> AC-4.1], [FR-5 -> AC-5.1], [FR-10 -> AC-10.1]` | **Informed by:** AD-4, F-9, F-14, F-15 | **Effort:** S

**Files:**
- `todo-app-migrated/backend/app/database.py` — create
- `todo-app-migrated/backend/app/models.py` — create

**Intent:** `check_same_thread=False` is mandatory for SQLite + FastAPI. `UNIQUE(provider, provider_id)` on users is critical for upsert safety. `ON DELETE CASCADE` on tasks.user_id ensures cleanup. `idx_tasks_user_completed` index mirrors Firebase's `orderByChild('completed')`.

**Implementation guidance:**
1. `database.py`: `engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})`; `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`; `Base = declarative_base()`; `def get_db() -> Generator: db = SessionLocal(); try: yield db; finally: db.close()`
2. `models.py User`: id (Integer PK), provider (String), provider_id (String), email (String nullable), name (String nullable), created_at (DateTime server default); UniqueConstraint('provider', 'provider_id')
3. `models.py Task`: id (Integer PK), user_id (Integer FK→users.id cascade), title (String), completed (Boolean default False), created_at (DateTime server default); Index('idx_tasks_user_completed', 'user_id', 'completed')
4. Import Base into models.py; do NOT call create_all here

**Verify:**
- Level: integration | Given: `DATABASE_URL=sqlite:///./test.db` | Action: `Base.metadata.create_all(bind=engine)` | Outcome: users and tasks tables exist; unique constraint present

> **Standards:** S-6, S-10

**Dependencies:** Depends on STEP-1; enables STEP-3, STEP-4

---

### STEP-3: FastAPI app entry point + CORS
**Trace:** `MANUAL -> app wiring` | **Informed by:** F-13, AD-4 | **Effort:** S

**Files:**
- `todo-app-migrated/backend/app/main.py` — create

**Intent:** `allow_origins=["*"]` with `allow_credentials=True` is invalid. Must list exact origins. Lifespan pattern replaces deprecated `@app.on_event("startup")`.

**Implementation guidance:**
1. `@asynccontextmanager async def lifespan(app): Base.metadata.create_all(bind=engine); yield`
2. `app = FastAPI(lifespan=lifespan)`
3. `CORSMiddleware`: `allow_origins=settings.cors_origins`, `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`
4. Mount routers (from STEP-6 and STEP-7 — stub imports OK for now)
5. `@app.get("/")` health check: returns `{"status": "ok"}`

**Verify:**
- Level: integration | Given: FastAPI running | Action: `OPTIONS http://localhost:8000/tasks -H "Origin: http://localhost:3000"` | Outcome: `Access-Control-Allow-Credentials: true` in response

> **Standards:** S-1

**Dependencies:** Depends on STEP-2; enables STEP-6, STEP-7

---

### STEP-4: Pydantic schemas (auth + tasks)
**Trace:** `[FR-1 -> AC-1.1], [FR-1 -> AC-1.2], [FR-4 -> AC-4.1], [FR-5 -> AC-5.1]` | **Informed by:** F-12, F-15, AD-5 | **Effort:** S

**Files:**
- `todo-app-migrated/backend/app/schemas.py` — create

**Intent:** `OAuthLogin` uses `provider_id` not email as identity key. `TaskUpdate` must be fully optional for partial PATCH semantics. `TaskOut` needs `from_attributes=True` for ORM serialization.

**Implementation guidance:**
1. Auth: `OAuthLogin(provider: str, provider_id: str, email: str | None, name: str | None)`, `TokenResponse(access_token: str, user_id: int, token_type: str = "bearer")`
2. Tasks: `TaskCreate(title: str)`, `TaskUpdate(title: str | None = None, completed: bool | None = None)`, `TaskOut(id: int, title: str, completed: bool, created_at: datetime, model_config=ConfigDict(from_attributes=True))`
3. Validate `TaskCreate.title` non-empty via `@field_validator`
4. All schemas use Pydantic v2 (`from pydantic import BaseModel, ConfigDict, field_validator`)

**Verify:**
- Level: inspection | Given: schemas.py | Action: `TaskCreate(title="")` | Outcome: ValidationError; `TaskOut.model_config.from_attributes is True`

> **Standards:** S-5

**Dependencies:** Depends on STEP-1; enables STEP-5, STEP-6, STEP-7

---

### STEP-5: JWT dependency (get_current_user)
**Trace:** `[FR-10 -> AC-10.1], [FR-10 -> AC-10.2]` | **Informed by:** AD-5, F-10, S-10 | **Effort:** S

**Files:**
- `todo-app-migrated/backend/app/dependencies.py` — create

**Intent:** Must raise 401 (not 403) on invalid/expired token — 403 is reserved for ownership violations. JWT `sub` is `str(user.id)` at encode time; cast to `int` at decode. Tampered tokens must not return a user row.

**Implementation guidance:**
1. `security = HTTPBearer()`
2. `def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:`
3. Try/except `JWTError` → 401; `int(payload.get("sub"))` → 401 if missing
4. `db.query(User).filter(User.id == user_id).first()` → 401 if None
5. Return the User ORM object

**Verify:**
- Level: unit | Given: valid JWT for user_id=1 | Action: call via TestClient | Outcome: returns User(id=1); expired token → 401; tampered token → 401

> **Standards:** S-6, S-10

**Dependencies:** Depends on STEP-2, STEP-4; enables STEP-6, STEP-7, STEP-8

---

### STEP-6: Auth router (/auth/oauth + /auth/anonymous)
**Trace:** `[FR-1 -> AC-1.1], [FR-1 -> AC-1.2], [FR-1 -> AC-1.3]` | **Informed by:** AD-2, F-15, NFR-2 | **Effort:** M

**Files:**
- `todo-app-migrated/backend/app/routers/__init__.py` — create
- `todo-app-migrated/backend/app/routers/auth.py` — create
- `todo-app-migrated/backend/app/main.py` — modify (mount auth router)

**Intent:** Upsert by `(provider, provider_id)` — NOT email. Anonymous creates new user per sign-in (uuid4 provider_id). Token expiry = `settings.access_token_expire_days` days.

**Implementation guidance:**
1. `POST /auth/oauth`: query User by provider+provider_id; if not found create; call `create_access_token({"sub": str(user.id)})`; return `TokenResponse`
2. `POST /auth/anonymous`: `User(provider="anonymous", provider_id=str(uuid4()))`; same token generation
3. `create_access_token(data)`: `jose.jwt.encode({**data, "exp": utcnow() + timedelta(days=settings.access_token_expire_days)}, settings.secret_key, algorithm=settings.algorithm)`
4. Both return `TokenResponse(access_token=token, user_id=user.id)`
5. Mount: `app.include_router(auth.router, prefix="/auth", tags=["auth"])` in main.py

**Test (test-after):** `tests/test_auth.py` — POST /auth/oauth twice with same provider_id → same user_id; POST /auth/anonymous → valid JWT; expired JWT → 401

**Verify:**
- Level: integration | Given: running FastAPI | Action: POST /auth/oauth twice with same provider_id | Outcome: same user_id returned both times; JWT decodable

> **Standards:** S-2, S-10

**Dependencies:** Depends on STEP-3, STEP-4, STEP-5; enables B-4 (STEP-13)
