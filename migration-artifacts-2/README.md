# Migration Artifacts v2 — Large-App Edition

Toolkit for migrating **large legacy applications (100K–5M+ LOC)** to a modern stack using a parallelized, state-driven, strangler-fig variant of the SDS methodology.

v2 exists because v1 silently breaks at scale. See [`CHANGELOG-vs-v1.md`](./CHANGELOG-vs-v1.md) for the 20 capabilities v1 cannot deliver.

---

## Table of Contents

1. [When to use v1 vs v2](#when-to-use-v1-vs-v2)
2. [What's new vs v1](#whats-new-vs-v1)
3. [Folder structure](#folder-structure)
4. [Installation](#installation)
5. [Usage Guide](#usage-guide) ← **the runbook**
   - [Step 0: Prerequisites](#step-0-prerequisites)
   - [Step 1: Initialize migration-state.json](#step-1-initialize-migration-statejson)
   - [Step 2: Phase 0 — Discovery](#step-2-phase-0--discovery)
   - [Step 3: Phase 0.5 — Decompose](#step-3-phase-05--decompose)
   - [Step 4: Per-domain SDS cycle (phases 1–5)](#step-4-per-domain-sds-cycle-phases-15)
   - [Step 5: Phase 6 — Strangler-Fig rollout](#step-5-phase-6--strangler-fig-rollout)
   - [Step 6: Phase 7 — Verify (10 dimensions)](#step-6-phase-7--verify-10-dimensions)
   - [Step 7: Phase 8 — API diff](#step-7-phase-8--api-diff)
   - [Step 8: Phase 9 — Decommission](#step-8-phase-9--decommission)
6. [Parameters reference](#parameters-reference)
7. [Daily workflow rhythm](#daily-workflow-rhythm)
8. [Onboarding a new contributor](#onboarding-a-new-contributor)
9. [Troubleshooting / FAQ](#troubleshooting--faq)
10. [See also](#see-also)

---

## When to use v1 vs v2

| LOC of legacy app | Domains expected | Recommendation |
|-------------------|------------------|----------------|
| under 5K          | 1                | v1 small-app path |
| 5K – 100K         | 1–3              | v1 large-app path |
| 100K – 1M         | 3–8              | **v2 light** (skip 06/08/09 phases) |
| 1M – 5M           | 5–15             | **v2 full** (all 10 phases) |
| over 5M           | 10+              | **v2 full + sub-domain decomp** (run `feature-spec.md` per feature within each domain) |

If unsure: pick v2. v2 contains v1 as a subset — every v1 phase has a v2 counterpart with the same outputs plus state-file updates.

---

## What's new vs v1

1. **10 phases** (not 7): Discovery, Decompose, Spec, Design, Tasks, Execute, **Strangler-Fig**, Verify, **API-Diff**, **Decommission**.
2. **Persistent state file** (`migration-state.json`) — every sub-agent reads/writes it. Migrations resume across sessions, weeks, months.
3. **Scheduler sub-agent** — computes which sub-agents to dispatch next, respecting dependencies and concurrency caps.
4. **Per-module discovery** — each scanner operates on ONE module at a time, max ~50K LOC per scan. Solves context overflow.
5. **Sub-domain decomposition** — domains over 200K LOC split into features via `feature-spec.md`.
6. **Strangler-Fig automation** — generates working nginx / ALB / Cloudflare Worker routing configs + feature-flag wiring + fallback middleware + canary schedule with SLO gates.
7. **API-Diff harness** — runnable parallel-run comparator with semantic-equivalence rules.
8. **Decommission phase** — gated removal of legacy code: traffic-verify → dependency-check → archival → soft-delete → hard-delete.
9. **10 verify dimensions** (not 6): traceability, completeness, code-quality, test-quality, regression, security, **performance, observability, compliance, data-parity**.
10. **Team ownership, rollback runbooks, contract registry, CODEOWNERS templates**.

---

## Folder structure

```
migration-artifacts-2/
├── README.md               ← this file
├── SKILL.md                ← Claude Code skill orchestrating the 10-phase pipeline
├── workflow.md             ← runbook with LOC→strategy matrix and example timelines
├── CHANGELOG-vs-v1.md      ← 20 capability gaps v2 closes
├── REVIEW-REPORT.md        ← independence-review audit (PASS WITH CAVEATS)
├── coordinator/
│   ├── migration-state.schema.json  ← canonical state schema
│   ├── scheduler.md                 ← dispatches next sub-agents
│   └── progress-dashboard.md        ← human-readable status
├── sub-agents/
│   ├── 00-discovery/       ← 8 scanners (per-module, bounded)
│   ├── 01-decompose/       ← 5 decomposition agents
│   ├── 02-spec/            ← domain + feature spec
│   ├── 03-design/          ← domain + contract + data-migration design
│   ├── 04-tasks/           ← bundle decomp + critical path
│   ├── 05-execute/         ← bundle execute + fixture + PR strategy
│   ├── 06-strangler-fig/   ← routing, flags, fallback, canary
│   ├── 07-verify/          ← 10 parallel verify dimensions
│   ├── 08-api-diff/        ← harness, equivalence, runner
│   ├── 09-decommission/    ← traffic-verify → safe-removal
│   └── _shared/            ← context budget, commit conventions, handoff format
└── templates/              ← working configs and code (not pseudo)
```

---

## Installation

### As a Claude Code skill (recommended)

```bash
mkdir -p .claude/skills/migration-v2
cp -R migration-artifacts-2/* .claude/skills/migration-v2/
```

Then invoke from Claude Code:

```
/migration-v2
```

Claude reads `SKILL.md`, collects parameters, writes `migration-state.json`, and begins Phase 0.

### As reference docs (manual orchestration)

Just keep the folder anywhere in your repo and dispatch sub-agents manually. Every sub-agent file is a self-contained prompt — paste it into Claude Code with `{{PLACEHOLDERS}}` filled in.

---

## Usage Guide

This is the operational runbook. Follow each step in order for a clean migration. Time estimates assume a 4M LOC monolith with 5–15 domains and a team of 4–10 engineers.

---

### Step 0: Prerequisites

Before starting, you need:

| Item | Why | How to check |
|---|---|---|
| Legacy app source tree (read-only) | Discovery scans | `ls $LEGACY_PATH` |
| Empty target directory for new code | Execute output | `mkdir -p $OUTPUT_PATH` |
| Git access to legacy repo | Git-log mining | `git -C $LEGACY_PATH log --oneline | head` |
| Production traffic capture capability | API-diff phase | depends — shadow logging, replay tool, or HAR exports |
| Feature flag service (or willingness to adopt one) | Strangler-fig phase | LaunchDarkly, Unleash, Statsig, Flagsmith all supported |
| API gateway / reverse proxy | Strangler-fig phase | nginx, ALB, Cloudflare Worker — templates included |
| Observability stack | Verify phase | metrics + logs + traces; the canary SLO gates won't work without them |
| Tech stack decisions made | Design phase | language, framework, db, auth, deploy — locked in before starting |
| A tech lead, a domain expert per domain, an SRE, a security reviewer | Phase gates | named humans, not "TBD" |

Estimated calendar time: **1–2 weeks** to line up these prerequisites for a real 4M LOC migration.

---

### Step 1: Initialize migration-state.json

The state file is the source of truth. Every sub-agent reads it on start and writes to it on completion.

Create the initial file at the repo root:

```bash
cat > migration-state.json <<'EOF'
{
  "schema_version": "1.0",
  "legacy_path": "/repo/legacy-monolith",
  "output_path": "/repo/new-services",
  "tech_stack": {
    "language": "TypeScript",
    "runtime": "Node 20",
    "framework": "Next.js 14",
    "database": "PostgreSQL + Prisma",
    "auth": "NextAuth v5",
    "deploy": "Vercel + AWS RDS"
  },
  "phases_complete": [],
  "domains": [],
  "shared_kernel": [],
  "contracts": [],
  "risks": [],
  "rollback_history": [],
  "concurrency_cap": 4
}
EOF
```

Validate against schema:

```bash
# Using ajv or any JSON Schema validator
npx ajv validate -s migration-artifacts-2/coordinator/migration-state.schema.json -d migration-state.json
```

Commit:

```bash
git add migration-state.json
git commit -m "chore: initialize migration state"
```

---

### Step 2: Phase 0 — Discovery

Goal: produce a complete, evidence-based feature inventory before writing any spec.

#### 2.1 — List modules to scan

Identify top-level modules in the legacy app. For each module, you'll dispatch one set of scanners.

```bash
ls -d $LEGACY_PATH/src/*/ | xargs -n1 basename
# Example output: auth billing catalog notifications orders search users
```

#### 2.2 — Dispatch per-module scanners (parallel, bounded)

For each module, dispatch the 5 per-module scanners. Cap parallelism at 4 concurrent agents (the schema's `concurrency_cap` controls this).

For Claude Code users, the dispatch pattern is:

```
Dispatch a sub-agent using migration-artifacts-2/sub-agents/00-discovery/code-map-scan.md
with {{LEGACY_PATH}}=/repo/legacy-monolith and {{MODULE}}=auth
```

Repeat for `api-routes-scan.md`, `db-schema-scan.md`, `test-spec-scan.md`, `git-log-mining.md`.

Each scanner writes to `discovery/modules/{{MODULE}}/` so outputs do not collide.

#### 2.3 — Dispatch global scanners

These run once, not per-module:

- `ui-screen-crawl.md` — Playwright crawl of every route (requires running legacy app)
- `dependency-graph.md` — module-level import graph (uses madge/depcruise/pydeps)

#### 2.4 — Synthesize

After all per-module scanners finish, run:

```
Dispatch migration-artifacts-2/sub-agents/00-discovery/discovery-synthesis.md
```

This produces `discovery/SUMMARY.md` — the top-level rollup. It operates on per-module summaries only (not raw scan data) so it stays inside context budget.

#### 2.5 — Gate

Phase 0 is complete when:
- `discovery/modules/{{MODULE}}/` exists for every module
- `discovery/SUMMARY.md` exists
- `discovery/dependency-graph.json` exists
- `migration-state.json` → `phases_complete` contains `"discovery"`

**Mandatory human review gate:** a domain expert (someone who worked on the legacy app) must sign off on `discovery/SUMMARY.md` before proceeding. Add their sign-off as a commit.

**Estimated calendar time:** 4–8 weeks for 4M LOC.

---

### Step 3: Phase 0.5 — Decompose

Goal: divide the system into independently migratable domains.

#### 3.1 — Domain decomposition

```
Dispatch migration-artifacts-2/sub-agents/01-decompose/domain-decompose.md
```

Reads `discovery/SUMMARY.md` + `dependency-graph.json`. Produces `domains/_index.md` and `domains/{{DOMAIN}}/charter.md` per detected domain.

For a 4M LOC monolith, expect **5–15 domains**.

#### 3.2 — Shared kernel inventory

```
Dispatch migration-artifacts-2/sub-agents/01-decompose/shared-kernel-inventory.md
```

Lists code referenced by multiple domains and recommends one of: **extract** to shared library, **duplicate** per domain, **split** by responsibility. This is the single highest-leverage decomposition decision.

#### 3.3 — Contract registry

```
Dispatch migration-artifacts-2/sub-agents/01-decompose/contract-registry.md
```

Produces `domains/_contracts.yaml` with inbound/outbound contracts per domain, version, SLA, deprecation_date.

#### 3.4 — Team ownership

```
Dispatch migration-artifacts-2/sub-agents/01-decompose/team-ownership-map.md
```

Maps domains to teams. Generates a `CODEOWNERS` file ready to drop into `.github/`.

#### 3.5 — Migration order

```
Dispatch migration-artifacts-2/sub-agents/01-decompose/migration-order.md
```

Topological sort + risk weighting. Outputs `domains/_migration-order.md`. Each domain gets a wave number (parallel groups).

#### 3.6 — Gate

- `domains/_index.md`, `_shared-kernel.md`, `_contracts.yaml`, `_codeowners.md`, `_migration-order.md` all exist
- `migration-state.json` → `domains[]` populated with `{name, status: "pending", dependencies: [...], wave: N}`
- `phases_complete` contains `"decompose"`
- **Human gate:** tech lead + product approve domain boundaries

**Estimated calendar time:** 2–4 weeks.

---

### Step 4: Per-domain SDS cycle (phases 1–5)

Now, **for each domain in `_migration-order.md`**, run the SDS cycle. Domains in the same wave run in parallel.

#### 4.1 — Spec (Phase 1)

```
Dispatch migration-artifacts-2/sub-agents/02-spec/domain-spec.md
with {{DOMAIN}}=auth
```

If the domain is over 200K LOC, the spec agent will recommend splitting into features. In that case, run `feature-spec.md` once per feature.

**Output:** `domains/auth/spec.md` (or `domains/auth/features/sso/spec.md`)

#### 4.2 — Design (Phase 2)

Three sub-agents run in sequence:

```
1. domain-design.md     → domains/auth/design.md
2. contract-design.md   → domains/auth/contracts.openapi.yaml (per inbound contract)
3. data-migration-design.md → domains/auth/data-migration.md (schema diff, backfill, dual-write, cutover)
```

#### 4.3 — Tasks (Phase 3)

```
1. domain-tasks.md           → domains/auth/tasks.md + bundle-*.md
2. critical-path-analysis.md → domains/auth/critical-path.md
```

#### 4.4 — Execute (Phase 4)

For each bundle in `tasks.md`, dispatch:

```
Dispatch migration-artifacts-2/sub-agents/05-execute/bundle-execute.md
with {{DOMAIN}}=auth, {{BUNDLE}}=1, {{OUTPUT_PATH}}=/repo/new-services
```

Rules baked into the agent:
- One bundle = one PR
- PR targets `migration/auth` integration branch (not main)
- Commits use `feat(auth)[BUNDLE-N]: ...`
- Never commit `.env`
- Auto-fix TypeScript / compile errors before completion

Run `fixture-migration.md` once per domain to bring over seed data and test fixtures.

#### 4.5 — Verify (Phase 5 / Phase 7 in v2 numbering)

See [Step 6](#step-6-phase-7--verify-10-dimensions) — verify is broken out as its own step because it runs 10 parallel dimensions.

#### 4.6 — Per-domain gate

A domain is "ready for strangler-fig" when:
- `spec.md`, `design.md`, `tasks.md`, all bundles executed, all tests pass
- `migration-state.json` → `domains[name].status = "verified"`
- All 10 verify dimensions pass (or have documented waivers)

**Estimated calendar time per domain:** 6–12 weeks for a 500K LOC domain.

---

### Step 5: Phase 6 — Strangler-Fig rollout

Goal: route real traffic incrementally from legacy to new. **Per domain, after that domain is verified.**

#### 5.1 — Generate routing config

```
Dispatch migration-artifacts-2/sub-agents/06-strangler-fig/routing-config.md
with {{DOMAIN}}=auth, {{RAMP_PERCENT}}=1
```

Pick one of the three template flavors based on your infra:
- `templates/strangler-config-nginx.conf` — nginx upstream with `split_clients`
- `templates/strangler-config-alb.tf` — AWS ALB weighted target groups
- `templates/strangler-config-cloudflare-worker.js` — CF Worker with JWT-based sticky bucketing

#### 5.2 — Wire feature flags

```
Dispatch migration-artifacts-2/sub-agents/06-strangler-fig/feature-flag-wiring.md
```

Generates the kill-switch flag (`auth.migration.enabled`) and per-endpoint sub-flags. Wires both server-side (gateway) and client-side gates.

#### 5.3 — Add fallback middleware

```
Dispatch migration-artifacts-2/sub-agents/06-strangler-fig/fallback-logic.md
```

Generates a circuit-breaker middleware: if the new service returns 5xx or times out, fall back to legacy. Configurable error budget per endpoint.

#### 5.4 — Canary schedule

```
Dispatch migration-artifacts-2/sub-agents/06-strangler-fig/canary-rollout.md
```

Generates `domains/auth/canary-schedule.yaml`:

```yaml
schedule:
  - week: 1, ramp: 1,   gates: { error_rate_max: 0.1, p95_latency_max_delta: 10ms }
  - week: 2, ramp: 10,  gates: { ... }
  - week: 4, ramp: 50,  gates: { ... }
  - week: 6, ramp: 99,  gates: { ... }
  - week: 8, ramp: 100, gates: { ... }
auto_rollback_triggers:
  - error_rate > 1.0
  - p99_latency_delta > 100ms
  - pager_alert_fired
```

#### 5.5 — Per-week operation

Each week:
1. Update `ramp_percent` in `migration-state.json` to the scheduled value
2. Re-run `routing-config.md` to regenerate gateway config
3. Apply the new config (gateway-specific)
4. Monitor for the week
5. If gates pass → advance; if breached → auto-rollback fires

#### 5.6 — Gate

Strangler-fig is "done" for a domain when `ramp_percent = 100` and gates have held for 7+ days.

**Estimated calendar time per domain:** 6–10 weeks.

---

### Step 6: Phase 7 — Verify (10 dimensions)

Run **all 10 dimensions in parallel** after Phase 4 (execute) and before / during Phase 6 (strangler-fig ramp).

```
Dispatch in parallel:
- sub-agents/07-verify/traceability.md     (FR → step → commit chain)
- sub-agents/07-verify/completeness.md     (all contracts implemented)
- sub-agents/07-verify/code-quality.md     (smells, dead code, complexity)
- sub-agents/07-verify/test-quality.md     (state machines, ownership, edge cases)
- sub-agents/07-verify/regression.md       (tests pass, build green, types clean)
- sub-agents/07-verify/security.md         (.env, 403/404, secrets, injection)
- sub-agents/07-verify/performance.md      (k6/locust vs baseline, ≤10% regression)
- sub-agents/07-verify/observability.md    (structured logs, traces, metrics, dashboards)
- sub-agents/07-verify/compliance.md       (GDPR/SOC2/HIPAA/PCI controls matrix)
- sub-agents/07-verify/data-parity.md      (row-level diff legacy vs new)
```

Each produces `domains/{{DOMAIN}}/verify-{{DIMENSION}}.md`. A synthesis step combines into `verify-report.md`.

**Gate:** CRITICAL findings must be fixed or waived (with named approver) before strangler-fig ramp can advance past 1%.

---

### Step 7: Phase 8 — API diff

Goal: prove behavioral parity between legacy and new system before going past 50% ramp.

#### 7.1 — Set up harness

```
Dispatch migration-artifacts-2/sub-agents/08-api-diff/harness-setup.md
```

Uses `templates/api-diff-harness.ts` (≈200 LOC, runnable). It:
1. Reads recorded traffic from `traffic/recorded.jsonl`
2. Replays each request against both legacy and new endpoints
3. Captures both responses
4. Calls the diff runner

#### 7.2 — Configure semantic equivalence

```
Dispatch migration-artifacts-2/sub-agents/08-api-diff/semantic-equivalence.md
```

Generates `api-diff/equivalence.yaml`:

```yaml
ignore_fields:
  - "$..timestamp"
  - "$..request_id"
  - "$..created_at"
  - "$..updated_at"
ignore_ordering:
  - "$.users[*]"
  - "$.orders[*].items"
treat_as_equivalent:
  - { from: "null", to: "[]" }
  - { from: "missing", to: "false" }
```

#### 7.3 — Run the diff

```
Dispatch migration-artifacts-2/sub-agents/08-api-diff/diff-runner.md
```

Produces `api-diff/report.md`:
- Per-endpoint pass/fail counts
- 5 sample diffs per category (body-diff, status-diff, error)
- Verdict: `RAMP_ADVANCE_OK` | `RAMP_HOLD` | `RAMP_ROLLBACK`

**Gate:** before advancing ramp past 50%, body-diff rate must be <0.5% and status-diff rate must be 0%.

---

### Step 8: Phase 9 — Decommission

Goal: safely remove legacy code after 100% traffic on new system. Four gates, each one a separate PR.

#### 8.1 — Traffic verify (7-day soak)

```
Dispatch migration-artifacts-2/sub-agents/09-decommission/traffic-verify.md
```

Reads gateway logs. Must show **zero hits** to legacy endpoints for the domain over 7 consecutive days.

#### 8.2 — Dependency check

```
Dispatch migration-artifacts-2/sub-agents/09-decommission/dependency-check.md
```

Greps remaining codebase for any imports/calls to legacy domain code. Must be zero.

#### 8.3 — Data archival

```
Dispatch migration-artifacts-2/sub-agents/09-decommission/data-archival.md
```

Snapshots legacy DB tables to cold storage (S3 Glacier / equivalent), then disconnects writes. Reads are kept available read-only for 30 days.

#### 8.4 — Safe removal (3 stages, 30-day soak between)

```
Dispatch migration-artifacts-2/sub-agents/09-decommission/safe-removal.md
```

Generates 3 PRs:
1. **Disable** — feature flag forced off, legacy code remains but unreachable. 30-day soak.
2. **Soft delete** — move legacy code to `/archive` directory. 30-day soak.
3. **Hard delete** — `git rm` legacy code. Final.

Each PR includes its own rollback instructions.

#### 8.5 — Gate

Domain is "decommissioned" when all 3 stages complete and no rollback was triggered.

**Estimated calendar time per domain:** 3–4 months (mostly soak time).

---

## Parameters reference

| Param | Description | Example |
|-------|-------------|---------|
| `{{LEGACY_PATH}}` | Absolute path to legacy monolith | `/repo/legacy-monolith` |
| `{{OUTPUT_PATH}}` | Absolute path for new app(s) | `/repo/new-services` |
| `{{MODULE}}` | A subdirectory of legacy (for per-module scans) | `src/billing` |
| `{{DOMAIN}}` | Bounded domain name | `auth`, `orders`, `catalog` |
| `{{FEATURE}}` | Sub-domain feature (large domains only) | `auth/sso`, `orders/returns` |
| `{{BUNDLE}}` | Execute-phase bundle number | `1`, `2`, `3` |
| `{{TECH_STACK}}` | Target stack (JSON) | see `workflow.md` §6 |
| `{{RAMP_PERCENT}}` | Strangler-fig traffic ramp | `1`, `10`, `50`, `100` |
| `{{TIMEFRAME}}` | Git-log mining window | `last-6-months`, `2024-Q1` |

---

## Daily workflow rhythm

A typical day during the per-domain SDS cycle:

| Time | Activity |
|---|---|
| **Standup (15 min)** | Read `coordinator/progress-dashboard.md`. Identify blocked domains. |
| **Morning (3 hr)** | Dispatch next batch of sub-agents per scheduler output. Review yesterday's outputs. |
| **Mid-day** | Wait for execute / verify agents to complete (they take 10–60 min each). Use the time for human-review tasks. |
| **Afternoon (3 hr)** | Code review on PRs landing in `migration/{{DOMAIN}}` integration branches. |
| **End of day** | Update `migration-state.json` — any blockers, risks, rollbacks. Commit. |

During strangler-fig phase, swap "dispatch agents" for "monitor SLOs and approve ramp advances."

---

## Onboarding a new contributor

A new contributor joining mid-migration should:

1. Read this README end-to-end (30 min).
2. Read `workflow.md` for timeline and roles (15 min).
3. Read `migration-state.json` to see current state (5 min).
4. Read `coordinator/progress-dashboard.md` to see current status (5 min).
5. Read the charter of the domain they'll work on: `domains/{{DOMAIN}}/charter.md` (10 min).
6. Pair on dispatching one sub-agent before working solo (1 hr).

Total ramp time: about half a day. The state file + dashboard + per-domain charter give them everything they need.

---

## Troubleshooting / FAQ

**Q: A sub-agent failed mid-phase. Now what?**
A: Re-dispatch the same sub-agent. It reads `migration-state.json` on start, so it resumes from where the previous run left off. If the failure was due to context overflow, narrow the scope (`{{MODULE}}` to a smaller subdirectory).

**Q: Two domains have the same shared kernel file. Who owns it?**
A: This is what `shared-kernel-inventory.md` is for. Run it; it produces a decision: extract → library, duplicate → per-domain copies, or split → break the file by responsibility.

**Q: We hit a regression in production after a ramp step.**
A: The canary schedule has auto-rollback triggers. They fire on SLO breach. If they didn't fire but you saw the regression manually, set ramp_percent back to the last known-good value, regenerate routing config, re-apply. Then log the incident in `rollback_history`.

**Q: Our team is smaller than the workflow assumes (1–2 engineers).**
A: Use **v2 light**: skip phases 06 (strangler-fig — replace with big-bang cutover behind a single flag), 08 (API-diff — replace with manual smoke test), and 09 (decommission — replace with "delete after 30 days"). This works up to ~1M LOC.

**Q: We don't have a feature flag service.**
A: You need one. Cheapest path: Unleash (open source, self-hosted, no per-seat fee). The flag-wiring agent generates client code for it.

**Q: Can we skip the API-diff phase?**
A: Only if you have no production traffic to capture (e.g., greenfield API). Otherwise, no — static analysis can't catch behavioral drift in a 4M LOC migration.

**Q: How do we handle database migrations during strangler-fig?**
A: `data-migration-design.md` defines a **dual-write window**: legacy writes go to both old and new DB, reads can come from either. After the new DB is verified at parity, reads flip to new, then writes flip, then old DB enters archival.

**Q: What if a domain expert refuses to sign off on the discovery summary?**
A: They're catching a real risk. Pause Phase 0.5 and address their concerns. The whole point of Phase 0 + expert review is to find missing features *before* spec work, not during execution.

**Q: How long does a 4M LOC migration take, realistically?**
A: 12–18 months end-to-end for a team of 6–10. Discovery 1–2 months, decompose 2–3 weeks, per-domain SDS 2–3 months × N domains (parallelized), strangler-fig ramp 2–3 months, decommission soak 3–4 months. See `workflow.md` for detailed timelines.

---

## See also

- [`CHANGELOG-vs-v1.md`](./CHANGELOG-vs-v1.md) — what's new vs v1 and why
- [`workflow.md`](./workflow.md) — full runbook, 3/12/24-month timelines, 4M LOC e-commerce example
- [`SKILL.md`](./SKILL.md) — Claude Code skill spec
- [`coordinator/scheduler.md`](./coordinator/scheduler.md) — how parallelism is bounded
- [`coordinator/migration-state.schema.json`](./coordinator/migration-state.schema.json) — canonical state schema
- [`sub-agents/_shared/context-budget-rules.md`](./sub-agents/_shared/context-budget-rules.md) — rules every agent follows
- [`REVIEW-REPORT.md`](./REVIEW-REPORT.md) — independence audit
