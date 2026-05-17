# Migration Artifacts v2 — Large-App Edition

Toolkit for migrating **large legacy applications (100K–5M+ LOC)** to a modern stack using a parallelized, state-driven, strangler-fig variant of the SDS methodology.

v2 exists because v1 silently breaks at scale. See [`CHANGELOG-vs-v1.md`](./CHANGELOG-vs-v1.md) for the 20 capabilities v1 cannot deliver.

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

## What's New (vs v1)

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

## Folder Structure

```
migration-artifacts-2/
├── README.md               ← this file
├── SKILL.md                ← Claude Code skill orchestrating the 10-phase pipeline
├── workflow.md             ← runbook with LOC→strategy matrix and example timelines
├── CHANGELOG-vs-v1.md      ← 20 capability gaps v2 closes
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

## Quick Start

### Option A — Skill

```bash
mkdir -p .claude/skills/migration-v2
cp migration-artifacts-2/SKILL.md .claude/skills/migration-v2/SKILL.md
```

In Claude Code: `/migration-v2`. Claude will collect parameters, write `migration-state.json`, and begin Phase 0.

### Option B — Manual

Read `workflow.md` for the runbook. Run sub-agents in the order listed in `SKILL.md`. Every sub-agent file is a self-contained prompt; replace `{{PLACEHOLDERS}}` and paste.

---

## Parameters

| Param | Description | Example |
|-------|-------------|---------|
| `{{LEGACY_PATH}}` | Absolute path to legacy monolith | `/repo/legacy-monolith` |
| `{{OUTPUT_PATH}}` | Absolute path for new app(s) | `/repo/new-services` |
| `{{MODULE}}` | A subdirectory of legacy (for per-module scans) | `src/billing` |
| `{{DOMAIN}}` | Bounded domain name | `auth`, `orders`, `catalog` |
| `{{FEATURE}}` | Sub-domain feature (large domains only) | `auth/sso`, `orders/returns` |
| `{{TECH_STACK}}` | Target stack (JSON) | see `workflow.md` §6 |
| `{{RAMP_PERCENT}}` | Strangler-fig traffic ramp | `1`, `10`, `50`, `100` |

---

## Phase Gates

Every phase has a gate that requires BOTH:
1. The required output files exist.
2. `migration-state.json` has been updated to reflect phase completion.

The scheduler will refuse to dispatch next-phase agents until both are true.

---

## See Also

- `CHANGELOG-vs-v1.md` — what's new and why
- `workflow.md` — full runbook, timelines, roles
- `coordinator/scheduler.md` — how parallelism is bounded
- `sub-agents/_shared/context-budget-rules.md` — rules every agent follows
