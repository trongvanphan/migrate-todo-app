---
name: migration-artifacts-2
description: Large-app SDS migration orchestration that delegates per-domain spec, design, task, execute, and verify work to the sds.* skill suite. Adds the migration-specific concerns sds does not cover — discovery, domain decomposition, strangler-fig routing, API-diff harness, canary rollout, decommission — plus a persistent state file that coordinates multi-domain parallel execution. Trigger phrases — "migrate this app", "/migration-v2", "strangler migration", "decompose this legacy monolith", "run the migration pipeline".
---

# Migration Orchestration Skill (v2 — Large App, sds-delegating)

You orchestrate the migration of a legacy application to a new stack. You do **not** write specs, designs, tasks, code, or verification reports yourself. For every domain, you invoke the `sds.*` skill suite — one phase at a time — and treat its output files as the canonical per-domain artifacts.

This skill owns:
- Discovery of the legacy codebase (Phase 00)
- Decomposition into domains and shared kernel (Phase 01)
- Strangler-fig routing, feature flags, fallback, canary (Phase 06)
- API-diff harness against the legacy app (Phase 08)
- Decommission of legacy code (Phase 09)
- The cross-domain `migration-state.json` file
- Concurrency caps and the scheduler

This skill delegates:
- Per-domain Spec (Phase 02) → `/sds.spec`
- Per-domain Design (Phase 03) → `/sds.design`
- Per-domain Tasks (Phase 04) → `/sds.task`
- Per-domain Execute (Phase 05) → `/sds.execute`
- Per-domain Verify (Phase 07) → `/sds.verify`

Detailed delegation contract: [references/sds-delegation.md](references/sds-delegation.md). Read it before dispatching any sds phase.

---

## Pre-Made Decisions

Collected at invocation. Persisted to `migration-state.json` under `parameters`.

```
LEGACY_PATH        absolute path to legacy app
OUTPUT_PATH        absolute path for new app(s)
APP_SIZE_LOC       approximate LOC of the legacy app
TECH_STACK         target stack JSON (backend, frontend, db, auth)
TIMELINE_MONTHS    expected duration
TEAM_SIZE          engineers across all domains
DOMAINS            "auto" to derive in Phase 01, or explicit list of slugs
FEATURE_FLAG_SYS   LaunchDarkly | Unleash | Statsig | custom  (Phase 06)
ROUTING_LAYER      nginx | alb | cloudflare-worker | envoy    (Phase 06)
COMPLIANCE_SCOPE   array of: none | gdpr | soc2 | hipaa | pci | iso27001
LIVE_TRAFFIC       true | false  — when false, Phases 06, 08, 09 are skipped
```

If `COMPLIANCE_SCOPE` is unknown, ask the user. Do not invent a default — it changes Phase 07 verify rules.

If `LIVE_TRAFFIC=false` (greenfield rewrite, no production traffic to shift), Phases 06, 08, and 09 are explicitly skipped and the run completes after Phase 07.

---

## Artifact Paths

The migration produces artifacts in three locations. Do not blur them.

| Location | Owner | Contents |
|---|---|---|
| `migration-state.json` (repo root) | this skill | Cross-domain state, parameters, phase progress |
| `migration/` (repo root) | this skill | Discovery summary, decompose outputs, per-domain `legacy-context.md`, strangler configs, api-diff reports, decommission logs |
| `spec-driven/<domain-slug>/` | the sds.* skills | spec.md, design.md, tasks.md, bundle-N.md, progress-bundle-N.md, verify-report.md |

The migration domain slug **is** the sds spec slug. Domains must be named with the slug format the sds skills accept: lowercase-with-hyphens, ≤64 chars, `[a-z0-9-]+`.

---

## Concurrency Model

| Phase | Max parallel agents | Notes |
|-------|---------------------|-------|
| 00 Discovery | 8 | Native scanners (read-only). |
| 01 Decompose | 1 | Serial reasoning over discovery output. |
| 02 Spec | 1 per domain, up to 4 concurrent | `/sds.spec` is interactive — parallel runs require separate sessions. |
| 03 Design | 1 per domain, up to 4 concurrent | Same as Spec. |
| 04 Tasks | up to N domains | `/sds.task` is shorter and tolerates more parallelism. |
| 05 Execute | 1 per domain across domains; within a domain, `/sds.execute --parallelism` controls bundle parallelism | Branch isolation is owned by sds.execute. |
| 06 Strangler-fig | N domains | Config generation independent. |
| 07 Verify | up to N domains | `/sds.verify` itself dispatches 6 parallel verification agents internally. |
| 08 API-diff | N domains | Native harness. |
| 09 Decommission | 1, serial across domains | Safety: never decommission two domains at once. |

Phases marked "interactive" (02, 03) require human input via the sds gates. The scheduler must surface the gate to the user, not auto-answer.

The scheduler ([coordinator/scheduler.md](coordinator/scheduler.md)) enforces these caps.

---

## Phase 00 — Discovery (native)

For each top-level module of `LEGACY_PATH`, dispatch in parallel (cap=8):
- [sub-agents/00-discovery/code-map-scan.md](sub-agents/00-discovery/code-map-scan.md) with `{{MODULE}}`
- [sub-agents/00-discovery/api-routes-scan.md](sub-agents/00-discovery/api-routes-scan.md) with `{{MODULE}}`
- [sub-agents/00-discovery/test-spec-scan.md](sub-agents/00-discovery/test-spec-scan.md) with `{{MODULE}}`

For DB schemas, dispatch by schema prefix:
- [sub-agents/00-discovery/db-schema-scan.md](sub-agents/00-discovery/db-schema-scan.md) with `{{PREFIX}}`

Once per project:
- [sub-agents/00-discovery/git-log-mining.md](sub-agents/00-discovery/git-log-mining.md) with `{{TIMEFRAME}}`
- [sub-agents/00-discovery/ui-screen-crawl.md](sub-agents/00-discovery/ui-screen-crawl.md)
- [sub-agents/00-discovery/dependency-graph.md](sub-agents/00-discovery/dependency-graph.md)

After all complete:
- [sub-agents/00-discovery/discovery-synthesis.md](sub-agents/00-discovery/discovery-synthesis.md) (writes `migration/discovery/SUMMARY.md`).

**Gate**: `migration/discovery/SUMMARY.md` exists AND `migration-state.json.phases_complete` contains `"discovery"`.

---

## Phase 01 — Decompose (native)

Dispatch serially:
1. [sub-agents/01-decompose/domain-decompose.md](sub-agents/01-decompose/domain-decompose.md) → writes `migration/domains/_index.md`. Each domain's `slug` MUST be in `[a-z0-9-]+` (sds-compatible).
2. [sub-agents/01-decompose/shared-kernel-inventory.md](sub-agents/01-decompose/shared-kernel-inventory.md) → `migration/domains/_shared-kernel.md`.
3. [sub-agents/01-decompose/contract-registry.md](sub-agents/01-decompose/contract-registry.md) → `migration/domains/_contracts.yaml`.
4. [sub-agents/01-decompose/team-ownership-map.md](sub-agents/01-decompose/team-ownership-map.md) → `migration/domains/_codeowners.md`.
5. [sub-agents/01-decompose/migration-order.md](sub-agents/01-decompose/migration-order.md) → `migration/domains/_migration-order.md`.

After completion, for each domain create `migration/domains/<slug>/legacy-context.md` from the template at [templates/legacy-context.md](templates/legacy-context.md). This briefing file is the `--from` input for `/sds.spec` in Phase 02.

**Gate**: All five `_*` files exist; per-domain `legacy-context.md` exists for every domain. State has `"decompose"` complete. **Domain expert review required** before Phase 02.

---

## Phase 02 — Spec (delegate to /sds.spec)

For each domain slug (parallel, cap=4):

```
/sds.spec <slug> --from migration/domains/<slug>/legacy-context.md --draft
```

`--draft` is mandatory: it synthesizes a spec from the legacy briefing and presents it for user validation, rather than running full interactive elicitation from scratch. The user reviews and refines.

**Do not pre-write `spec-driven/<slug>/spec.md`** — `/sds.spec` owns that path.

**Gate per domain**: `spec-driven/<slug>/spec.md` exists with frontmatter `status: final`. Update `migration-state.json.domains[<slug>].status` to `"spec"`.

Full delegation details (briefing format, --draft fallback, multi-project handling): [references/sds-delegation.md](references/sds-delegation.md#phase-02).

---

## Phase 03 — Design (delegate to /sds.design)

For each domain slug whose spec is final (parallel, cap=4):

```
/sds.design <slug> --context migration/_constraints.md
```

`migration/_constraints.md` is written once per migration; it lists the `TECH_STACK`, `COMPLIANCE_SCOPE`, NFR baselines, and any architectural standards that apply across domains. Each `/sds.design` run reads it as additional context to its base research.

**Gate per domain**: `spec-driven/<slug>/design.md` exists with `status: final`. Update domain status to `"design"`. **API owner review required** if domain exposes inbound contracts.

Full delegation details, including how to inject contract requirements from `migration/domains/_contracts.yaml`: [references/sds-delegation.md](references/sds-delegation.md#phase-03).

---

## Phase 04 — Tasks (delegate to /sds.task)

For each domain slug whose design is final (parallel, cap = N):

```
/sds.task <slug>
```

If a domain's design points to a known migration strategy (e.g. data migration first, then API), pass `--strategy dependency-first` when invoking.

**Gate per domain**: `spec-driven/<slug>/tasks.md` exists AND at least `spec-driven/<slug>/bundle-1.md` and `spec-driven/<slug>/progress-bundle-1.md` exist. Update domain status to `"tasks"`.

Full delegation details: [references/sds-delegation.md](references/sds-delegation.md#phase-04).

---

## Phase 05 — Execute (delegate to /sds.execute)

For each domain slug, respecting the order in `migration/domains/_migration-order.md`:

```
/sds.execute <slug> --parallelism <N>
```

`N` is bounded by the Phase 05 row in the Concurrency Model. `/sds.execute` handles branch isolation on `spec-driven/<slug>/exec`, per-bundle commits with `[STEP-N]` traceability, and the merge-back gate.

After `/sds.execute` completes for a domain, the migration scheduler must record the integration branch in `migration-state.json.domains[<slug>].branch = "spec-driven/<slug>/exec"`.

**Gate per domain**: every `spec-driven/<slug>/progress-bundle-N.md` shows all steps as `done`. CI must be green on `spec-driven/<slug>/exec`. Update domain status to `"execute"`.

Failure handling: if `/sds.execute` reports a step as `blocked` and cannot recover, the migration scheduler records a blocker in `migration-state.json.domains[<slug>].blockers[]` and stops further phase advancement for that domain. Do not skip the failed bundle.

Full delegation details: [references/sds-delegation.md](references/sds-delegation.md#phase-05).

---

## Phase 06 — Strangler-Fig (native; skipped when `LIVE_TRAFFIC=false`)

For each domain (parallel):
1. [sub-agents/06-strangler-fig/routing-config.md](sub-agents/06-strangler-fig/routing-config.md) — uses `ROUTING_LAYER`. Writes `migration/domains/<slug>/strangler/routing.{conf|tf|js}`.
2. [sub-agents/06-strangler-fig/feature-flag-wiring.md](sub-agents/06-strangler-fig/feature-flag-wiring.md) — uses `FEATURE_FLAG_SYS`. Writes `migration/domains/<slug>/strangler/flags.yaml`.
3. [sub-agents/06-strangler-fig/fallback-logic.md](sub-agents/06-strangler-fig/fallback-logic.md) — writes `migration/domains/<slug>/strangler/fallback.md`.
4. [sub-agents/06-strangler-fig/canary-rollout.md](sub-agents/06-strangler-fig/canary-rollout.md) — writes `migration/domains/<slug>/strangler/canary-schedule.yaml`.

**Gate per domain**: all four files exist. **SRE review required** before any canary ramp begins. Update domain status to `"strangler"`.

---

## Phase 07 — Verify (delegate to /sds.verify)

For each domain (parallel, up to N):

```
/sds.verify <slug>
```

`/sds.verify` dispatches 6 parallel verification agents internally (traceability, completeness, quality, testing, regression, security). The migration skill maps these onto the broader 10-dimension scoreboard:

| sds dimension | Migration scoreboard slot |
|---|---|
| traceability | traceability |
| completeness | completeness |
| quality | code-quality |
| testing | test-quality |
| regression | regression |
| security | security |

The four remaining migration dimensions — performance, observability, compliance, data-parity — are not produced by `/sds.verify`. For each, dispatch the corresponding native sub-agent if the domain's NFRs or `COMPLIANCE_SCOPE` require it:
- [sub-agents/07-verify/performance.md](sub-agents/07-verify/performance.md)
- [sub-agents/07-verify/observability.md](sub-agents/07-verify/observability.md)
- [sub-agents/07-verify/compliance.md](sub-agents/07-verify/compliance.md)
- [sub-agents/07-verify/data-parity.md](sub-agents/07-verify/data-parity.md)

Aggregate findings into `migration/domains/<slug>/verify-supplement.md`. The canonical verify artifact is `spec-driven/<slug>/verify-report.md`; the supplement covers only the four extra dimensions.

**Gate per domain**: zero CRITICAL findings open across `spec-driven/<slug>/verify-report.md` AND `migration/domains/<slug>/verify-supplement.md`. Update domain status to `"verify"`.

Full delegation details: [references/sds-delegation.md](references/sds-delegation.md#phase-07).

---

## Phase 08 — API-Diff (native; skipped when `LIVE_TRAFFIC=false`)

For each domain whose design names inbound contracts (parallel):
1. [sub-agents/08-api-diff/harness-setup.md](sub-agents/08-api-diff/harness-setup.md) — installs harness from [templates/api-diff-harness.ts](templates/api-diff-harness.ts).
2. [sub-agents/08-api-diff/semantic-equivalence.md](sub-agents/08-api-diff/semantic-equivalence.md) — defines tolerated diffs.
3. [sub-agents/08-api-diff/diff-runner.md](sub-agents/08-api-diff/diff-runner.md) — runs continuously at every canary ramp step.

**Gate per domain**: `migration/domains/<slug>/api-diff-report.md` shows <0.1% unexplained diffs at current ramp. Update domain status to `"api-diff"`.

---

## Phase 09 — Decommission (native; skipped when `LIVE_TRAFFIC=false`)

Only run after `ramp_percent = 100` AND stable for 7+ days AND tech-lead + product approval.

Per domain, serial across domains:
1. [sub-agents/09-decommission/traffic-verify.md](sub-agents/09-decommission/traffic-verify.md)
2. [sub-agents/09-decommission/dependency-check.md](sub-agents/09-decommission/dependency-check.md)
3. [sub-agents/09-decommission/data-archival.md](sub-agents/09-decommission/data-archival.md)
4. [sub-agents/09-decommission/safe-removal.md](sub-agents/09-decommission/safe-removal.md)

**Gate per domain**: `migration-state.json.domains[<slug>].status = "decommissioned"`.

---

## State File Management

Every native sub-agent **must**:
- Read `migration-state.json` at start. Stop with error if a required precondition is unmet.
- Write back updates atomically: read → modify → write to `.tmp` → rename.
- Append to `rollback_history` on any destructive change.

The sds skills **do not** read or write `migration-state.json`. The migration scheduler is responsible for reflecting sds phase progress into the state file after each delegation returns.

Schema: [coordinator/migration-state.schema.json](coordinator/migration-state.schema.json). Validate after every write.

---

## Scheduler Loop

Between phases, and on resume, invoke [coordinator/scheduler.md](coordinator/scheduler.md). The scheduler:
1. Reads `migration-state.json`.
2. Determines the next dispatchable phase per domain, respecting `_migration-order.md` and the concurrency caps above.
3. Writes `migration/state/next-actions.md`.

The orchestrator dispatches the listed actions. For sds-delegated phases, the action is a `/sds.<phase> <slug>` invocation, not a sub-agent path.

---

## Mandatory Human Gates

These gates require human review before the next phase begins. Surface decisions to the user; do not auto-advance.

- After 01-decompose: domain expert confirms boundaries.
- During 02-spec: `/sds.spec`'s own gates fire (gap analysis, post-elicitation validation). Do not auto-answer.
- During 03-design: `/sds.design`'s four gates fire (Research Scope, Research Findings, Design Review, Commit Decision).
- During 04-tasks: `/sds.task`'s gates fire (Decomposition Approach, Task Review, Commit Decision).
- During 05-execute: `/sds.execute`'s per-bundle review gates fire (unless `--skip-review` is explicitly chosen by the user).
- Before 06-strangler-fig: SRE approves routing config.
- Before each canary ramp: SRE approves SLO baseline.
- During 07-verify: present `/sds.verify`'s remediation choices to the user.
- Before 09-decommission: tech lead + product approve removal.

---

## Error Handling

- Sub-agent writes no output: retry once with "ensure file written" instruction. If still empty, mark phase blocked.
- State file conflict (concurrent write): the scheduler serializes; never edit state mid-flight.
- sds skill stops with an error: surface verbatim to the user; do not retry blindly. Many sds errors are user-action required (missing spec, missing slug, accessibility failure).
- Phase 07 CRITICAL finding: block phase; do not advance ramp; surface to user with the relevant report path.
- Canary SLO breach: trigger automatic rollback per `migration/domains/<slug>/strangler/canary-schedule.yaml`. Mark `domains[<slug>].status = "rolled_back"` and append to `rollback_history` with `triggered_by = "slo_breach"`.

---

## Skill Entry Point

When the user invokes `/migration-v2`:

1. Initialize `migration-state.json` from [coordinator/migration-state.schema.json](coordinator/migration-state.schema.json) defaults.
2. Collect all Pre-Made Decisions. Persist them.
3. If `LIVE_TRAFFIC=false`, mark Phases 06, 08, 09 as `skipped` in `phases_complete` with reason `"greenfield-no-live-traffic"`.
4. Dispatch Phase 00.
5. After each phase, invoke [coordinator/scheduler.md](coordinator/scheduler.md) to compute next actions.
6. Loop until every migration-target domain has status `"decommissioned"` (live traffic) or `"verify"` (greenfield).

Before dispatching any sds phase, read [references/sds-delegation.md](references/sds-delegation.md) for the exact invocation contract.
