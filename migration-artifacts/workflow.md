# Migration Workflow Runbook

This document explains how to run the full SDS migration pipeline, from legacy codebase to working new implementation.

---

## Table of Contents

1. [How to use SKILL.md as a Claude Code skill](#1-using-skillmd-as-a-claude-code-skill)
2. [How to run each sub-agent manually](#2-running-sub-agents-manually)
3. [Decision tree: small app vs large app](#3-decision-tree)
4. [Example: small app with 1 domain](#4-example-small-app)
5. [Example: large app with 4 domains](#5-example-large-app)
6. [Adapting TECH_STACK for different stacks](#6-adapting-tech_stack)

---

## 1. Using SKILL.md as a Claude Code skill

### Installation

Copy `SKILL.md` into your project's Claude Code skills folder:

```bash
mkdir -p .claude/skills/migration
cp migration-artifacts/SKILL.md .claude/skills/migration/SKILL.md
```

### Invocation

In Claude Code, type:
```
/migration
```

Claude will ask for:
- `LEGACY_PATH` — path to your legacy app
- `OUTPUT_PATH` — where to write the new app
- `APP_SIZE` — `small` or `large`
- `TECH_STACK` — your target stack (see section 6)
- `DOMAINS` — list of domains, or `auto` to derive from the codebase

Claude will then run the full pipeline, dispatching sub-agents for each phase.

---

## 2. Running Sub-Agents Manually

Each file in `migration-artifacts/sub-agents/` is a standalone prompt. To run one manually:

1. Open the file.
2. Replace every `{{PARAM}}` placeholder with your actual value.
3. Paste the entire file content as a task in Claude Code.

### Parameter substitution example

If your `{{DOMAIN}}` is `tasks` and `{{LEGACY_PATH}}` is `/repo/old-app/src`, replace:
- Every `{{DOMAIN}}` → `tasks`
- Every `{{LEGACY_PATH}}` → `/repo/old-app/src`

### Manual pipeline order

```
1. discovery.md         (if large app)
2. domain-decompose.md  (if large app)
3. spec.md              (once per domain)
4. design.md            (once per domain)
5. tasks.md             (once per domain)
6. execute.md           (once per domain)
7. verify.md            (once per domain)
```

---

## 3. Decision Tree

```
Is the legacy app under ~5000 LOC with 1-2 clear feature areas?
├── YES → Small App Path
│   ├── Skip phases 0 and 0.5
│   ├── Manually define 1-2 domain names
│   └── Run: spec → design → tasks → execute → verify
│
└── NO → Large App Path
    ├── Run Phase 0 (discovery)
    ├── Run Phase 0.5 (domain-decompose)
    ├── Read discovery/domain-map.md to get domain list
    └── For each domain in parallel: spec → design → tasks → execute → verify
```

**When in doubt, use the large app path.** Discovery is cheap and provides valuable context even for medium-sized apps.

---

## 4. Example: Small App with 1 Domain

**Scenario**: Migrating a simple todo app (Angular 4 + Firebase) to Next.js 14 + PostgreSQL. Single domain: `tasks` (includes auth because auth is thin — just Firebase anonymous auth + UID).

### Step 1 — Set your parameters

```
LEGACY_PATH:  /repo/todo-angular-firebase-demo/src/app
OUTPUT_PATH:  /repo/todo-app-migrated
APP_SIZE:     small
DOMAINS:      tasks
TECH_STACK:   (see section 6 — Next.js example)
```

### Step 2 — Write the spec

Open `sub-agents/spec.md`, replace:
- `{{DOMAIN}}` → `tasks`
- `{{LEGACY_PATH}}` → `/repo/todo-angular-firebase-demo/src/app`

Paste into Claude Code. Wait for `spec-driven/tasks/spec.md` to be written.

### Step 3 — Write the design

Open `sub-agents/design.md`, replace:
- `{{DOMAIN}}` → `tasks`
- `{{TECH_STACK}}` → your JSON (see section 6)

Paste into Claude Code. Wait for `spec-driven/tasks/design.md` to be written.

### Step 4 — Decompose tasks

Open `sub-agents/tasks.md`, replace:
- `{{DOMAIN}}` → `tasks`

Paste into Claude Code. Wait for `spec-driven/tasks/tasks.md` and `bundle-*.md` files.

### Step 5 — Execute

Open `sub-agents/execute.md`, replace:
- `{{DOMAIN}}` → `tasks`
- `{{OUTPUT_PATH}}` → `/repo/todo-app-migrated`

Paste into Claude Code. Claude will implement all bundles and commit after each one.

### Step 6 — Verify

Open `sub-agents/verify.md`, replace:
- `{{DOMAIN}}` → `tasks`

Paste into Claude Code. Wait for `spec-driven/tasks/verify-report.md`. Review the report and address any open findings.

### Expected output

```
spec-driven/
  tasks/
    spec.md
    design.md
    tasks.md
    bundle-1.md
    bundle-2.md
    bundle-3.md
    verify-report.md

todo-app-migrated/
  src/
    tasks/
      components/
      hooks/
      services/
      repositories/
      __tests__/
  prisma/
    schema.prisma
  package.json
  tsconfig.json
```

---

## 5. Example: Large App with 4 Domains

**Scenario**: Migrating a SaaS project management app (Rails + MySQL) to Next.js 14 + PostgreSQL + Prisma. Domains: `auth`, `organizations`, `projects`, `tasks`.

### Step 1 — Discovery

Open `sub-agents/discovery.md`, replace:
- `{{LEGACY_PATH}}` → `/repo/rails-app`

Paste into Claude Code. Wait for all 5 discovery files.

### Step 2 — Domain decompose

Open `sub-agents/domain-decompose.md`, replace:
- `{{LEGACY_PATH}}` → `/repo/rails-app`

Paste into Claude Code. Read `discovery/domain-map.md`. Confirm the 4 domains and execution order.

### Step 3 — Spec all domains (parallel)

Dispatch 4 spec sub-agents simultaneously (one per domain). In Claude Code, you can use the Task tool or paste each in parallel sessions:

```
Domain: auth       → spec-driven/auth/spec.md
Domain: organizations → spec-driven/organizations/spec.md
Domain: projects   → spec-driven/projects/spec.md
Domain: tasks      → spec-driven/tasks/spec.md
```

### Step 4 — Design all domains (parallel)

Dispatch 4 design sub-agents simultaneously:

```
Domain: auth
Domain: organizations
Domain: projects
Domain: tasks
```

### Step 5 — Tasks all domains (parallel)

Dispatch 4 tasks sub-agents simultaneously.

### Step 6 — Execute in dependency order

From `discovery/domain-map.md`, the execution order is:

```
Phase A (sequential — foundational):
  auth              ← other domains depend on this

Phase B (parallel after auth):
  organizations
  projects

Phase C (parallel after B):
  tasks             ← depends on projects
```

Execute:
1. Execute `auth` domain first. Wait for completion.
2. Execute `organizations` and `projects` in parallel.
3. Execute `tasks` after both complete.

### Step 7 — Verify all domains (parallel)

Dispatch 4 verify sub-agents simultaneously after all domains are executed.

### Expected timeline

```
Phase 0: Discovery           — 5-10 min
Phase 0.5: Domain decompose  — 5 min
Phase 1: Spec (parallel)     — 15-20 min
Phase 2: Design (parallel)   — 15-20 min
Phase 3: Tasks (parallel)    — 10-15 min
Phase 4: Execute (sequential/parallel per order) — 60-120 min
Phase 5: Verify (parallel)   — 15-20 min
Total:                       — 2-3 hours
```

---

## 6. Adapting TECH_STACK for Different Stacks

The `{{TECH_STACK}}` JSON is passed to the design sub-agent. It informs all technical decisions.

### Next.js 14 + PostgreSQL + Prisma

```json
{
  "language": "TypeScript",
  "runtime": "Node 20",
  "framework": "Next.js 14",
  "router": "App Router",
  "state": "Zustand",
  "auth": "NextAuth.js v5",
  "database": "PostgreSQL",
  "orm": "Prisma 5",
  "validation": "Zod",
  "testing": "Vitest + React Testing Library + Playwright",
  "styling": "Tailwind CSS",
  "deployment": "Vercel",
  "notes": "Server Components by default, Client Components when needed for interactivity"
}
```

### Express + MongoDB

```json
{
  "language": "TypeScript",
  "runtime": "Node 20",
  "framework": "Express 4",
  "auth": "Passport.js + JWT",
  "database": "MongoDB",
  "orm": "Mongoose 8",
  "validation": "Zod",
  "testing": "Jest + Supertest",
  "deployment": "AWS ECS",
  "notes": "REST API only, no UI"
}
```

### FastAPI + PostgreSQL

```json
{
  "language": "Python 3.12",
  "runtime": "Python",
  "framework": "FastAPI",
  "auth": "python-jose + passlib",
  "database": "PostgreSQL",
  "orm": "SQLAlchemy 2.0 + Alembic",
  "validation": "Pydantic v2",
  "testing": "pytest + httpx",
  "deployment": "AWS Lambda",
  "notes": "Async everywhere, use async SQLAlchemy"
}
```

### React + Supabase

```json
{
  "language": "TypeScript",
  "runtime": "Node 20",
  "framework": "React 18 + Vite",
  "auth": "Supabase Auth",
  "database": "Supabase (PostgreSQL)",
  "orm": "Supabase JS client",
  "validation": "Zod",
  "testing": "Vitest + React Testing Library",
  "deployment": "Netlify",
  "notes": "No custom backend — all DB access via Supabase RLS policies"
}
```

### Rails API + React

```json
{
  "language": "Ruby / TypeScript",
  "runtime": "Ruby 3.3 / Node 20",
  "framework": "Rails 7 API + React 18",
  "auth": "Devise + JWT",
  "database": "PostgreSQL",
  "orm": "ActiveRecord",
  "validation": "Rails validators + Zod (frontend)",
  "testing": "RSpec + Capybara (backend) + Vitest (frontend)",
  "deployment": "Heroku",
  "notes": "Rails API mode only, React in separate app"
}
```

---

## Tips

- **Start with a test run on one domain** before running the full pipeline. This lets you validate your TECH_STACK choice and catch issues early.
- **Save your parameter values** in a file like `.migration-config.md` at the repo root so you can reference them across sessions.
- **Review each phase output** before dispatching the next phase. A bad spec produces a bad design. A bad design produces bad tasks.
- **The verify phase is not optional.** It catches regressions and security issues automatically.
- **Commits are your checkpoints.** If something goes wrong during execute, you can `git reset` to the last good bundle commit.
