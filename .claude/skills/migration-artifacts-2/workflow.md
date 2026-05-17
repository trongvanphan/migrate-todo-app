# Migration Workflow Runbook (v2)

Runbook for migrations of any size — single-domain SPA through multi-million-LOC monolith. Pair with `SKILL.md` (machine instructions), `references/sds-delegation.md` (per-phase sds invocations), and `coordinator/scheduler.md` (dispatch logic).

---

## Table of Contents

1. [LOC → strategy matrix](#1-loc--strategy-matrix)
2. [Timeline templates](#2-timeline-templates)
3. [Parallelism limits](#3-parallelism-limits)
4. [Required roles](#4-required-roles)
5. [Step-by-step example: 4M LOC e-commerce monolith](#5-example-4m-loc-e-commerce)
6. [Adapting TECH_STACK](#6-adapting-tech_stack)
7. [Operating tips at scale](#7-operating-tips-at-scale)

---

## 1. LOC → Strategy Matrix

| LOC | Domains | Phases to run | Recommended duration | Team size |
|-----|---------|---------------|----------------------|-----------|
| <10K | 1 | All sds-delegated phases (02–05, 07). Discovery collapses to one pass. Skip 06/08/09 when `LIVE_TRAFFIC=false`. | hours – 1 week | 1 |
| 10K–100K | 1–3 | sds-delegated phases per domain. Per-module discovery only when 4+ top-level source dirs. Skip 06/08/09 unless live traffic. | 1–8 weeks | 1–3 |
| 100K–1M | 3–8 | Full pipeline (06/08/09 if live traffic). | 3–6 months | 3–10 |
| 1M–5M | 5–15 | Full pipeline. | 12–24 months | 10–40 |
| >5M | 10+ | Full pipeline + sub-domain split: for domains where one `/sds.spec` session would carry >20 FRs, write a per-feature briefing and invoke `/sds.spec` per feature. | 24–36 months | 40+ |

**Decision rule**: same pipeline regardless of size. The cells above describe what fans out and how long it takes, not whether to invoke the skill.

---

## 2. Timeline Templates

### 3-Month Variant (≈300K LOC, 4 domains, parallel team)

```
Month 1
  W1: Phase 00 Discovery (per-module scans, parallel)
  W2: Phase 01 Decompose + domain-expert gate
  W3-4: Phase 02 Spec + 03 Design (parallel per domain)
Month 2
  W5: Phase 04 Tasks
  W6-8: Phase 05 Execute (parallel per domain, cap=4)
Month 3
  W9: Phase 06 Strangler-fig setup
  W10: Phase 07 Verify (10 dims, parallel)
  W11: Phase 08 API-diff + canary ramp 1%→10%→50%
  W12: Ramp 100% + Phase 09 Decommission first leaf domain
```

### 12-Month Variant (≈1.5M LOC, 8 domains)

```
M1-2: Discovery + Decompose (8 domain charters approved)
M3:   Spec all domains (parallel)
M4:   Design all domains (parallel)
M5:   Tasks all domains
M6-9: Execute (4 in parallel at a time, dependency-ordered)
M10:  Strangler-fig + Verify (all domains)
M11:  API-diff + canary ramps (staggered: leaf domains first)
M12:  Decommission (serial, one domain per week)
```

### 24-Month Variant (≈4M LOC, 12 domains, sub-domain decomp)

```
M1-3:   Discovery (per-module, ~50 modules) + Decompose
M4-6:   Spec (sub-domain: ~80 features) + Design
M7-9:   Tasks + start Execute on leaf domains
M10-18: Execute (rolling waves of 4 domains in parallel)
M14-20: Strangler-fig + Verify (overlapping with execute on later domains)
M16-22: Canary ramps per domain (each takes 4-8 weeks)
M20-24: Decommission (serial, with 30-day soak between domains)
```

---

## 3. Parallelism Limits

The scheduler enforces these. Violating them causes git lock contention, state-file races, and CI thrashing.

| Resource | Cap | Why |
|----------|-----|-----|
| Discovery scanners | 8 | network/disk IO bound on legacy repo |
| Spec / Design / Tasks agents | unbounded across domains | independent, read-mostly |
| Execute agents | **4** | each opens a branch + PR; git serializes |
| Verify dimensions | 20 total | CPU on test runners |
| Canary ramps simultaneously active | 3 | one bad ramp poisons SLO baseline; limit blast radius |
| Decommissions in flight | 1 | irreversible; one at a time |

If you have more domains than caps allow, run in waves.

---

## 4. Required Roles

| Role | Phase responsibilities | When critical |
|------|------------------------|---------------|
| Tech lead | Approve 01 decompose, 03 design | Phase gates |
| Domain expert(s) | Confirm boundaries, contracts | 01, 03 |
| SRE | Approve routing config, canary schedule, SLO baseline | 06, before each ramp |
| Security review | Sign off on 07 verify/security and 07 verify/compliance | Before 100% ramp |
| Data engineer | Approve 03 data-migration design, oversee 09 archival | 03, 09 |
| Product owner | Confirm feature coverage in spec, accept verify reports | 02, 07 |
| Per-domain owner | Owns one branch, one charter, one rollback runbook | 02 onward |

At 1M+ LOC, **a single tech lead cannot cover all domains**. Assign one domain owner per domain.

---

## 5. Example: 4M LOC e-commerce monolith → microservices

Stack: Java 8 Spring monolith + Oracle → Go microservices + Postgres + Kafka.

### Step 1 — Initialize state

```bash
cp migration-artifacts-2/coordinator/migration-state.schema.json migration-state.json
# edit parameters: LEGACY_PATH=/repo/monolith, OUTPUT_PATH=/repo/services,
#   APP_SIZE_LOC=4000000, ROUTING_LAYER=envoy, FEATURE_FLAG_SYS=launchdarkly,
#   COMPLIANCE_SCOPE=pci,soc2
```

### Step 2 — Discovery (Month 1–3)

Scanners run per-module. The monolith has ~60 top-level Java packages; scheduler dispatches in waves of 8.

Output per module: `discovery/modules/{module}/{code-map,api-routes,test-spec}.md`.
Output for DB: `discovery/schemas/{prefix}-schema.md` per schema prefix (e.g., `cust_*`, `ord_*`, `inv_*`).
Synthesis writes `discovery/SUMMARY.md` (≤2000 lines, summaries only).

**Domain-expert gate**: tech lead + 2 senior engineers review SUMMARY.md.

### Step 3 — Decompose (Month 3)

`01-decompose/domain-decompose.md` reads SUMMARY + dependency graph. Output: 12 domains.

```
auth, customers, catalog, search, cart, checkout, orders, payments,
returns, fulfillment, notifications, reporting
```

`shared-kernel-inventory.md` identifies ~80 files used by 3+ domains (pricing utils, money type, audit helpers). Decision per file: extract / duplicate / split.

`contract-registry.md` enumerates 240 inbound contracts across domains.

`migration-order.md` produces:
```
Wave 1: auth (foundational)
Wave 2: customers, catalog, search (depend only on auth)
Wave 3: cart, notifications (depend on customers, catalog)
Wave 4: checkout, orders, payments (depend on cart)
Wave 5: returns, fulfillment, reporting (depend on orders)
```

### Step 4 — Sub-domain split

`payments` is 800K LOC. `domain-spec.md` emits directive: run `feature-spec.md` for each of:
- `payments/card-processing`
- `payments/wallets`
- `payments/refunds`
- `payments/chargebacks`
- `payments/reconciliation`

Each feature gets its own spec, design, tasks, bundles.

### Step 5 — Per-domain SDS cycle (Months 4–18)

For each wave, scheduler dispatches spec→design→tasks in parallel. Execute respects cap=4. Each domain produces:
- `domains/{{DOMAIN}}/spec.md` (or `features/{{F}}/spec.md`)
- `domains/{{DOMAIN}}/design.md`, `contract-design.md`, `data-migration.md`
- `domains/{{DOMAIN}}/tasks.md` + `bundle-*.md`
- Working code at `OUTPUT_PATH/{{DOMAIN}}/`
- PRs onto `migration/{{DOMAIN}}` integration branch

### Step 6 — Strangler-fig (Months 14–20)

Per domain:
- `routing-config.md` generates Envoy weighted-cluster YAML
- `feature-flag-wiring.md` produces LaunchDarkly flag definitions + server/client gate code
- `fallback-logic.md` produces Go middleware with circuit breaker (gobreaker)
- `canary-rollout.md` produces `canary-schedule.yaml`: W1=1%, W2=10%, W3=25%, W4=50%, W5=100%

### Step 7 — Verify (continuous)

10 dimensions per domain. The compliance dimension for PCI checks tokenization paths, card-data masking in logs, audit trail completeness.

### Step 8 — API-Diff (continuous during ramp)

Record 1 hour of production traffic per endpoint. Replay through both stacks via `templates/api-diff-harness.ts` (port to Go for this app). Diff with semantic-equivalence rules: ignore timestamps, generated UUIDs, response field ordering.

Advance ramp only when unexplained diff rate <0.1%.

### Step 9 — Decommission (Months 20–24)

Per domain, serially:
1. Confirm 7 days at 100% with zero legacy traffic.
2. Grep legacy code for inbound calls; must be zero.
3. Snapshot legacy DB tables to S3 cold storage.
4. Soft-delete: move legacy code to `legacy/archive/{{DOMAIN}}/`. 30-day soak.
5. Hard-delete: PR removing `legacy/archive/{{DOMAIN}}/`. Tag release.

---

## 6. Adapting TECH_STACK

Declare a single `tech-stack.json` at the repo root (or pass via `{{TECH_STACK}}`) capturing the target platform. Large-app fields:

```json
{
  "language": "Go 1.22",
  "framework": "gRPC + chi router",
  "database": "PostgreSQL 16 (Aurora)",
  "messaging": "Kafka (Confluent)",
  "auth": "OIDC via Cognito",
  "observability": {
    "logs": "structured JSON to Loki",
    "metrics": "Prometheus + Grafana",
    "tracing": "OpenTelemetry → Tempo"
  },
  "routing": "Envoy",
  "feature_flags": "LaunchDarkly",
  "deployment": "Kubernetes (EKS) + Argo CD",
  "compliance": ["pci-dss-4", "soc2-type2"]
}
```

The `observability`, `routing`, `feature_flags`, `compliance` fields are required at scale — they drive the strangler-fig and verify phases.

---

## 7. Operating Tips at Scale

- **State file is the source of truth.** When in doubt, read `migration-state.json`. Never reason about migration progress from memory.
- **Resume = re-run scheduler.** After any pause (overnight, weekly), invoke `coordinator/scheduler.md`. It will compute exactly which agents to dispatch next.
- **Never edit state file by hand during execution.** Agents use atomic writes; a hand-edit during a write races and corrupts.
- **One bundle = one PR.** Never combine bundles in a single PR. Reviewers cannot review 2000-line PRs.
- **Branch hygiene**: `migration/{{DOMAIN}}` ← `migration/{{DOMAIN}}/bundle-N` ← feature branches. Rebase weekly.
- **Roll back fast.** A canary breach should auto-rollback in <60 seconds via feature flag. If your flag system takes longer, fix that before starting ramps.
- **Decommission is irreversible.** Two human approvals required: tech lead AND product owner. Both recorded in state.
- **Compliance review is not optional.** PCI, SOC2, HIPAA — the legal cost of a missed control vastly exceeds the time to run `07-verify/compliance.md`.
- **Domain-expert gates are not optional.** Without a human who knows the legacy app, you will ship a 90%-correct migration that misses the 10% that matters (often the most revenue-critical edge cases).
