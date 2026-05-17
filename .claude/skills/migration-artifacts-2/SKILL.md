---
name: migration-artifacts-2
description: Large-app (100K–5M+ LOC) SDS migration orchestration. 10-phase pipeline with persistent state, parallel multi-domain execution, sub-domain decomposition, strangler-fig automation, API diff harness, canary rollout, decommission. Invoke with /migration-v2.
---

# Migration Orchestration Skill (v2 — Large App)

You are orchestrating an **SDS migration of a large legacy application** (100K–5M+ LOC). Follow the 10-phase pipeline. Every phase gate requires (1) output files exist AND (2) `migration-state.json` has been updated. Never skip phases. Never silently proceed when a gate fails.

This skill differs from v1 in five fundamental ways:
- **Per-module operation**: scanners are bounded to one module at a time (max ~50K LOC).
- **State-driven**: every sub-agent reads and writes `migration-state.json`.
- **Concurrency-aware**: a scheduler computes which agents to dispatch and respects concurrency caps.
- **Strangler-fig native**: a dedicated phase produces routing configs, feature-flag wiring, fallback middleware, canary schedules.
- **Domain-expert gates**: mandatory human review between phases. Surface decisions; do not proceed silently.

---

## Pre-Made Decisions

Collect these at invocation time. Write them into `migration-state.json` under `parameters`.

```
LEGACY_PATH:        absolute path to legacy monolith
OUTPUT_PATH:        absolute path for new app(s)
APP_SIZE_LOC:       approximate LOC (drives strategy — see workflow.md §1)
TECH_STACK:         target stack JSON (see workflow.md §6)
TIMELINE_MONTHS:    expected duration (drives parallelism caps)
TEAM_SIZE:          number of engineers across all domains
DOMAINS:            "auto" to derive via 01-decompose, or explicit list
FEATURE_FLAG_SYS:   LaunchDarkly | Unleash | Statsig | custom
ROUTING_LAYER:      nginx | alb | cloudflare-worker | envoy
COMPLIANCE_SCOPE:   none | gdpr | soc2 | hipaa | pci | multiple (drives 07-verify/compliance)
```

If unknown, ask the user. Do not invent defaults for COMPLIANCE_SCOPE — it changes verify rules materially.

---

## Concurrency Model

| Phase | Max parallel agents | Rationale |
|-------|---------------------|-----------|
| 00 Discovery | 8 | scanners are read-only, independent |
| 01 Decompose | 1 | serial reasoning over discovery output |
| 02 Spec | N domains | independent per domain |
| 03 Design | N domains | independent per domain |
| 04 Tasks | N domains | independent per domain |
| 05 Execute | **4** | git lock contention; PRs must serialize per integration branch |
| 06 Strangler-fig | N domains | config generation is independent |
| 07 Verify | 10 dims × N domains | dimensions independent; cap at 20 concurrent total |
| 08 API-Diff | N domains | independent harness runs |
| 09 Decommission | 1 per domain, serial across domains | safety: one decommission at a time |

The scheduler sub-agent (`coordinator/scheduler.md`) enforces these caps.

---

## Phase 00 — Discovery

For each top-level module of `LEGACY_PATH`, dispatch in parallel (cap=8):
- `sub-agents/00-discovery/code-map-scan.md` with `{{MODULE}}`
- `sub-agents/00-discovery/api-routes-scan.md` with `{{MODULE}}`
- `sub-agents/00-discovery/test-spec-scan.md` with `{{MODULE}}`

For DB schemas, dispatch by schema prefix:
- `sub-agents/00-discovery/db-schema-scan.md` with `{{PREFIX}}`

Once per project:
- `sub-agents/00-discovery/git-log-mining.md` with `{{TIMEFRAME}}`
- `sub-agents/00-discovery/ui-screen-crawl.md`
- `sub-agents/00-discovery/dependency-graph.md`

After all complete:
- `sub-agents/00-discovery/discovery-synthesis.md` (rolls up summaries)

**Gate**: `discovery/SUMMARY.md` exists AND `migration-state.json.phases_complete` contains `"discovery"`.

---

## Phase 01 — Decompose

Dispatch serially:
1. `sub-agents/01-decompose/domain-decompose.md`
2. `sub-agents/01-decompose/shared-kernel-inventory.md`
3. `sub-agents/01-decompose/contract-registry.md`
4. `sub-agents/01-decompose/team-ownership-map.md`
5. `sub-agents/01-decompose/migration-order.md`

**Gate**: `domains/_index.md`, `domains/_shared-kernel.md`, `domains/_contracts.yaml`, `domains/_codeowners.md`, `domains/_migration-order.md` all exist. State has `"decompose"` complete. **Domain expert review required.**

---

## Phase 02 — Spec (per domain, parallel)

For each domain, dispatch `sub-agents/02-spec/domain-spec.md`.

If a domain's LOC exceeds 200K (as recorded in `domains/{{DOMAIN}}/charter.md`), `domain-spec.md` will instead emit a directive to run `sub-agents/02-spec/feature-spec.md` per feature. The scheduler picks these up on the next tick.

**Gate per domain**: `domains/{{DOMAIN}}/spec.md` exists OR (`domains/{{DOMAIN}}/features/*/spec.md` exist for all features).

---

## Phase 03 — Design (per domain, parallel)

For each domain:
1. `sub-agents/03-design/domain-design.md`
2. `sub-agents/03-design/contract-design.md`
3. `sub-agents/03-design/data-migration-design.md`

**Gate per domain**: all three files in `domains/{{DOMAIN}}/`.

---

## Phase 04 — Tasks (per domain, parallel)

For each domain:
1. `sub-agents/04-tasks/domain-tasks.md`
2. `sub-agents/04-tasks/critical-path-analysis.md`

**Gate per domain**: `domains/{{DOMAIN}}/tasks.md` + `domains/{{DOMAIN}}/critical-path.md` + at least one bundle file.

---

## Phase 05 — Execute (per domain, cap=4)

For each domain (respecting dependencies in `domains/_migration-order.md`):
- `sub-agents/05-execute/bundle-execute.md` per bundle, serial within domain
- `sub-agents/05-execute/fixture-migration.md` once per domain
- `sub-agents/05-execute/pr-strategy.md` once at start (writes branching policy)

**Gate per domain**: all bundles merged to `migration/{{DOMAIN}}` branch, CI green.

---

## Phase 06 — Strangler-Fig (per domain, parallel)

For each domain:
1. `sub-agents/06-strangler-fig/routing-config.md` (uses `ROUTING_LAYER`)
2. `sub-agents/06-strangler-fig/feature-flag-wiring.md` (uses `FEATURE_FLAG_SYS`)
3. `sub-agents/06-strangler-fig/fallback-logic.md`
4. `sub-agents/06-strangler-fig/canary-rollout.md`

**Gate per domain**: routing config + flag config + fallback middleware + canary schedule exist in `domains/{{DOMAIN}}/strangler/`.

---

## Phase 07 — Verify (per domain, 10 dimensions parallel)

For each domain, dispatch all 10 dimensions in parallel (cap=20 total across all domains):
- traceability, completeness, code-quality, test-quality, regression, security, performance, observability, compliance, data-parity

Then synthesize per domain into `domains/{{DOMAIN}}/verify-report.md`.

**Gate per domain**: zero CRITICAL findings open.

---

## Phase 08 — API-Diff (per domain, parallel)

For each domain:
1. `sub-agents/08-api-diff/harness-setup.md`
2. `sub-agents/08-api-diff/semantic-equivalence.md`
3. `sub-agents/08-api-diff/diff-runner.md`

Run continuously at every canary ramp step. Diff report must show <0.1% unexplained diffs before advancing ramp.

**Gate per domain**: `domains/{{DOMAIN}}/api-diff-report.md` shows pass at current ramp.

---

## Phase 09 — Decommission (per domain, serial across domains)

Only run after `ramp_percent = 100` and stable for 7+ days.

1. `sub-agents/09-decommission/traffic-verify.md`
2. `sub-agents/09-decommission/dependency-check.md`
3. `sub-agents/09-decommission/data-archival.md`
4. `sub-agents/09-decommission/safe-removal.md`

**Gate per domain**: `migration-state.json.domains[{{DOMAIN}}].status = "decommissioned"`.

---

## State File Management

Every sub-agent **must**:
- Read `migration-state.json` at start. Fail if missing required preconditions.
- Write back updates atomically (read → modify → write to `.tmp` → rename).
- Append to `rollback_history` on any destructive change.

Schema: `coordinator/migration-state.schema.json`. Validate after every write.

---

## Scheduler Loop

Between phases (and on resume), invoke `coordinator/scheduler.md`. It will:
1. Read state.
2. Determine next dispatchable sub-agents respecting deps and caps.
3. Output `state/next-actions.md`.

You (the orchestrator) then dispatch those agents in parallel and loop.

---

## Mandatory Human Gates

These phases **require human review** before next phase begins. Surface decisions; do not proceed:

- After 01-decompose: domain expert confirms domain boundaries.
- After 03-design contracts: API owner approves contracts.
- Before 06-strangler-fig: SRE approves routing config.
- Before each canary ramp: SRE approves SLO baseline.
- Before 09-decommission: tech lead + product approve removal.

---

## Error Handling

- Sub-agent fails to write output: retry once with explicit "ensure file written" instruction.
- State file conflict (concurrent write): scheduler serializes; never edit state mid-flight.
- Verify CRITICAL finding: block phase; do not advance ramp; surface to user.
- Canary SLO breach: trigger automatic rollback per `canary-schedule.yaml`; mark `domains[].status = "rolled_back"` and append to `rollback_history`.

---

## Skill Entry Point

When user invokes `/migration-v2`:
1. Initialize `migration-state.json` from `coordinator/migration-state.schema.json` defaults.
2. Collect all Pre-Made Decisions.
3. Persist to state.
4. Dispatch Phase 00.
5. After each phase, invoke `coordinator/scheduler.md` to compute next actions.
6. Loop until `domains[].status` is `decommissioned` for all migration-target domains.
