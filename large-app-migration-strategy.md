# Large App Migration Strategy
# Scaling SDS Workflow to 2–3 Million Line Codebases

---

## The Core Problem

The standard SDS workflow (spec → design → tasks → execute → verify) works well for small-to-medium apps. At 2–3M LOC, three things break:

1. **Context ceiling** — No single agent can read and reason over the entire codebase at once.
2. **Hidden behavior** — A decade of bug fixes, edge cases, and tribal knowledge lives in places no spec ever captured.
3. **Live system constraint** — You cannot take a 2–3M LOC production system offline to migrate it. Users are using it while you rewrite it.

The solution is not a different workflow — it is adding two phases *before* spec work begins, and changing execution from sequential-single-team to parallel-multi-domain.

---

## Enhanced Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ENHANCED MIGRATION PIPELINE                     │
│                                                                     │
│  ┌─────────────┐   ┌─────────────────┐                             │
│  │  PHASE 0    │   │  PHASE 0.5      │                             │
│  │  Discovery  │──►│  Decompose      │  ← NEW (pre-spec)           │
│  │             │   │  (DDD domains)  │                             │
│  └─────────────┘   └────────┬────────┘                             │
│                             │                                       │
│            ┌────────────────┼────────────────┐                     │
│            ▼                ▼                ▼                     │
│     ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│     │  Domain A  │  │  Domain B  │  │  Domain C  │  (parallel)    │
│     │ spec       │  │ spec       │  │ spec       │                │
│     │ design     │  │ design     │  │ design     │                │
│     │ tasks      │  │ tasks      │  │ tasks      │                │
│     │ execute    │  │ execute    │  │ execute    │                │
│     │ verify     │  │ verify     │  │ verify     │                │
│     └─────┬──────┘  └─────┬──────┘  └─────┬──────┘               │
│           └───────────────┼───────────────┘                        │
│                           ▼                                         │
│              ┌────────────────────────┐                            │
│              │  Integration Layer     │                            │
│              │  + Strangler Fig       │                            │
│              │  + API Diff Verify     │                            │
│              └────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 0 — Discovery

**Goal:** Produce a complete, evidence-based feature inventory before writing a single FR.

Without this phase, missing features are not a risk — they are a certainty.

### 0a: Code Structure Analysis

```bash
# LOC distribution — find where the weight is
find . -name "*.java" -o -name "*.py" -o -name "*.ts" | xargs wc -l | sort -rn | head 50

# Module coupling — which modules import what (Java example)
grep -r "^import" --include="*.java" | awk -F: '{print $2}' | sort | uniq -c | sort -rn | head 30

# High-churn files — what changed most in git history
git log --format=format: --name-only | sort | uniq -c | sort -rn | head 50
# High churn = high business value AND high bug risk — prioritize these domains
```

Produce a **code map document** with:
- LOC per top-level module
- Dependency graph (which modules depend on which)
- Churn ranking (highest to lowest)
- External system integrations (databases, message queues, third-party APIs)

### 0b: Feature Surface Enumeration

Use all five sources. Missing any one of them guarantees missing features.

```
Source                   Technique                  What you find
──────────────────────   ────────────────────────   ──────────────────────────────────
UI screens               Screenshot every state     Visible features + empty states +
                         (Playwright crawl)         error states + disabled states

API routes               Grep controllers/routes    Every endpoint including internal,
                                                    admin, webhook, background job

Database tables          Schema extraction          Every entity the system manages
                         + FK relationships         + implicit relationships

Test suite               Extract test descriptions  Every requirement someone cared
                         from it/test_/@Test        about enough to write a test for

Git log                  grep fix|bug|edge|case     Every implicit requirement learned
                         in commit messages         from production incidents
```

#### UI Screen Crawl (Playwright example)

```javascript
// crawl-screens.js
const { chromium } = require('playwright');
const fs = require('fs');

const routes = [
  '/login', '/register', '/dashboard', '/settings',
  '/orders', '/orders/123', '/orders/new',
  // ... enumerate all known routes
];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:3000');
  // sign in as test user
  for (const route of routes) {
    await page.goto(`http://localhost:3000${route}`);
    await page.screenshot({ path: `screens${route.replace(/\//g, '-')}.png`, fullPage: true });
  }
})();
```

Store screenshots in `discovery/screens/`. Each unique screen = at least one AC cluster.

#### The "Feature from Every Table" Rule

```
For every database table, ask these four questions:
  1. Can a user CREATE rows? → Create FR
  2. Can a user READ/LIST rows? → View + Filter FR
  3. Can a user UPDATE rows? → Edit FR
  4. Can a user DELETE rows? → Delete FR

Then ask: are there rows a user CANNOT modify?
  → Ownership + authorization FRs

Then ask: are there state transitions?
  → Status/workflow FRs (e.g. order: pending → confirmed → shipped → delivered)
```

This alone captures 80% of missing FRs before you talk to a single stakeholder.

#### API Route Enumeration

```bash
# Express.js
grep -r "router\.\(get\|post\|put\|patch\|delete\)" --include="*.ts" -h | sort | uniq

# Spring Boot
grep -r "@\(Get\|Post\|Put\|Delete\|Patch\)Mapping" --include="*.java" -h | sort | uniq

# FastAPI
grep -r "@app\.\(get\|post\|put\|patch\|delete\)" --include="*.py" -h | sort | uniq

# Django
grep -r "path\|re_path\|url" --include="urls.py" -rh | sort | uniq
```

Every route = at least one FR. Undocumented routes = features the spec writer didn't know about.

#### Test Suite as Spec

```bash
# Extract test names — these ARE your requirements
grep -r "it(\|test(\|def test_\|@Test" --include="*.spec.ts" --include="*.test.ts" \
     --include="*_test.py" --include="*Test.java" -h | sort | uniq
```

Every test name maps to an AC. Example:
```
"should not allow cancellation after 48 hours"
→ AC: Given an order created more than 48 hours ago,
       When the user clicks Cancel,
       Then the cancel button is disabled and an error message is shown.
```

#### Git Log as Spec

```bash
git log --oneline --all \
  | grep -iE "fix|bug|edge|case|handle|when|should|must|cannot|prevent|validate" \
  | head 200
```

Every bug fix is a hidden requirement. "Fix crash when user has no billing address" = an AC that will never appear in the UI — but must be covered in your spec.

### 0c: Produce Discovery Artifacts

```
discovery/
├── code-map.md          ← LOC, coupling, churn ranking, external systems
├── screen-inventory/    ← screenshots of every UI state
│   ├── 001-login.png
│   ├── 002-login-error-invalid.png
│   ├── 003-login-error-locked.png
│   └── ...
├── api-routes.md        ← every endpoint grouped by domain
├── db-schema.md         ← all tables, columns, FKs, constraints
├── test-as-spec.md      ← extracted test names mapped to implied ACs
└── git-log-findings.md  ← notable bug fixes → implied requirements
```

**Gate:** Do not start Phase 0.5 until all five discovery artifacts exist and have been reviewed by a domain expert (product owner or tech lead who worked on the legacy app).

---

## Phase 0.5 — Domain Decomposition

**Goal:** Divide the system into independently migratable domains (bounded contexts). Each domain becomes its own SDS cycle.

### How to find domain boundaries

```
Signal                             What it means
─────────────────────────────────  ────────────────────────────────────
Low cross-module imports           Natural boundary — can be extracted
Separate database schema prefix    Already isolated at data level
Separate team ownership            Cognitive boundary = code boundary
Different release cadence          Independent deployability possible
No shared mutable state            Safe to extract
```

### Draw the Context Map

```
                        ┌─────────────────────┐
                        │    API Gateway /     │
                        │    Reverse Proxy     │
                        └──────────┬──────────┘
                                   │
           ┌───────────────────────┼──────────────────────┐
           │                       │                      │
    ┌──────▼──────┐         ┌──────▼──────┐       ┌──────▼──────┐
    │    Auth     │         │   Orders    │       │   Catalog   │
    │   Domain    │◄────────│   Domain   │──────►│   Domain    │
    │             │  (reads  │            │(reads  │             │
    │  users      │  user)   │  orders    │ items) │  products   │
    │  sessions   │         │  payments  │       │  inventory  │
    │  permissions│         │  returns   │       │  search     │
    └─────────────┘         └─────────────┘       └─────────────┘

Arrow direction = dependency (Domain A → Domain B means A calls B)
Migrate in reverse dependency order: leaf domains first.
```

### Set Migration Order

```
Priority  Domain    Why first/last
────────  ────────  ──────────────────────────────────────────
1st       Auth      Every other domain depends on it;
                    smallest blast radius if it breaks
2nd       Catalog   Read-heavy, stateless, no writes from other domains
3rd       Search    Depends only on Catalog
4th       Orders    Depends on Auth + Catalog (both already migrated)
Last      Payments  Most critical; migrate only after everything else proven
```

**Rule:** Never migrate a domain before all domains it depends on are migrated and verified in production.

---

## Per-Domain SDS Cycle

Each domain runs the standard SDS cycle independently. Key differences from small-app SDS:

### Spec: Hierarchical FRs

```
spec-driven/{domain}/spec.md

Epic level:
  EP-1: Order Management

Feature level:
  FR-1.1: Create order
  FR-1.2: View order history
  FR-1.3: Cancel order

Story level (ACs):
  AC-1.3.1: Given order < 48h old, When Cancel clicked, cancel succeeds
  AC-1.3.2: Given order > 48h old, When Cancel clicked, error shown
  AC-1.3.3: Given order status=shipped, When Cancel clicked, button disabled
```

Do not write a single flat FR list for a 2–3M LOC app. You will miss things and lose traceability.

### Design: Research the Integration Boundary First

The biggest risk in per-domain design is **breaking the contracts other domains depend on**. Document these explicitly before anything else:

```
Inbound contracts  (what OTHER domains call from THIS domain):
  GET /auth/me → { user_id, email, roles }
  POST /auth/verify-token → { valid: bool, user_id }

Outbound contracts (what THIS domain calls from OTHER domains):
  GET /catalog/products/{id} → { price, available }
  POST /payments/charge → { amount, user_id }

These contracts must NOT change. If they must change: version them first.
```

### Execute: Strangler Fig Pattern

Do not replace the legacy domain all at once. Route traffic incrementally.

```
                  ┌──────────────┐
                  │  API Gateway │
                  └──────┬───────┘
                         │
              ┌──────────▼──────────┐
              │   Feature Flags /   │
              │   Traffic Router    │
              └──────────┬──────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
  ┌─────────────┐                 ┌─────────────┐
  │   Legacy    │                 │     New     │
  │   Domain    │                 │   Domain    │
  │  (old code) │                 │  (migrated) │
  └─────────────┘                 └─────────────┘

Week 1:   new=1%,  legacy=99%
Week 2:   new=10%, legacy=90%
Week 4:   new=50%, legacy=50%
Week 6:   new=99%, legacy=1%  (keep 1% as canary fallback)
Week 8:   new=100%, legacy=decommission
```

### Verify: API Diff Testing

Static code review is insufficient at this scale. Run both systems simultaneously and diff responses.

```
                    Production traffic
                           │
           ┌───────────────┴───────────────┐
           │                               │
           ▼                               ▼
    ┌─────────────┐                 ┌─────────────┐
    │   Legacy    │                 │     New     │
    │  response A │                 │  response B │
    └──────┬──────┘                 └──────┬──────┘
           │                               │
           └───────────────┬───────────────┘
                           ▼
                    ┌─────────────┐
                    │    DIFF     │
                    │   Engine    │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       Responses match            Responses differ
       → log + continue           → alert + log +
                                    keep legacy response
                                    + create ticket
```

Any diff = a missing feature, a behavior change, or a bug in the new system.

---

## Anti-Missing-Feature Techniques Summary

| Technique | When to use | What it catches |
|-----------|-------------|-----------------|
| Screenshot every UI state | Phase 0 | Empty states, error states, disabled states, permission variants |
| API route enumeration | Phase 0 | Undocumented endpoints, admin routes, webhook handlers |
| Feature-from-every-table | Phase 0 | CRUD operations, ownership rules, state machines |
| Test suite as spec | Phase 0 | Edge cases, validation rules, access control |
| Git log archaeology | Phase 0 | Production incidents → hidden requirements |
| Domain expert review | Phase 0 gate | Tribal knowledge not in code or tests |
| API diff testing | Verify phase | Behavioral differences invisible to static analysis |
| Parallel run + canary | Execute phase | Real-world usage patterns not covered by tests |

---

## Comparison: Small App vs Large App

| Dimension | Small app (current SDS) | Large app (enhanced SDS) |
|-----------|------------------------|--------------------------|
| Phases | 5 (spec→verify) | 7 (discovery→decompose→5×SDS per domain) |
| Spec files | 1 spec.md | 1 per domain + cross-domain integration spec |
| Execution | Sequential, 1 team | Parallel, 1 team per domain |
| Migration strategy | Big bang (replace all at once) | Strangler Fig (incremental, always live) |
| Verification | Static code review + unit tests | API diff + parallel run + canary rollout |
| Timeline | Days to weeks | Months to years |
| Missing feature risk | Low (codebase is readable in full) | High without Phase 0 |
| Rollback | Revert the branch | Feature flag to legacy (instant) |

---

## Migration Timeline Template (2–3M LOC)

```
Month 1–2:   Phase 0 — Discovery (all five techniques)
Month 2:     Phase 0.5 — Domain decomposition + migration order
Month 3–4:   Domain A (Auth) — full SDS cycle
Month 4–6:   Domain B (Catalog) — full SDS cycle  ← parallel with A after Phase 0
Month 6–9:   Domain C (Orders) — full SDS cycle
Month 9–12:  Domain D (Payments) — full SDS cycle
Month 12–15: Integration layer + cross-domain verify + strangler fig completion
Month 15+:   Legacy decommission (domain by domain)
```

The timeline scales with the number of domains, not the total LOC. A 3M LOC app with clean domain boundaries migrates faster than a 500K LOC monolith with everything tangled together.

---

## Key Rules

1. **Discover before you specify.** A spec written without Phase 0 will miss features. Not might miss — will miss.

2. **Migrate in dependency order.** Leaf domains (no outbound dependencies) first. Core domains (everything depends on them) last — or first if they are Auth.

3. **Never break existing contracts.** Document inbound/outbound contracts before designing. Version before changing.

4. **Always stay live.** Strangler Fig is not optional at this scale. Big-bang migrations of 2–3M LOC systems fail.

5. **API diff is the only complete verification.** Static analysis and unit tests cannot verify behavioral parity with a legacy system. Run both in parallel and compare.

6. **Git log and test suite are specs.** The single most reliable source of hidden requirements is the history of what broke in production.
